import os
import time
import hmac
import hashlib
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
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("[PUSHOVER] Notificação enviada com sucesso!")
        else:
            print(f"[PUSHOVER ERRO] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[PUSHOVER EXCEÇÃO] {e}")

def verificar_vendas_shopee():
    global ultimo_order_id
    
    try:
        print("\n--- CONSULTANDO API SHOPEE (MODO TESTE) ---")
        
        # SIMULAÇÃO DE PEDIDO PARA TESTE
        orders = [{"order_id": "TESTE_SHOPEE_999", "total_commission": "25.90"}]
        
        if orders:
            primeiro_pedido = orders[0]
            order_id = primeiro_pedido.get("order_id")
            valor = primeiro_pedido.get("total_commission", "0.00")
            
            if order_id and order_id != ultimo_order_id:
                print(f"[NOVA VENDA DETETADA] Pedido #{order_id}")
                enviar_notificacao_pushover(
                    "🎉 Nova Venda Shopee! (TESTE)",
                    f"Pedido #{order_id}\nComissão: R$ {valor}"
                )
                ultimo_order_id = order_id
            else:
                print("[SHOPEE] Nenhuma venda nova nesta checagem.")
        else:
            print("[SHOPEE] Nenhum pedido retornado.")
            
    except Exception as e:
        print(f"[SHOPEE EXCEÇÃO] {e}")

def loop_do_bot():
    while True:
        verificar_vendas_shopee()
        time.sleep(120)

if __name__ == "__main__":
    # 1. Inicia o Flask em background para liberar a porta do Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Inicia o loop contínuo de verificação
    loop_do_bot()
