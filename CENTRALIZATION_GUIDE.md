# Guida alla Centralizzazione di Qwen CLI & Credential Rotation

Questa guida descrive come centralizzare l'uso della `qwen` CLI e di `credential-rotation` per evitare installazioni multiple di Node.js e ottimizzare la gestione delle quote in architetture a moduli o microservizi.

---

## Il Problema: Ridondanza delle Risorse
Installare Node.js e la CLI in ogni modulo/container consuma circa 400MB+ di spazio e memoria per istanza, oltre a rendere difficile la sincronizzazione della rotazione delle credenziali.

## La Soluzione: Puntamento Unico
Centralizzare la logica in un unico punto e far comunicare i moduli tramite protocolli leggeri.

---

## Requisito Comune: Il Volume delle Credenziali
In tutti gli approcci, la directory delle credenziali deve essere esterna e montata nel container "Master":
*   **Host Path:** `/path/to/your/.qwen`
*   **Container Path:** `/root/.qwen` (o la home dell'utente nel container)
*   **Permessi:** Deve essere montato in modalità lettura/scrittura (`rw`) per permettere la rotazione del symlink.

---

## Strategia 1: Qwen-as-a-Service (API HTTP) - CONSIGLIATO
I moduli comunicano con un server centrale tramite semplici richieste HTTP.

### 1. Dockerfile del Master (`qwen-service`)
```dockerfile
FROM node:20-slim as node_base
FROM python:3.11-slim

# Copia node da node_base
COPY --from=node_base /usr/local/bin/node /usr/local/bin/
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# Installa Qwen CLI e credential-rotation
RUN npm install -g @google/qwen
RUN pip install credential-rotation fastapi uvicorn

COPY app.py .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Script API (`app.py`)
```python
from fastapi import FastAPI, HTTPException
from credential_rotation import QwenWrapper

app = FastAPI()
wrapper = QwenWrapper(max_retries=5)

@app.post("/generate")
def generate(payload: dict):
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")
    
    result = wrapper.call(prompt)
    return {"text": result.output, "success": result.success, "attempts": result.attempts}
```

### 3. Esempio di utilizzo (Client)
```bash
curl -X POST http://qwen-service:8000/generate -d '{"prompt": "Spiega il codice..."}'
```

---

## Strategia 2: Il Pattern Worker (Coda Task)
Ideale per pipeline batch asincrone (es. processamento massivo di documenti).

*   **Modulo Client:** Inserisce il prompt in una coda (es. Redis).
*   **Qwen Worker:** Unico container con Node/CLI che legge dalla coda, elabora e scrive il risultato in un database o di nuovo su Redis.

**Vantaggio:** Impedisce il sovraccarico dei modelli LLM limitando il numero di worker attivi contemporaneamente.

---

## Strategia 3: Orchestrazione via Docker Exec
Ideale per script legacy o quando non si vuole implementare un'API.

1. Lancia un container "Master" dormiente: `docker run -d --name qwen-master -v ~/.qwen:/root/.qwen:rw mia-immagine tail -f /dev/null`.
2. Dagli altri moduli, invoca il comando:
```bash
docker exec qwen-master account-qwen --wrapper "Il mio prompt"
```

---

## Tabella Comparativa

| Caratteristica | Approccio 1 (API) | Approccio 2 (Worker) | Approccio 3 (Exec) |
| :--- | :--- | :--- | :--- |
| **Complessità** | Media | Alta | Bassa |
| **Performance** | Alta (Sincrona) | Altissima (Asincrona) | Media (Lancio processo) |
| **Uso ideale** | Web App, Chatbot | Data Scraping, Batch | Script Bash semplici |
| **Dipendenze Client** | Solo `curl` / `requests` | Libreria Redis | Client Docker |

---

## Note sulla Sicurezza
*   Se l'API (Approccio 1) è esposta su una rete non protetta, aggiungi un'autenticazione tramite Header (es. `X-API-Key`).
*   Assicurati che solo il container Master abbia i permessi di scrittura sulla cartella `.qwen` se vuoi un controllo granulare, anche se per la rotazione automatica il `rw` è necessario al processo che esegue lo switch.
