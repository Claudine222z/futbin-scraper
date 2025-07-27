#!/usr/bin/env python3
"""
Script para aguardar o deploy e testar o serviço
"""

import requests
import time
from datetime import datetime

def test_service(url):
    """Testa se o serviço está respondendo"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def wait_for_deploy(service_url):
    """Aguarda o deploy terminar"""
    print("⏳ Aguardando deploy terminar...")
    print("🔄 Isso pode levar 2-5 minutos...")
    
    max_attempts = 30  # 5 minutos (10 segundos cada)
    
    for attempt in range(max_attempts):
        print(f"🔍 Tentativa {attempt + 1}/{max_attempts}...")
        
        if test_service(service_url):
            print("✅ Serviço está respondendo!")
            return True
        
        print("⏳ Serviço ainda não está pronto, aguardando...")
        time.sleep(10)
    
    print("❌ Timeout - serviço não respondeu em 5 minutos")
    return False

def main():
    """Função principal"""
    print("🚀 AGUARDANDO DEPLOY E TESTANDO SERVIÇO")
    print("=" * 60)
    
    service_url = "https://futbin-scraper.onrender.com"
    
    print(f"🎯 Serviço: {service_url}")
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aguardar deploy
    if wait_for_deploy(service_url):
        print("\n🎉 DEPLOY CONCLUÍDO!")
        print("🔍 Testando endpoints...")
        
        # Testar endpoints
        endpoints = ["/", "/health", "/status", "/ping"]
        
        for endpoint in endpoints:
            try:
                url = f"{service_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    
                    # Verificar se é o status do scraper
                    if endpoint == "/status":
                        try:
                            data = response.json()
                            scraper_running = data.get('scraper_running', False)
                            if scraper_running:
                                print("🎉 SCRAPER ESTÁ RODANDO EM BACKGROUND!")
                                stats = data.get('stats', {})
                                if stats:
                                    print(f"📊 Progresso: {stats.get('total_scraped', 0)} cartas")
                            else:
                                print("⚠️ Scraper não está rodando")
                        except:
                            pass
                else:
                    print(f"❌ {endpoint}: Erro {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {endpoint}: Erro - {e}")
        
        print("\n" + "=" * 60)
        print("🎯 RESULTADO FINAL:")
        print("✅ Se todos os endpoints responderam, o serviço está funcionando!")
        print("✅ Se /status mostra 'scraper_running: true', está em background!")
        print("✅ Agora você pode fechar o navegador com segurança!")
        
    else:
        print("\n❌ PROBLEMA NO DEPLOY")
        print("🔧 Verifique:")
        print("1. Render Dashboard - logs do deploy")
        print("2. Configurações - Start Command deve ser 'python app.py'")
        print("3. Variáveis de ambiente configuradas")

if __name__ == "__main__":
    main() 