from datetime import datetime, timedelta, timezone
from core.logging import get_logger
from services.retreive.retrieve_context import retrieve_context
from services.retreive.graph_context import get_neighbors
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = get_logger(__name__)

MEMORY_TIMEOUT_HOURS = 24
MAX_HISTORY_TURNS = 6  # Keep last 6 turns (12 messages) to stay within context limits

# In-memory store: { user_id: { "messages": [...], "last_active": datetime } }
_history_store: dict = {}

SYSTEM_PROMPT = """You are an expert code assistant helping developers understand codebases.

You will receive a <code_context> block containing retrieved code nodes (functions, classes, methods).

YOUR JOB IS TO USE JUDGMENT:
- If the user's question is about code/the codebase → use the context to give an accurate, well-formatted answer with file references and code snippets.
- If the retrieved context is NOT relevant to the question → IGNORE it entirely and just respond like a normal assistant.
- If the user is greeting you, making small talk, or asking something unrelated to code → respond naturally and friendly, do NOT reference any code context.

RESPONSE FORMAT:
- **Structure**: Use `##` (H2) for major sections and `###` (H3) for sub-points. Use `---` (horizontal rules) between logical sections.
- **Formatting**: Use Markdown: headings, bullet points, and code blocks where appropriate. Use **bold** for emphasis and `tables` for structured data comparison.
- **Referencing**: Reference specific function names, file paths, and code snippets when answering code questions.
- **Clarity**: If the context genuinely doesn't contain enough information to answer a code question, say so clearly.
"""


def _cleanup_expired_sessions():
    try:
        now = datetime.now(timezone.utc)
        expired = [
            uid for uid, data in _history_store.items()
            if now - data["last_active"] > timedelta(hours=MEMORY_TIMEOUT_HOURS)
        ]
        for uid in expired:
            del _history_store[uid]
        if expired:
            logger.info(f"Memory cleanup: removed {len(expired)} expired sessions.")
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")


def _get_history(user_id: str) -> list:
    if user_id not in _history_store:
        _history_store[user_id] = {
            "messages": [],
            "last_active": datetime.now(timezone.utc),
        }
    _history_store[user_id]["last_active"] = datetime.now(timezone.utc)
    return _history_store[user_id]["messages"]


def _trim_history(messages: list) -> list:
    """Keep only the last MAX_HISTORY_TURNS * 2 messages (user+assistant pairs)."""
    max_msgs = MAX_HISTORY_TURNS * 2
    return messages[-max_msgs:] if len(messages) > max_msgs else messages


def run_retreival_pipeline(session_id: str, query: str, user_id: str = "default") -> str:
    logger.info(f"Processing query for user: {user_id}, session: {session_id}")

    _cleanup_expired_sessions()

    # Step 1: Retrieve relevant code context from Neo4j (always deterministic)
    try:
        context = retrieve_context(query=query, session_id=session_id)
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}", exc_info=True)
        context = "Could not retrieve code context due to an error."

    # Step 2: Load this user's chat history
    history = _get_history(user_id)
    trimmed_history = _trim_history(history)

    # Step 3: Build the message list for the LLM
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(trimmed_history)

    # Inject context into the current user message only (not into history storage)
    augmented_user_message = (
        f"<code_context>\n{context}\n</code_context>\n\n"
        f"Question: {query}"
    )
    messages.append(HumanMessage(content=augmented_user_message))

    # Step 4: Call LLM — NO tools, plain chat completion. Reliable on all Groq models.
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",  # Best Groq model for complex reasoning
        temperature=0.1,
        max_tokens=2048,
    )

    try:
        response = llm.invoke(messages)
        answer = response.content

        # Normalize content (can be list in some model versions)
        if isinstance(answer, list):
            answer = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in answer
            )
        answer = str(answer).strip() if answer else "I could not generate a response."

    except Exception as e:
        logger.error(f"LLM invocation failed: {e}", exc_info=True)
        answer = f"An error occurred while generating the response: {str(e)}"

    # Step 5: Save only the bare query (not the injected context) + answer to history
    history.append(HumanMessage(content=query))
    history.append(AIMessage(content=answer))

    return answer