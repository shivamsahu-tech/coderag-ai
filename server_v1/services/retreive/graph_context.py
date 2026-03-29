import os
from core.logging import get_logger
from db.neo4j_client import get_neo4j_driver

logger = get_logger(__name__)
neo4j_driver = get_neo4j_driver()


def get_neighbors(node_id: str, session_id: str) -> str:
    """
    Given a node ID, return all neighboring nodes (both incoming and outgoing)
    from the Neo4j graph for the given session.
    """
    logger.info("get_neighbors called")
    try:
        db_name = os.getenv("NEO4J_DATABASE", "neo4j")

        with neo4j_driver.session(database=db_name) as session:
            logger.info(f"Fetching neighbors for node: {node_id} in session: {session_id}")

            result = session.run(
                """
                MATCH (n:CodeNode {id: $node_id, session_id: $session_id})-[r]-(m:CodeNode {session_id: $session_id})
                RETURN m, type(r) AS rel_type,
                       CASE WHEN startNode(r).id = $node_id THEN 'OUTGOING' ELSE 'INCOMING' END AS direction
                """,
                node_id=node_id,
                session_id=session_id
            )

            records = list(result)[:5]  # Limit to 5 neighbors

            if not records:
                return f"No neighbors found for node '{node_id}'. The node may not exist or has no connections in this session."

            parts = [f"Neighbors of node '{node_id}' (showing top {len(records)}):\n"]

            for record in records:
                m = record["m"]
                rel_type = record["rel_type"]
                direction = record["direction"]

                neighbor_id  = m.get("id", "unknown")
                name         = m.get("name", "unknown")
                ast_type     = m.get("ast_type", "unknown")
                file_path    = m.get("file", "unknown")
                code_str     = m.get("code_str", "")

                block = (
                    f"\n{'-' * 75}\n"
                    f"  Relationship : --[{rel_type}]--> ({direction})\n"
                    f"  ID           : {neighbor_id}\n"
                    f"  Name         : {name}\n"
                    f"  Type         : {ast_type}\n"
                    f"  File         : {file_path}\n"
                    f"  Code         : {code_str[:300]}..."
                )
                parts.append(block)

            return "\n".join(parts)

    except Exception as e:
        logger.error(f"Error fetching neighbors for node '{node_id}': {e}", exc_info=True)
        return f"Error fetching neighbors: {str(e)}"
