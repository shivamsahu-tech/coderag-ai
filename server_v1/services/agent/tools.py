from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from services.retreive.retrieve_context import retrieve_context
from services.retreive.graph_context import get_neighbors


@tool("retrieve_context")
def retrieve_context_wrapper(query: str, config: RunnableConfig) -> str:
    """
    Searches the codebase and returns relevant code nodes (functions, classes,
    methods, etc.) based on semantic similarity to the query.

    Use this tool to answer ANY question about what code exists, how something
    works, where something is defined, or what a function does.

    Args:
        query: A natural language description of what you are looking for.
               Examples:
                 - "getState method implementation"
                 - "Redux store configuration"
                 - "user authentication logic"
                 - "how HTTP requests are sent"
               Keep it concise and descriptive. Do NOT use structured syntax
               like 'ast_type:X name:Y' — plain natural language works best.

    Returns:
        Formatted code nodes with: id, name, ast_type, file path, and source code.
    """
    session_id = config["configurable"].get("session_id")

    if not session_id:
        return "Error: No session_id in config. Cannot retrieve context."

    return retrieve_context(query=query, session_id=session_id)


@tool("get_neighbors")
def get_neighbors_wrapper(node_id: str, config: RunnableConfig) -> str:
    """
    Fetches all nodes directly connected to a given node in the code graph.
    Use this to find what a function calls, or what other functions call it.

    Call this AFTER retrieve_context, using the exact 'id' value from its output.

    Args:
        node_id: The exact 'id' field of the node from retrieve_context results.
                 Example: "data/repos/abc123/src/store.ts:42:method_definition"
                 Copy it exactly — do not modify or construct it yourself.

    Returns:
        All neighbor nodes with relationship type (INCOMING/OUTGOING), name,
        ast_type, file, and a code snippet.
    """
    session_id = config["configurable"].get("session_id")

    if not session_id:
        return "Error: No session_id in config. Cannot fetch neighbors."

    return get_neighbors(node_id=node_id, session_id=session_id)