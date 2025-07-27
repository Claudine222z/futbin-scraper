#!/usr/bin/env python3
"""
Futbin Scraper - Aplicação Flask para Render com Scraper em Background
"""

from flask import Flask, jsonify, request
import os
import threading
import time
from datetime import datetime
from futbin_mass_scraper import FutbinMassScraper

app = Flask(__name__)

# Variável global para controlar o scraper
scraper_instance = None
scraper_thread = None
is_running = False

def run_scraper_in_background():
    """Executa o scraper em background"""
    global scraper_instance, is_running
    
    try:
        # Token do Telegram das variáveis de ambiente
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw')
        
        # Criar scraper
        scraper_instance = FutbinMassScraper(telegram_token)
        is_running = True
        
        # Executar scraping em massa
        scraper_instance.run_mass_scraping()
        
    except Exception as e:
        print(f"❌ Erro no scraper em background: {e}")
        is_running = False

def start_scraper():
    """Inicia o scraper em uma thread separada"""
    global scraper_thread, is_running
    
    if not is_running:
        scraper_thread = threading.Thread(target=run_scraper_in_background, daemon=True)
        scraper_thread.start()
        print("🚀 Scraper iniciado em background")
        return True
    else:
        print("⚠️ Scraper já está rodando")
        return False

@app.route('/')
def home():
    """Página inicial"""
    return jsonify({
        "message": "🚀 Futbin Scraper API",
        "status": "online",
        "scraper_status": "running" if is_running else "stopped",
        "endpoints": {
            "/": "Esta página",
            "/start": "POST - Iniciar scraper",
            "/status": "GET - Status do scraper",
            "/health": "GET - Status da aplicação",
            "/ping": "GET - Manter ativo"
        }
    })

@app.route('/health')
def health():
    """Verificar status da aplicação"""
    return jsonify({
        "status": "healthy",
        "service": "futbin-scraper",
        "scraper_running": is_running,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/ping')
def ping():
    """Endpoint para manter o serviço ativo"""
    return jsonify({
        "status": "pong",
        "scraper_running": is_running,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/start', methods=['POST'])
def start_scraper_endpoint():
    """Endpoint para iniciar o scraper"""
    try:
        if start_scraper():
            return jsonify({
                "message": "🚀 Scraper iniciado com sucesso!",
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "message": "⚠️ Scraper já está rodando",
                "status": "already_running",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            "error": f"Erro ao iniciar scraper: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/status')
def scraper_status():
    """Endpoint para verificar status do scraper"""
    try:
        if scraper_instance:
            stats = scraper_instance.stats
            return jsonify({
                "scraper_running": is_running,
                "stats": {
                    "total_scraped": stats.get('total_scraped', 0),
                    "success_count": stats.get('success_count', 0),
                    "error_count": stats.get('error_count', 0),
                    "skipped_count": stats.get('skipped_count', 0),
                    "current_player": stats.get('current_player', ''),
                    "start_time": stats.get('start_time', '').isoformat() if stats.get('start_time') else None
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "scraper_running": False,
                "message": "Scraper não iniciado",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            "error": f"Erro ao obter status: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/scrape', methods=['POST'])
def scrape_player():
    """Endpoint para scrapar jogador específico"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "error": "URL do jogador é obrigatória",
                "example": {
                    "url": "https://www.futbin.com/25/player/60820/eusebio-da-silva-ferreira"
                }
            }), 400
        
        url = data['url']
        
        # Criar scraper temporário
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw')
        scraper = FutbinMassScraper(telegram_token)
        
        # Scrapar jogador
        player = scraper.scrape_player(url)
        
        if not player:
            return jsonify({
                "error": "Jogador não encontrado",
                "url": url
            }), 404
        
        # Salvar no banco
        success = scraper.save_to_mysql(player)
        
        if not success:
            return jsonify({
                "error": "Erro ao salvar no banco de dados",
                "player": {
                    "name": player.nome,
                    "overall": player.overall,
                    "position": player.posicao
                }
            }), 500
        
        return jsonify({
            "message": "✅ Jogador scrapado e salvo com sucesso!",
            "player": {
                "id": player.id,
                "name": player.nome,
                "overall": player.overall,
                "position": player.posicao,
                "nation": player.nacao,
                "league": player.liga,
                "club": player.clube,
                "image_url": player.url_imagem
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Erro interno: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Iniciar scraper automaticamente quando a aplicação subir
    print("🚀 Iniciando Futbin Scraper...")
    start_scraper()
    
    # Iniciar servidor Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Servidor iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 