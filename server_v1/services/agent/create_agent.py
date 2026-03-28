import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from services.agent.tools import retrieve_context_wrapper, get_neighbors_wrapper
from core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert Codebase Assistant.

The codebase is indexed as a dependency graph (via tree-sitter). Each node has:
  id, name, ast_type, file, code_str, calls, depth, language, session_id.

Embeddings are built from: name | ast_type | code_str | file.

HOW TO ANSWER:
- YOU ARE FREE TO USE OR NOT USE THE TOOLS ACCORDING TO THE USER QUERY, YOU WILL SELECT THE BEST POSSIBLE TOOL TO ANSWER THE QUERY
- IF YOU ARE NOT SATISFY WITH ANY TOOL RESPONSE, THEN YOU CAN AGAIN CALL TOOL WITH DIFFERENT PARAMETER TO PROVIDE BEST RESPONSE TO THE USER, MAX TOOL CALL 3
- IF YOU ARE NOT ABLE TO ANSWER THE QUERY, THEN YOU CAN SAY I AM NOT ABLE TO ANSWER THE QUERY
- DON'T ANSWER THE USER, IF HE IS ASKING ANY GENERALIZE QESTION THAT IS NOT RELATED WITH THE CODEBASE OR CODING.
- YOU ARE FREE TO USER BEST APPROACH AND MODIFY THE USER'S QUERY ACCORDINGLY FOR BEST POSSIBLE RESPONSE.

TOOL CALLING RULES (CRITICAL):
- When calling a tool, output ONLY the tool call — nothing else.
- Do NOT write "Let me check..." or any text before calling a tool.
- Do NOT answer from memory. Always retrieve first.
"""

class State(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent_graph():
    # llama-3.3-70b-versatile is significantly more reliable for tool use
    # than the deprecated llama3-groq-70b-8192-tool-use-preview
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        max_tokens=4096,  # Was 1000 — truncated responses were causing malformed tool JSON
        api_key=os.getenv("GROQ_API_KEY"),
    )

    tools = [retrieve_context_wrapper, get_neighbors_wrapper]

    # parallel_tool_calls=False prevents the model from attempting
    # concurrent tool calls which Groq handles poorly
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

    def chatbot(state: State, config: RunnableConfig):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

        # Retry up to 3 times on tool_use_failed / BadRequestError
        last_error = None
        for attempt in range(3):
            try:
                response = llm_with_tools.invoke(messages)

                # Guard: if the model returned empty content with no tool calls,
                # something went wrong — treat it as a retryable error
                has_tool_calls = bool(getattr(response, "tool_calls", None))
                has_content = bool(
                    response.content
                    if isinstance(response.content, str)
                    else any(response.content)
                )

                if not has_tool_calls and not has_content:
                    logger.warning(f"Empty response on attempt {attempt + 1}, retrying...")
                    continue

                return {"messages": [response]}

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Only retry on Groq tool-generation failures
                if "tool_use_failed" in error_str or "failed to call a function" in error_str:
                    logger.warning(
                        f"Tool call generation failed (attempt {attempt + 1}/3): {e}"
                    )
                    # Inject a corrective hint into history so the next attempt
                    # knows the previous tool call was malformed
                    messages.append(
                        AIMessage(content="[Tool call failed. Retrying with a simpler query.]")
                    )
                    continue

                # Non-retryable error — surface it immediately
                logger.error(f"Non-retryable LLM error: {e}", exc_info=True)
                raise

        # All retries exhausted
        logger.error(f"All 3 attempts failed. Last error: {last_error}")
        fallback = AIMessage(
            content=(
                "I encountered repeated errors while trying to retrieve context. "
                "Please try rephrasing your question or try again in a moment."
            )
        )
        return {"messages": [fallback]}

    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


agent_app = build_agent_graph()