#!/usr/bin/env python3
"""
Script para verificar o status do serviço na Render
"""

import requests
import json
from datetime import datetime

def check_render_service():
    """Verifica o status do serviço na Render"""
    
    print("🔍 VERIFICANDO STATUS DO SERVIÇO NA RENDER")
    print("=" * 60)
    
    # URL do seu serviço (substitua pela sua URL real)
    service_url = input("🌐 Digite a URL do seu serviço na Render: ").strip()
    
    if not service_url:
        print("❌ URL não fornecida")
        return
    
    # Remover barra final se existir
    if service_url.endswith('/'):
        service_url = service_url[:-1]
    
    print(f"\n🎯 Verificando: {service_url}")
    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Testar endpoints
    endpoints = [
        ("/", "Página inicial"),
        ("/health", "Status de saúde"),
        ("/status", "Status do scraper"),
        ("/ping", "Ping")
    ]
    
    for endpoint, description in endpoints:
        try:
            url = f"{service_url}{endpoint}"
            print(f"\n🔍 Testando {description}: {url}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Sucesso! Status: {response.status_code}")
                
                try:
                    data = response.json()
                    print(f"📊 Resposta JSON:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Verificar se é o endpoint de status
                    if endpoint == "/status":
                        scraper_running = data.get('scraper_running', False)
                        if scraper_running:
                            print("🎉 SCRAPER ESTÁ RODANDO EM BACKGROUND!")
                            stats = data.get('stats', {})
                            if stats:
                                print(f"📈 Progresso:")
                                print(f"   - Total scrapado: {stats.get('total_scraped', 0)}")
                                print(f"   - Sucessos: {stats.get('success_count', 0)}")
                                print(f"   - Erros: {stats.get('error_count', 0)}")
                        else:
                            print("⚠️ Scraper não está rodando")
                            
                except:
                    print(f"📄 Resposta: {response.text[:200]}...")
            else:
                print(f"❌ Erro! Status: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
                
        except Exception as e:
            print(f"❌ Erro ao testar {endpoint}: {e}")
    
    print("\n" + "=" * 60)
    print("📋 DIAGNÓSTICO:")
    print("✅ Se todos os endpoints responderam, o serviço está funcionando")
    print("✅ Se /status mostra 'scraper_running: true', está em background")
    print("✅ Se não, pode ser que ainda não tenha feito deploy da versão atualizada")
    print("\n🔄 Para verificar se está usando a versão correta:")
    print("1. Vá para Render Dashboard")
    print("2. Verifique os logs do deploy")
    print("3. Procure por: '🚀 Scraper iniciado em background'")

if __name__ == "__main__":
    check_render_service() 