import os
from core.logging import get_logger
from services.llm.embedding_jina import get_embeddings
from db.neo4j_client import get_neo4j_driver
from fastapi import HTTPException

logger = get_logger(__name__)
neo4j_driver = get_neo4j_driver()

CONTEXT_THRESHOLD = 6000

def retrieve_context(query: str, session_id: str, k: int = 10) -> str:
    """
    Retrieve context by first filtering by session_id, then computing similarity.
    Includes robust error handling for edge cases.
    """
    try:
        logger.info(f"Embedding query: {query}")
        # This will automatically trigger task="nl2code.query" because len == 1
        query_embedding = get_embeddings([query])[0]
        logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")
        
        # --- KEY CHANGE 1: Grab the specific Aura database name ---
        db_name = os.getenv("NEO4J_DATABASE", "neo4j")
        
        with neo4j_driver.session(database=db_name) as session:

            logger.info(f"Searching for nodes in session: {session_id}")
            
            # --- KEY CHANGE 2: Replaced gds.similarity.cosine with vector.similarity.cosine ---
            # Neo4j Aura Free doesn't have GDS installed, but has native vector math.
            result = session.run(
                """
                MATCH (node:CodeNode)
                WHERE node.session_id = $session_id 
                  AND node.embedding IS NOT NULL
                WITH node, 
                     vector.similarity.cosine(node.embedding, $query_vector) AS score
                RETURN node, score
                ORDER BY score DESC
                LIMIT $k
                """,
                session_id=session_id,
                query_vector=query_embedding,
                k=k
            )
            
            records = list(result)
            
            if not records:
                logger.warning(f"No nodes found for session {session_id}")
                return f"Query: {query}\n\nNo relevant nodes found for this session."
            
            top_nodes = [record["node"] for record in records]
            scores = [record["score"] for record in records]
            
            logger.info(f"Top nodes found: {len(top_nodes)}")
            
            top_ids = [node["id"] for node in top_nodes]
            
            logger.info(f"Fetching neighbors for {len(top_ids)} nodes...")
            rel_result = session.run(
                """
                MATCH (n:CodeNode)
                WHERE n.session_id = $session_id AND n.id IN $top_ids
                MATCH (n)-[r]->(m:CodeNode)
                WHERE m.session_id = $session_id
                RETURN m AS target_node, type(r) AS rel_type
                """,
                top_ids=top_ids,
                session_id=session_id
            )
            
            related_nodes = []
            seen_ids = set(top_ids)
            
            for record in rel_result:
                m = record["target_node"]
                if m["id"] not in seen_ids:
                    related_nodes.append(m)
                    seen_ids.add(m["id"])
            
            logger.info(f"Found {len(related_nodes)} related neighbor nodes")
            
            all_nodes = top_nodes + related_nodes
            logger.info(f"Total nodes to process: {len(all_nodes)}")
            
            context_parts = ""
            current_length = 0
            nodes_added = 0
            
            for node in all_nodes:
                name = node.get('name', 'unknown')
                ast_type = node.get('ast_type', 'unknown')
                file_path = node.get('file', 'unknown')
                code_str = node.get('code_str', '')
                
                block = f"""
                        Name: {name}
                        Type: {ast_type}
                        File: {file_path}
                        Code: {code_str}
                        """
                block = "\n" + "-" * 75 + "\n" + block
                block_len = len(block)
                
                if current_length + block_len > CONTEXT_THRESHOLD:
                    logger.info(
                        f"Threshold reached. Added {nodes_added} nodes out of {len(all_nodes)}"
                    )
                    break
                
                context_parts += block
                current_length += block_len
                nodes_added += 1
            
            logger.info(f"Final context: {current_length} chars, {nodes_added} nodes")
            
            if not context_parts.strip():
                logger.warning("Context is empty after building")
                return f"Query: {query}\n\nNo context could be built within threshold."
            
            return context_parts
            
    # --- KEY CHANGE 3: Fixed missing 'as e' in exception handling ---
    except HTTPException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Issue in context retrieval storage | Error {e.detail}"
        )
        
    except Exception as e:
        logger.error(f"Retrieval error: {e}", exc_info=True)
        
        error_msg = str(e).lower()
        if "vector.similarity.cosine" in error_msg or "unknown function" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Neo4j vector similarity function failed. "
                    "Ensure you are running Neo4j 5.0+ for native vector support."
                )
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch context from Neo4j! | Error: {str(e)}"
        )



# print(retrieve_context("what is this codebase all about", "f8bf52ef-5ba7-4435-b25b-ca28bd03549f"))
# TEST_SESSION_ID = "f8bf52ef-5ba7-4435-b25b-ca28bd03549f"
# run_all_tests(TEST_SESSION_ID)