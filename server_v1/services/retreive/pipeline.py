from datetime import datetime, timedelta, timezone
from services.agent.create_agent import agent_app
# from services.retreive.retrieve_context import retrieve_context
# from services.llm.prompt_template import template
# from services.llm.query_enhancement import enhance_query
# from services.llm.llm import chat
from core.logging import get_logger

logger = get_logger(__name__)

MEMORY_TIMEOUT_HOURS = 24

def perform_global_cleanup():
    try:
        storage = agent_app.checkpointer.storage

        if len(storage.items()) < 10:
            return
        
        threads_to_delete = []
        current_time = datetime.now(timezone.utc)
        
        
        for thread_id, checkpoints in storage.items():
            if not checkpoints:
                threads_to_delete.append(thread_id)
                continue

            try:
                latest_checkpoint_id = max(checkpoints.keys(), key=lambda k: checkpoints[k]['ts'])
                latest_checkpoint = checkpoints[latest_checkpoint_id]
                
                last_active_str = latest_checkpoint.get('ts')
                
                if not last_active_str:
                    continue
                    
                last_active_time = datetime.fromisoformat(last_active_str)
                
                if last_active_time.tzinfo is None:
                    last_active_time = last_active_time.replace(tzinfo=timezone.utc)
                
                time_diff = current_time - last_active_time
                if time_diff > timedelta(hours=MEMORY_TIMEOUT_HOURS):
                    threads_to_delete.append(thread_id)
            
            except Exception as inner_e:
                logger.warning(f"Error parsing thread {thread_id}: {inner_e}")
                continue

        if threads_to_delete:
            logger.info(f"Memory Cleanup: removing {len(threads_to_delete)} expired sessions.")
            for thread_id in threads_to_delete:
                if thread_id in storage:
                    del storage[thread_id]

    except Exception as e:
        logger.error(f"Global memory cleanup failed: {e}")



def run_retreival_pipeline(session_id: str, query: str, user_id: str = "dfsd") -> str:
    logger.info(f"Processing query for user: {user_id}, session: {session_id}")
    
    perform_global_cleanup()
    config = {
        "configurable": {
            "thread_id": user_id,   
            "session_id": session_id, 
            "recursion_limit": 10
        }
    }

    response = agent_app.invoke(
        {"messages": [("user", query)]},
        config=config
    )

    return response["messages"][-1].content

