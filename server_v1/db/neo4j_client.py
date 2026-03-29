import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

from core.logging import get_logger 
logger = get_logger(__name__)

load_dotenv()

__neo4j_driver = None

def get_neo4j_driver():
    global __neo4j_driver

    if __neo4j_driver is None:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_username = os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not neo4j_uri or not neo4j_password or not neo4j_username:
            raise ValueError("Neo4j URI, Username, or Password missing from environment variables")
        
        try:
            # 1. Initialize the driver
            __neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_username, neo4j_password),
                max_connection_lifetime=200, # Closes connections older than 200 seconds
                keep_alive=True
            )
            
            # 2. Add this line: It actively pings the DB to ensure DNS and Auth are working
            __neo4j_driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j Aura instance!")
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j. Check your .env credentials or network. Error: {e}")
            raise e
    
    return __neo4j_driver