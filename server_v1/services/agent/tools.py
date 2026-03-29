"""
Tool definitions for the manual Groq tool-calling agent.

Each Python function is a plain callable — no LangChain decorators.
TOOL_DEFINITIONS contains the OpenAI-format schemas sent to Groq.
TOOL_MAP maps tool name → callable for dispatch.
"""
from services.retreive.retrieve_context import retrieve_context
from services.retreive.graph_context import get_neighbors as _get_neighbors
from core.logging import get_logger

logger = get_logger(__name__)


def tool_retrieve_context(query: str, session_id: str) -> str:
    """
    Searches the codebase via semantic similarity and returns relevant code nodes.
    Use this for ANY question about code: functions, classes, files, imports, logic.
    query must be natural language (e.g. 'user authentication logic').
    """
    logger.info(f"[Agent] Calling tool 'retrieve_context' with query='{query}'")
    return retrieve_context(query=query, session_id=session_id)


def tool_get_neighbors(node_id: str, session_id: str) -> str:
    """
    Returns all nodes connected to the given node_id in the code dependency graph.
    Use the exact 'id' field returned by retrieve_context.
    Helps understand what a function calls or what calls it.
    """
    logger.info(f"[Agent] Calling tool 'get_neighbors' with node_id='{node_id}'")
    return _get_neighbors(node_id=node_id, session_id=session_id)


# ── OpenAI-format tool schemas for Groq ───────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_context",
            "description": (
                "Semantically searches the indexed codebase and returns relevant code nodes "
                "(functions, classes, methods, etc.). "
                "ALWAYS call this first when the user asks any question about the codebase, "
                "how code works, where something is defined, or what a function does."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language description of what you are looking for. "
                            "Examples: 'user authentication logic', 'how HTTP requests are sent', "
                            "'Redux store configuration'. Keep it concise and descriptive."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_neighbors",
            "description": (
                "Fetches all nodes directly connected to a given node in the code graph. "
                "Use this AFTER retrieve_context to understand dependencies: "
                "what a function calls, or what other functions call it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": (
                            "The exact 'id' field from a retrieve_context result. "
                            "Example: 'data/repos/abc123/src/store.ts:42:method_definition'. "
                            "Copy it exactly — do not construct or modify it."
                        ),
                    }
                },
                "required": ["node_id"],
            },
        },
    },
]

# ── Dispatch map ───────────────────────────────────────────────────────────────

TOOL_MAP = {
    "retrieve_context": tool_retrieve_context,
    "get_neighbors": tool_get_neighbors,
}