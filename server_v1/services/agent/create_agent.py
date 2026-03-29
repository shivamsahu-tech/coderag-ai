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

## RESPONSE QUALITY RULES
- **Structure**: Use `##` (H2) for major sections and `###` (H3) for sub-points. Use `---` (horizontal rules) between logical sections.
- **Formatting**: Use **bold** for emphasis, lists for steps/features, and `tables` for comparing multiple items, files, or nodes.
- **Synthesize**: Answer the user's actual question — don't dump raw tool output. Add code snippets and file references (e.g., `path/to/file.py`) when explaining code.
- **Graceful Fail**: If you genuinely cannot find the answer in the codebase, say so clearly.

## HOW TO DECIDE WHEN TO USE TOOLS

**Use tools** when the user asks about:
- What code exists, how something works, where something is defined
- Functions, classes, methods, files, imports, dependencies
- Any technical question about the indexed codebase

**BE THOROUGH (CRITICAL)**:
- Do NOT stop at the first tool result if it's incomplete.
- Always use `get_neighbors` after `retrieve_context` if you need to understand how a function is called or what it depends on.
- Continue calling tools if you discover new function names or file paths that seem relevant.
- You have a limit of **max 5 tool calls** per turn — use them to ensure your answer is complete and accurate.

## TOOL CALLING RULES
- When calling a tool, output ONLY the tool call — no text before or after.
- Do NOT write "Let me check..." before a tool call.
- Only call tools when the question is about the codebase.
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
        max_tokens=2048,  # 4096 was consuming ~7600 tokens/call (63% of 12K TPM limit). 2048 allows 2 agent calls/min.
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