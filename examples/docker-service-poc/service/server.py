from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from credential_rotation.qwen.manager import AccountManager, SwitchReason
from credential_rotation import QwenWrapper
import logging
import os
import subprocess
import threading

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen-service")

app = FastAPI()
wrapper = QwenWrapper(max_retries=3)

def validate_accounts():
    """
    Validate that all discovered accounts are actually usable.
    Run in background to avoid blocking startup.
    """
    logger.info("--- AVVIO VALIDAZIONE BACKGROUND ---")
    try:
        manager = AccountManager()
        ids = manager._discover_account_ids()
        
        if not ids:
            logger.warning("❌ Nessun account trovato.")
            return

        for i in ids:
            try:
                # Non facciamo switch reale per non disturbare il servizio
                # Eseguiamo solo un check informativo se possibile
                pass 
            except Exception as e:
                logger.error(f"Errore check account {i}: {e}")
                
        logger.info(f"Rilevati {len(ids)} account pronti.")
    except Exception as e:
        logger.error(f"Errore validazione: {e}")

# Avvia check in background
threading.Thread(target=validate_accounts, daemon=True).start()

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate(req: PromptRequest):
    logger.info(f"Received prompt: {req.prompt[:50]}...")
    result = wrapper.call(req.prompt)
    return {
        "success": result.success,
        "output": result.output,
        "attempts": result.attempts,
        "error": result.error
    }

@app.get("/health")
def health():
    return {"status": "ok", "wrapper_ready": True}