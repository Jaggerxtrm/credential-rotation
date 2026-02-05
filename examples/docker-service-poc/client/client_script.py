
import requests
import time
import json

URL_PING = "http://qwen-service:8000/ping-all"

print("\n" + "="*50)
print("   QWEN MULTI-ACCOUNT PING TEST (CONTAINER)")
print("="*50 + "\n")

# Attesa startup server
time.sleep(5)

try:
    print("Inviando richiesta di test globale...")
    start_time = time.time()
    response = requests.get(URL_PING, timeout=300) # Timeout lungo per coprire tutti gli account
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTest completato in {elapsed:.2f}s")
        print(f"Account rilevati: {data['total']}\n")
        
        for res in data['results']:
            status = "✅ OK" if res['success'] else "❌ FALLITO"
            print(f"Account {res['account']}: {status}")
            if res['success']:
                print(f"   Risposta: {res['output']}")
            else:
                print(f"   Errore: {res['error'][:150]}...")
            print("-" * 20)
            
        success_count = sum(1 for r in data['results'] if r['success'])
        if success_count == data['total']:
            print("\n🎉 TUTTI GLI ACCOUNT SONO OPERATIVI NEL CONTAINER!")
        else:
            print(f"\n⚠ ATTENZIONE: Solo {success_count}/{data['total']} account funzionano.")
            
    else:
        print(f"Errore Server: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Errore Connessione: {e}")

print("\n" + "="*50)
