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
            '%(asctime)s - %(levelname)s: [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        ws_handler = WebSocketLogHandler()
        ws_handler.setFormatter(formatter)
        logger.addHandler(ws_handler)
        
        # Axiom Remote Logging integration
        import os
        axiom_token = os.getenv("AXIOM_TOKEN")
        axiom_dataset = os.getenv("AXIOM_DATASET")
        
        if axiom_token and axiom_dataset:
            try:
                import axiom_py
                from axiom_py.logging import AxiomHandler
                
                # Instantiate Axiom client and handler
                axiom_client = axiom_py.Client(token=axiom_token)
                axiom_handler = AxiomHandler(axiom_client, axiom_dataset)
                axiom_handler.setFormatter(formatter)
                
                logger.addHandler(axiom_handler)
                print(f"✅ Axiom remote logging successfully connected to dataset: {axiom_dataset}")
            except ImportError:
                print("⚠️ axiom-py is not installed. Skipping remote logging.")
            except Exception as e:
                print(f"❌ Failed to attach Axiom logger: {e}")
    
    return logger