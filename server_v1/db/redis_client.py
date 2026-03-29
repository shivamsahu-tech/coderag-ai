import os
import json
import redis
from dotenv import load_dotenv
from core.logging import get_logger

load_dotenv()
logger = get_logger(__name__)

_MAX_HISTORY_QUESTIONS = 20  # Keep last 20 user questions per user+session

_redis_client = None

# In-memory fallback if Redis is unavailable
_local_cache: dict[str, list[dict]] = {}


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        url = os.getenv("REDIS_URL")
        if not url:
            raise ValueError("REDIS_URL is missing from environment variables")
        _redis_client = redis.from_url(url, decode_responses=True)
        logger.info("Connected to Redis successfully")
    return _redis_client


def get_history(user_id: str, session_id: str) -> list[dict]:
    """Load past user questions. Falls back to in-memory cache if Redis is down."""
    key = f"chat:{user_id}:{session_id}"
    try:
        client = get_redis_client()
        raw = client.get(key)
        if not raw:
            # Also check the local cache in case we just wrote to it
            return _local_cache.get(key, [])
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
        return _local_cache.get(key, [])


def save_history(user_id: str, session_id: str, messages: list[dict]) -> None:
    """
    Persist only the user's questions — no answers — to save space.
    Falls back to in-memory cache if Redis is down.
    """
    key = f"chat:{user_id}:{session_id}"
    # Only store 'user' messages (questions)
    questions = [m for m in messages if m.get("role") == "user"]
    # Cap to last N questions
    if len(questions) > _MAX_HISTORY_QUESTIONS:
        questions = questions[-_MAX_HISTORY_QUESTIONS:]

    # Always write to local cache first (instant and reliable)
    _local_cache[key] = questions

    try:
        client = get_redis_client()
        client.set(key, json.dumps(questions))
        logger.info(f"Saved {len(questions)} questions to Redis for user {user_id}")
    except Exception as e:
        logger.warning(f"Redis unavailable, history stored in-memory only: {e}")
