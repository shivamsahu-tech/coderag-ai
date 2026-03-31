import logging
import sys 
import contextvars
import asyncio
from core.websocket import manager

req_id_var = contextvars.ContextVar("req_id", default=None)

class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        req_id = req_id_var.get()
        if req_id:
            try:
                log_entry = self.format(record)
                if hasattr(manager, 'loop') and manager.loop:
                    # Thread-safe way to call async code from synchronous thread
                    asyncio.run_coroutine_threadsafe(manager.send_log(log_entry, req_id), manager.loop)
            except Exception:
                pass

def get_logger(name: str):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(levelname)s:     [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        ws_handler = WebSocketLogHandler()
        ws_handler.setFormatter(formatter)
        logger.addHandler(ws_handler)
    
    return logger