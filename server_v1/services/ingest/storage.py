import os
import time
from typing import List, Dict
from core.logging import get_logger
from db.neo4j_client import get_neo4j_driver
from fastapi import HTTPException
from services.llm.embedding_jina import get_embeddings

# Neo4j Aura free has ~512MB RAM — chunk large UNWIND operations to avoid OOM.
_NEO4J_WRITE_CHUNK = 200

logger = get_logger(__name__)

neo4j_driver = get_neo4j_driver()

def store_nodes_in_neo4j(nodes: List[Dict], session_id: str):

    if not nodes:
        logger.warning("No nodes to store in Neo4j.")
        return

    flattened = []
    relationship_edges = [] 

    for node in nodes:
        node_id = node.get("id")
        meta = node.get("metadata", {})
        rels = node.get("relationships", {})

        flattened.append({
            "id": node.get("id"),
            "name": node.get("name") or node.get("ast_type"),
            "code_str": node.get("code_str", ""),
            "ast_type": node.get("ast_type"),
            "file": node.get("file"),
            "language": node.get("language"),
            "start_line": node.get("start_line"),
            "end_line": node.get("end_line"),
            "start_byte": node.get("start_byte"),
            "end_byte": node.get("end_byte"),
            "size": node.get("size"),
            "depth": meta.get("depth"),
            "calls": meta.get("calls", []),
            "type_references": meta.get("type_references", []),
            "is_definition": meta.get("is_definition"),
            "definition_type": meta.get("definition_type"),
        })

        # Resolving the imports and creating relationship list
        for keys, values in rels.items():
            if keys == "imports_from":
                for imp in values:
                    if imp.get("is_external"):
                        continue

                    resolved_ids = imp.get("resolved_node_ids", [])
                    for tid in resolved_ids:
                        relationship_edges.append({
                            "source": node_id,
                            "target": tid,
                            "type": "IMPORTS_FROM"
                        })
                continue

            if isinstance(values, list):
                for tid in values:
                    relationship_edges.append({
                        "source": node_id,
                        "target": tid,
                        "type": keys.upper()
                    })

    try:
        # preparing text chunk for embedding
        text_chunks = []
        for node_data in flattened:
            text_parts = []
            if node_data.get("name"):
                text_parts.append(f"Name: {node_data['name']}")
            if node_data.get("ast_type"):
                text_parts.append(f"Type: {node_data['ast_type']}")
            if node_data.get("code_str"):
                text_parts.append(f"Code: {node_data['code_str']}")
            if node_data.get("file"):
                text_parts.append(f"File: {node_data['file']}")
            
            text_chunk = " | ".join(text_parts)
            text_chunks.append(text_chunk)
        
        logger.info(f"Generating embeddings for {len(text_chunks)} nodes...")
        embeddings = get_embeddings(text_chunks)
        
        if embeddings and len(embeddings) == len(flattened):
            for i, node_data in enumerate(flattened):
                node_data["embedding"] = embeddings[i]
            logger.info("Embeddings generated successfully.")
        else:
            logger.warning("Failed to generate embeddings or count mismatch. Storing nodes without embeddings.")

        # --- KEY CHANGE 1: Grab the database name from your .env ---
        db_name = os.getenv("NEO4J_DATABASE", "neo4j")

        # --- KEY CHANGE 2: Inject the database name into the session ---
        with neo4j_driver.session(database=db_name) as session:

            # --- Chunked node writes (avoid OOM on Aura free 512MB) ---
            total_chunks = (len(flattened) + _NEO4J_WRITE_CHUNK - 1) // _NEO4J_WRITE_CHUNK
            for chunk_i in range(0, len(flattened), _NEO4J_WRITE_CHUNK):
                chunk = flattened[chunk_i : chunk_i + _NEO4J_WRITE_CHUNK]
                chunk_num = chunk_i // _NEO4J_WRITE_CHUNK + 1
                logger.info(f"Writing node chunk {chunk_num}/{total_chunks} ({len(chunk)} nodes)...")
                session.run(
                    """
                    UNWIND $nodes AS node
                    CREATE (n:CodeNode)
                    SET n += node,
                        n.session_id = $session_id
                    """,
                    nodes=chunk,
                    session_id=session_id,
                )

            # Add AST labels
            session.run(
                """
                MATCH (n:CodeNode {session_id: $session_id})
                CALL apoc.create.addLabels(n, [n.ast_type]) YIELD node
                RETURN node
                """,
                session_id=session_id,
            )

            # Create vector index — dimension MUST match jina-code-embeddings-1.5b (1024)
            try:
                session.run(
                    """
                    CREATE VECTOR INDEX code_embeddings IF NOT EXISTS
                    FOR (n:CodeNode)
                    ON n.embedding
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """
                )
                logger.info("Vector index created or already exists (dim=1024).")
            except Exception as e:
                logger.warning(f"Vector index creation warning (may already exist): {e}")

            # --- Chunked relationship writes ---
            if relationship_edges:
                total_rel_chunks = (len(relationship_edges) + _NEO4J_WRITE_CHUNK - 1) // _NEO4J_WRITE_CHUNK
                for chunk_i in range(0, len(relationship_edges), _NEO4J_WRITE_CHUNK):
                    chunk = relationship_edges[chunk_i : chunk_i + _NEO4J_WRITE_CHUNK]
                    chunk_num = chunk_i // _NEO4J_WRITE_CHUNK + 1
                    logger.info(f"Writing relationship chunk {chunk_num}/{total_rel_chunks} ({len(chunk)} edges)...")
                    session.run(
                        """
                        UNWIND $edges AS edge
                        MATCH (a:CodeNode {id: edge.source, session_id: $session_id})
                        MATCH (b:CodeNode {id: edge.target, session_id: $session_id})
                        CALL apoc.create.relationship(a, edge.type, {}, b) YIELD rel
                        RETURN rel
                        """,
                        edges=chunk,
                        session_id=session_id,
                    )

            logger.info("Stored nodes + embeddings + all relationship types successfully.")

    except Exception as e:
        logger.error(f"Failed in store_nodes_in_neo4j: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Issue in neo4j storage | Error {e}"
        )