import os
import time
import hmac
import hashlib
import requests
import threading
from flask import Flask

# --- SERVIDOR WEB (Mantém o Render ativo no plano gratuito) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Shopee ativo e a monitorizar vendas 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CREDENCIAIS CONFIGURADAS ---
SHOPEE_APP_ID = "18391400464"
SHOPEE_SECRET = "7HXPKZGWFRZZIUCI2P3JTYXU4XF6RQ5I"

PUSHOVER_USER_KEY = "uvj912o52idhqyaf9in6frcjohu4bn"
PUSHOVER_API_TOKEN = "amb9sabvfof81xe5skf3yjvjswdr9a"

# Controlo de notificações duplicadas
ultimo_order_id = None

def enviar_notificacao_pushover(titulo, mensagem):
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": titulo,
        "message": mensagem,
        "sound": "cashregister"  # Som de caixa registadora
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Notificação enviada via Pushover com sucesso!")
        else:
            print(f"Erro ao enviar Pushover: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exceção no Pushover: {e}")

def verificar_vendas_shopee():
    global ultimo_order_id
    
    endpoint = "https://open-api.affiliate.shopee.com.br/open_api/v2/order/get_order_list"
    timestamp = int(time.time())
    
    # Gerar assinatura HMAC SHA256 exigida pela Shopee
    base_string = f"{SHOPEE_APP_ID}{timestamp}"
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
        print("Consultando API da Shopee...")
        payload = {
            "page_size": 10,
            "page": 1
        }
        
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            orders = dados.get("data", {}).get("nodes", [])
            
            if orders:
                primeiro_pedido = orders[0]
                order_id = primeiro_pedido.get("order_id")
                valor = primeiro_pedido.get("total_commission", "0.00")
                
                if order_id and order_id != ultimo_order_id:
                    print(f"Nova venda detetada: #{order_id}")
                    enviar_notificacao_pushover(
                        "🎉 Nova Venda Shopee!",
                        f"Pedido #{order_id}\nComissão: R$ {valor}"
                    )
                    ultimo_order_id = order_id
                else:
                    print("Nenhuma venda nova nesta checagem.")
            else:
                print("Nenhum pedido recente retornado.")
        else:
            print(f"Erro na resposta da Shopee: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exceção na consulta Shopee: {e}")

def loop_do_bot():
    while True:
        verificar_vendas_shopee()
        # Executa a verificação a cada 15 minutos (900 segundos)
        time.sleep(900)

if __name__ == "__main__":
    # 1. Inicia o servidor web em segundo plano para manter o Render ligado
    threading.Thread(target=run_flask, daemon=True).start()
    
    # TESTE INICIAL: Dispara uma notificação assim que o bot arrancar para validar o app
    enviar_notificacao_pushover("🎉 Teste Shopee!", "Pedido #TESTE123\nComissão: R$ 15.50")
    
    # 2. Inicia a verificação contínua das vendas
    loop_do_bot()
