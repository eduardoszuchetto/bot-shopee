import os
import time
import hmac
import hashlib
import requests

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
    
    endpoint = "https://open-api.affiliate.shopee.com.br/open_api/v2/order/get_order_list"
    timestamp = int(time.time())
    
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
        print("\n--- CONSULTANDO SHOPEE ---")
        payload = {"page_size": 10, "page": 1}
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            print("RESPOSTA SHOPEE:", dados)
            
            orders = dados.get("data", {}).get("nodes", [])
            if orders:
                primeiro_pedido = orders[0]
                order_id = primeiro_pedido.get("order_id")
                valor = primeiro_pedido.get("total_commission", "0.00")
                
                if order_id and order_id != ultimo_order_id:
                    print(f"[NOVA VENDA] Pedido #{order_id}")
                    enviar_notificacao_pushover(
                        "🎉 Nova Venda Shopee!",
                        f"Pedido #{order_id}\nComissão: R$ {valor}"
                    )
                    ultimo_order_id = order_id
                else:
                    print("[SHOPEE] Sem vendas novas nesta checagem.")
            else:
                print("[SHOPEE] Nenhum pedido retornado.")
        else:
            print(f"[SHOPEE ERRO] Status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"[SHOPEE EXCEÇÃO] {e}")

if __name__ == "__main__":
    print(">>> BOT INICIADO COM SUCESSO <<<")
    while True:
        verificar_vendas_shopee()
        time.sleep(120)
