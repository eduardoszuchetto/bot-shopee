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

ultimo_order_id = None

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
            print("[PUSHOVER] Notificação enviada com sucesso!")
        else:
            print(f"[PUSHOVER ERRO] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[PUSHOVER EXCEÇÃO] {e}")

def verificar_vendas_shopee():
    global ultimo_order_id
    
    print("\n[SHOPEE] Iniciando verificação de vendas...")
    endpoint = "https://open-api.affiliate.shopee.com.br/open_api/v2/order/get_order_list"
    
    agora = int(time.time())
    sete_dias_atras = agora - (7 * 24 * 60 * 60)
    timestamp = agora
    
    payload = {
        "page_size": 10,
        "page": 1,
        "purchase_time_start": sete_dias_atras,
        "purchase_time_end": agora
    }
    
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
        print(f"[SHOPEE STATUS CODE] {response.status_code}")
        
        dados = response.json()
        print(f"[SHOPEE RESPOSTA BRUTA]: {dados}")
        
        # Tenta capturar a lista de ordens independente da estrutura da chave
        data_obj = dados.get("data") or {}
        orders = []
        if isinstance(data_obj, dict):
            orders = data_obj.get("nodes") or data_obj.get("order_list") or []
        elif isinstance(data_obj, list):
            orders = data_obj
            
        if orders:
            primeiro_pedido = orders[0]
            order_id = primeiro_pedido.get("order_id") or primeiro_pedido.get("orderId")
            valor = primeiro_pedido.get("total_commission") or primeiro_pedido.get("commissionRate") or "0.00"
            
            print(f"[SHOPEE] Encontrados {len(orders)} pedidos nos últimos 7 dias. Último pedido: #{order_id}")
            
            if order_id and order_id != ultimo_order_id:
                print(f"[NOVA VENDA DETECTADA] Pedido #{order_id}")
                enviar_notificacao_pushover(
                    "🎉 Nova Venda Shopee!",
                    f"Pedido #{order_id}\nComissão: R$ {valor}"
                )
                ultimo_order_id = order_id
            else:
                print("[SHOPEE] Nenhuma venda nova nesta checagem.")
        else:
            print("[SHOPEE] Nenhum pedido retornado pela API nos últimos 7 dias.")
            
    except Exception as e:
        print(f"[SHOPEE ERRO/EXCEÇÃO]: {e}")

def loop_do_bot():
    time.sleep(3)
    while True:
        try:
            verificar_vendas_shopee()
        except Exception as err:
            print(f"[LOOP ERRO]: {err}")
        time.sleep(120)

if __name__ == "__main__":
    # Roda o monitoramento em thread secundária
    threading.Thread(target=loop_do_bot, daemon=True).start()
    
    # Roda o Flask no processo principal
    run_flask()
