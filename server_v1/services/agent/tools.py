from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from services.retreive.retrieve_context import retrieve_context


@tool("retrieve_context")
def retrieve_context_wrapper(query: str, config: RunnableConfig) -> str:
    """    
    Use this tool to answer questions about any questions related to YOUR CODEBASE.:
    this tool provide you top nodes from codebase that is cosine similar to the query embeddings. so if you have any question you can prepare a query according to the user query thats embedding retireve best chunks from the db, because you know the chunks structure and there embeddings.

    Args:
        query (str): The question or query string for which context needs to be retrieved.
        config (RunnableConfig): The runtime configuration containing metadata like session_id.
    
    Returns:
        a context string containing all the top relevant nodes related to the query.

    eg: what is the codebase all about?

    you prepare query: 'what is written in the readme file, where are the main functiosn defined?'

    context = 
    node: readme.md
    code_str: This is a codeRAG applicaiton...........

    node: main.py
    code_str: def main(): .....


    """
    # 1. Securely extract the session_id (thread_id) from the runtime config
    # This prevents the LLM from hallucinating a session ID.
    session_id = config["configurable"].get("session_id")
    
    if not session_id:
        return "Error: No session ID found in the configuration. Cannot retrieve context."

    # 2. Call the actual retrieval service
    # This function uses cosine similarity on your AST node embeddings
    return retrieve_context(query=query, session_id=session_id)