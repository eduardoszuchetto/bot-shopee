import os
import time
import hmac
import hashlib
import json
import requests
import threading
from flask import Flask

# --- SERVIDOR WEB (Abre a porta 10000 exigida pelo Render Free) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Shopee Ativo 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CREDENCIAIS ---
SHOPEE_APP_ID = "18391400464"
SHOPEE_SECRET = "7HXPKZGWFRZZIUCI2P3JTYXU4XF6RQ5I"

PUSHOVER_USER_KEY = "uvj912o52idhqyaf9in6frcjohu4bn"
PUSHOVER_API_TOKEN = "amb9sabvfof81xe5skf3yjvjswdr9a"

# Conjunto em memória para registrar pedidos já notificados
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
    endpoint = "https://open-api.affiliate.shopee.com.br/open_api/v2/order/get_order_list"
    
    agora = int(time.time())
    sete_dias_atras = agora - (7 * 24 * 60 * 60)
    timestamp = agora
    
    # Assinatura HMAC no padrão oficial da Open API da Shopee: AppId + Timestamp + Secret
    base_string = f"{SHOPEE_APP_ID}{timestamp}{SHOPEE_SECRET}"
    signature = hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 credential={SHOPEE_APP_ID}, timestamp={timestamp}, signature={signature}"
    }
    
    payload = {
        "page_size": 20,
        "page": 1,
        "purchase_time_start": sete_dias_atras,
        "purchase_time_end": agora
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        print(f"[SHOPEE STATUS CODE] {response.status_code}", flush=True)
        
        dados = response.json()
        print(f"[SHOPEE RESPOSTA BRUTA]: {dados}", flush=True)
        
        # Extração flexível da lista de pedidos
        data_obj = dados.get("data") or {}
        orders = []
        if isinstance(data_obj, dict):
            orders = data_obj.get("nodes") or data_obj.get("order_list") or []
        elif isinstance(data_obj, list):
            orders = data_obj
            
        if orders:
            novas_vendas = 0
            for pedido in reversed(orders):
                order_id = pedido.get("order_id") or pedido.get("orderId")
                valor = pedido.get("total_commission") or pedido.get("commissionRate") or "0.00"
                
                if order_id and order_id not in pedidos_processados:
                    print(f"[NOVA VENDA DETECTADA] Pedido #{order_id}", flush=True)
                    enviar_notificacao_pushover(
                        "🎉 Nova Venda Shopee!",
                        f"Pedido #{order_id}\nComissão: R$ {valor}"
                    )
                    pedidos_processados.add(order_id)
                    novas_vendas += 1
            
            if novas_vendas == 0:
                print("[SHOPEE] Nenhuma venda nova nesta checagem.", flush=True)
        else:
            print("[SHOPEE] Nenhum pedido retornado pela API no momento.", flush=True)
            
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
