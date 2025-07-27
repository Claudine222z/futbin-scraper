#!/usr/bin/env python3
"""
Futbin Scraper - Aplicação Flask para Render
"""

from flask import Flask, jsonify, request
import os
from scraper_final_simples import salvar_jogador_completo
from simple_futbin_scraper import SimpleFutbinScraper

app = Flask(__name__)

@app.route('/')
def home():
    """Página inicial"""
    return jsonify({
        "message": "🚀 Futbin Scraper API",
        "status": "online",
        "endpoints": {
            "/": "Esta página",
            "/scrape": "POST - Scrapar jogador por URL",
            "/health": "GET - Status da aplicação"
        }
    })

@app.route('/health')
def health():
    """Verificar status da aplicação"""
    return jsonify({
        "status": "healthy",
        "service": "futbin-scraper"
    })

@app.route('/scrape', methods=['POST'])
def scrape_player():
    """Endpoint para scrapar jogador"""
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
        
        # Scrapar jogador
        scraper = SimpleFutbinScraper()
        player = scraper.scrape_player(url)
        
        if not player:
            return jsonify({
                "error": "Jogador não encontrado",
                "url": url
            }), 404
        
        # Salvar no banco
        success = salvar_jogador_completo()
        
        if not success:
            return jsonify({
                "error": "Erro ao salvar no banco de dados",
                "player": {
                    "name": player.name,
                    "overall": player.overall,
                    "position": player.position
                }
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Jogador scrapado e salvo com sucesso!",
            "player": {
                "id": player.id,
                "name": player.name,
                "overall": player.overall,
                "rating": player.rating,
                "position": player.position,
                "nation": player.nation,
                "league": player.league,
                "club": player.club,
                "stats": {
                    "pace": player.stats.pace,
                    "shooting": player.stats.shooting,
                    "passing": player.stats.passing,
                    "dribbling": player.stats.dribbling,
                    "defending": player.stats.defending,
                    "physical": player.stats.physical
                },
                "detailed_stats": {
                    "acceleration": player.detailed_stats.acceleration,
                    "sprint_speed": player.detailed_stats.sprint_speed,
                    "finishing": player.detailed_stats.finishing,
                    "shot_power": player.detailed_stats.shot_power,
                    "long_shots": player.detailed_stats.long_shots,
                    "volleys": player.detailed_stats.volleys,
                    "penalties": player.detailed_stats.penalties,
                    "vision": player.detailed_stats.vision,
                    "crossing": player.detailed_stats.crossing,
                    "free_kick_accuracy": player.detailed_stats.free_kick_accuracy,
                    "short_passing": player.detailed_stats.short_passing,
                    "long_passing": player.detailed_stats.long_passing,
                    "curve": player.detailed_stats.curve,
                    "agility": player.detailed_stats.agility,
                    "balance": player.detailed_stats.balance,
                    "reactions": player.detailed_stats.reactions,
                    "ball_control": player.detailed_stats.ball_control,
                    "dribbling": player.detailed_stats.dribbling,
                    "composure": player.detailed_stats.composure,
                    "interceptions": player.detailed_stats.interceptions,
                    "heading_accuracy": player.detailed_stats.heading_accuracy,
                    "marking": player.detailed_stats.marking,
                    "standing_tackle": player.detailed_stats.standing_tackle,
                    "sliding_tackle": player.detailed_stats.sliding_tackle,
                    "jumping": player.detailed_stats.jumping,
                    "stamina": player.detailed_stats.stamina,
                    "strength": player.detailed_stats.strength,
                    "aggression": player.detailed_stats.aggression
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Erro interno: {str(e)}"
        }), 500

@app.route('/scrape/eusebio', methods=['GET'])
def scrape_eusebio():
    """Endpoint para scrapar Eusébio (teste)"""
    try:
        # URL do Eusébio
        url = "https://www.futbin.com/25/player/60820/eusebio-da-silva-ferreira"
        
        # Scrapar e salvar
        success = salvar_jogador_completo()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Eusébio scrapado e salvo com sucesso!",
                "url": url
            })
        else:
            return jsonify({
                "error": "Erro ao scrapar Eusébio"
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"Erro interno: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 