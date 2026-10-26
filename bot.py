import os
import time
import hmac
import hashlib
import json
import requests
import threading
from flask import Flask

# --- SERVIDOR WEB ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Shopee Ativo 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CREDENCIAIS ---
SHOPEE_APP_ID = "18391400464"
SHOPEE_SECRET = "5H4XMWIX4XVXL2Z6ZM6JD5V3YTBDMI7A"

PUSHOVER_USER_KEY = "uvj912o52idhqyaf9in6frcjohu4bn"
PUSHOVER_API_TOKEN = "amb9sabvfof81xe5skf3yjvjswdr9a"

pedidos_processados = set()

def enviar_notificacao_pushover(titulo, mensagem):
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": titulo,
        "message": mensagem,
        "sound": "pushover"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("[PUSHOVER] Notificação enviada com sucesso!", flush=True)
        else:
            print(f"[PUSHOVER ERRO] {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"[PUSHOVER EXCEÇÃO] {e}", flush=True)

def verificar_vendas_shopee():
    global pedidos_processados
    
    print("\n[SHOPEE] Executando checagem de vendas...", flush=True)
    endpoint = "https://open-api.affiliate.shopee.com.br/graphql"
    
    agora = int(time.time())
    sete_dias_atras = agora - (7 * 24 * 60 * 60)
    timestamp = agora
    
    # Query GraphQL simplificada em linha única para evitar incompatibilidade na assinatura
    query_str = f"query{{conversionReport(page:1,limit:20,purchaseTimeStart:{sete_dias_atras},purchaseTimeEnd:{agora}){{nodes{{orders{{orderId}}}}}}}}"
    
    payload = {"query": query_str}
    payload_json = json.dumps(payload, separators=(',', ':'))
    
    base_string = f"{SHOPEE_APP_ID}{timestamp}{payload_json}"
    signature = hmac.new(
        SHOPEE_SECRET.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 credential={SHOPEE_APP_ID}, timestamp={timestamp}, signature={signature}"
    }
    
    try:
        response = requests.post(endpoint, data=payload_json, headers=headers, timeout=15)
        print(f"[SHOPEE STATUS CODE] {response.status_code}", flush=True)
        
        dados = response.json()
        print(f"[SHOPEE RESPOSTA BRUTA]: {dados}", flush=True)
        
        nodes = dados.get("data", {}).get("conversionReport", {}).get("nodes", []) or []
        
        novas_vendas = 0
        for node in nodes:
            for order in node.get("orders", []):
                order_id = order.get("orderId")
                if order_id and order_id not in pedidos_processados:
                    print(f"[NOVA VENDA DETECTADA] Pedido #{order_id}", flush=True)
                    enviar_notificacao_pushover(
                        "🎉 Nova Venda Shopee!",
                        f"Pedido #{order_id}"
                    )
                    pedidos_processados.add(order_id)
                    novas_vendas += 1
                    
        if not nodes or novas_vendas == 0:
            print("[SHOPEE] Nenhuma venda nova retornada nesta checagem.", flush=True)
            
    except Exception as e:
        print(f"[SHOPEE ERRO/EXCEÇÃO]: {e}", flush=True)

def loop_do_bot():
    time.sleep(3)
    while True:
        try:
            verificar_vendas_shopee()
        except Exception as err:
            print(f"[LOOP ERRO]: {err}", flush=True)
        time.sleep(120)

if __name__ == "__main__":
    threading.Thread(target=loop_do_bot, daemon=True).start()
    run_flask()
