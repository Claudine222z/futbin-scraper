#!/usr/bin/env python3
"""
Script para manter o serviço ativo na Render
"""

import requests
import time
import os
from datetime import datetime

def ping_service():
    """Faz ping no serviço para mantê-lo ativo"""
    try:
        # URL do seu serviço na Render
        service_url = os.getenv('RENDER_EXTERNAL_URL', 'https://futbin-scraper.onrender.com')
        
        # Endpoints para ping
        ping_urls = [
            f"{service_url}/ping",
            f"{service_url}/health",
            f"{service_url}/status"
        ]
        
        for url in ping_urls:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    print(f"✅ Ping bem-sucedido: {url}")
                else:
                    print(f"⚠️ Ping com status {response.status_code}: {url}")
            except Exception as e:
                print(f"❌ Erro no ping {url}: {e}")
        
    except Exception as e:
        print(f"❌ Erro geral no ping: {e}")

def main():
    """Função principal"""
    print("🔄 Iniciando monitoramento do serviço...")
    
    # Intervalo entre pings (em segundos)
    ping_interval = 600  # 10 minutos
    
    while True:
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n🕐 [{current_time}] Fazendo ping...")
            
            ping_service()
            
            print(f"😴 Aguardando {ping_interval} segundos até o próximo ping...")
            time.sleep(ping_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoramento interrompido pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro no monitoramento: {e}")
            time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente

if __name__ == "__main__":
    main() 