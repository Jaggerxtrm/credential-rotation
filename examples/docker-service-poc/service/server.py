from fastapi import FastAPI
from pydantic import BaseModel
from credential_rotation.qwen.manager import AccountManager, SwitchReason
from credential_rotation import QwenWrapper
import logging
import subprocess
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qwen-service")

app = FastAPI()
wrapper = QwenWrapper(max_retries=3)

@app.get("/ping-all")
def ping_all_accounts():
    """
    Testa ogni account configurato eseguendo un comando reale.
    """
    manager = AccountManager()
    ids = manager._discover_account_ids()
    report = []
    
    logger.info(f"Avvio ping test per {len(ids)} account...")
    
    for i in ids:
        logger.info(f"Testando Account {i}...")
        try:
            # Switch forzato
            manager.switch_to(i, reason=SwitchReason.TEST)
            
            # Esecuzione comando Qwen (posizionale)
            # Usiamo un timeout per sicurezza
            result = subprocess.run(
                ["qwen", "say hello in one word"], 
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            report.append({
                "account": i,
                "success": success,
                "output": result.stdout.strip() if success else None,
                "error": result.stderr.strip() if not success else None
            })
            
            if success:
                logger.info(f"✅ Account {i} funzionante: {result.stdout.strip()}")
            else:
                logger.error(f"❌ Account {i} fallito: {result.stderr.strip()[:100]}")
                
        except Exception as e:
            report.append({"account": i, "success": False, "error": str(e)})
            
    return {"total": len(ids), "results": report}

@app.post("/generate")
def generate(req: dict):
    # Endpoint standard per l'uso normale
    prompt = req.get("prompt", "hello")
    result = wrapper.call(prompt)
    return {
        "success": result.success,
        "output": result.output,
        "attempts": result.attempts
    }

@app.get("/health")
def health():
    manager = AccountManager()
    state = manager.get_state()
    return {"status": "ok", "current_account": state.current_index}