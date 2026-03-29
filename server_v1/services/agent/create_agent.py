"""
Manual Groq ReAct agent — no LangChain.

Flow per request:
  1. Load chat history from Redis (keyed by user_id)
  2. Build messages: [system, ...history, user_msg]
  3. Loop ≤ MAX_ITERATIONS:
       a. POST to Groq /chat/completions with TOOL_DEFINITIONS
       b. tool_calls present  → execute each tool, append results, continue
       c. no tool_calls       → final text response, break
  4. Save updated history back to Redis
  5. Return the final assistant text
"""
import os
import json
import requests
from dotenv import load_dotenv
from core.logging import get_logger
from db.redis_client import get_history, save_history
from services.agent.tools import TOOL_DEFINITIONS, TOOL_MAP

import time

load_dotenv()
logger = get_logger(__name__)

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.3-70b-versatile"
_MAX_ITERATIONS = 5  # max tool-call rounds per query

SYSTEM_PROMPT = """You are an expert Codebase Assistant — a helpful, friendly AI that helps developers understand codebases.

## TOKEN SAVING (CRITICAL)
Your current rate limits are tight (12k tokens/min). 
- BE CONCISE with your internal tool call queries.
- Do NOT request more context than absolutely necessary.
- Synthesize information efficiently.

## RECALL HISTORY
The user has previously asked the following questions (in order):
{history_context}

Use these previous questions to provide context if the current query refers to them (e.g., 'what was my last question?').

The codebase is indexed as a dependency graph (via tree-sitter). Each node has:
  id, name, ast_type, file, code_str, calls, depth, language, session_id.

## WHEN TO USE TOOLS
- Use `retrieve_context` for ANY question about: code, functions, classes, files, imports, logic, architecture.
- Use `get_neighbors` after `retrieve_context` to explore what a node calls or depends on.
- Do NOT use tools for greetings, casual chat, or unrelated questions — just respond naturally.

## BE THOROUGH
- Do NOT stop at the first tool result if it looks incomplete.
- Chain `retrieve_context` → `get_neighbors` to trace full dependency paths.
- You can call tools up to 5 times per turn — use them to build a complete answer.

## RESPONSE FORMAT (CRITICAL)
- **Structure**: Use `##` (H2) for major sections and `###` (H3) for sub-points. Use `---` (horizontal rules) between logical sections.
- **Visual Hygiene**: Use **bold** for key terms, `tables` when comparing multiple files or nodes, and properly tagged code blocks for any code samples.
- **Narrative**: Do NOT dump raw tool output. Synthesize the findings into a clear, natural explanation.
- **Referencing**: Always mention exact file paths and function names.
- **Markdown Rendering**: The response will be rendered in a professional markdown viewer—make it look premium.
"""


def _call_groq(messages: list[dict], use_tools: bool = True) -> dict:
    """Make a single call to the Groq chat completions endpoint with retry logic."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables")

    payload = {
        "model": _MODEL,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.0,
    }
    if use_tools:
        payload["tools"] = TOOL_DEFINITIONS
        payload["tool_choice"] = "auto"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                _GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            
            if resp.status_code == 429:
                wait_time = (attempt + 1) * 3  # 3s, 6s, 9s backoff
                logger.warning(f"[Agent] Rate limit hit (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            return resp.json()
            
        except requests.exceptions.HTTPError as e:
            if resp.status_code != 429 or attempt == max_retries - 1:
                raise e
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
            
    raise Exception("Max retries reached for Groq API")


def run_agent(query: str, session_id: str, user_id: str) -> str:
    """
    Run the manual ReAct loop for a single user turn.

    Args:
        query:      The user's message.
        session_id: The Neo4j session (codebase) to search in.
        user_id:    Used to key Redis chat history.

    Returns:
        The assistant's final text response.
    """
    logger.info(f"Agent called | user={user_id} session={session_id} query={query!r}")

    # 1. Load prior history from Redis
    history = get_history(user_id, session_id)
    logger.info(f"[Agent] Loaded {len(history)} messages from history for user {user_id} session {session_id}")

    # 2. Format history into a readable list for the system prompt
    history_lines = [f"- {m['content']}" for m in history if m.get("role") == "user"]
    history_context = "\n".join(history_lines) if history_lines else "None (This is the beginning of the chat)."
    
    current_system_prompt = SYSTEM_PROMPT.format(history_context=history_context)

    # 3. Build initial message list
    messages: list[dict] = [
        {"role": "system", "content": current_system_prompt},
        {"role": "user", "content": query},
    ]

    final_answer = "I encountered an error generating a response. Please try again."

    # 3. ReAct loop
    for iteration in range(1, _MAX_ITERATIONS + 1):
        logger.info(f"[Agent] Iteration {iteration}/{_MAX_ITERATIONS} | messages={len(messages)}")

        try:
            groq_response = _call_groq(messages)
        except requests.HTTPError as e:
            logger.error(f"[Agent] Groq HTTP error: {e.response.text}")
            break
        except Exception as e:
            logger.error(f"[Agent] Groq call failed: {e}")
            break

        choice = groq_response["choices"][0]
        message = choice["message"]
        tool_calls = message.get("tool_calls")

        # Always add assistant message to the running context
        messages.append(message)

        # ── No tool calls → final answer ──────────────────────────────────
        if not tool_calls:
            final_answer = message.get("content") or "No response generated."
            logger.info(f"[Agent] Final answer at iteration {iteration}")
            break

        # ── Execute each requested tool ───────────────────────────────────
        logger.info(f"[Agent] {len(tool_calls)} tool call(s) requested")
        for call in tool_calls:
            fn_name  = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            call_id  = call["id"]

            # Parse args (Groq may return a string or dict)
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}

            logger.info(f"[Agent] Calling tool '{fn_name}' with args={args}")

            fn = TOOL_MAP.get(fn_name)
            if fn is None:
                result = f"Error: unknown tool '{fn_name}'"
            else:
                try:
                    # Inject session_id which the LLM doesn't know about
                    result = fn(**args, session_id=session_id)
                except Exception as e:
                    result = f"Error executing {fn_name}: {e}"
                    logger.error(f"[Agent] Tool error: {e}")

            logger.info(f"[Agent] Tool '{fn_name}' result length: {len(str(result))} chars")

            # Append tool result in OpenAI format
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": fn_name,
                "content": str(result),
            })

        # Loop continues — LLM will now see tool results and decide next step

    # 4. Save history: only user + assistant turns (not system/tool messages)
    new_turn = [
        {"role": "user", "content": query},
        {"role": "assistant", "content": final_answer},
    ]
    updated_history = history + new_turn
    save_history(user_id, session_id, updated_history)
    logger.info(f"[Agent] Saved history for user {user_id} session {session_id}. Total turns: {len(updated_history) // 2}")

    return final_answer