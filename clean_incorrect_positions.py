#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpar posições incorretas do banco de dados
Remove posições auxiliares e roles incorretos e re-scraping apenas dessas cartas
"""

import mysql.connector
import requests
import time
import logging
from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import random

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean_positions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'futbin_scraper'
}

# Configuração Telegram
TELEGRAM_BOT_TOKEN = '8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw'

def get_telegram_chat_id():
    """Obtém o chat_id automaticamente"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('ok') and data.get('result'):
            for update in reversed(data['result']):
                if 'message' in update:
                    return str(update['message']['chat']['id'])
        
        return None
    except Exception as e:
        logging.error(f"Erro ao obter chat_id: {e}")
        return None

TELEGRAM_CHAT_ID = get_telegram_chat_id()

def send_telegram_message(message):
    """Envia mensagem via Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logging.info("✅ Mensagem enviada via Telegram")
        else:
            logging.error(f"❌ Erro ao enviar mensagem Telegram: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Erro ao enviar mensagem Telegram: {e}")

def get_database_connection():
    """Cria conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao conectar ao banco: {e}")
        return None

def identify_cards_with_incorrect_positions():
    """Identifica cartas com posições incorretas"""
    connection = get_database_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Busca cartas com muitas posições auxiliares (provavelmente incorretas)
        query = """
        SELECT id, name, overall, alt_position_json, roles_json, futbin_url
        FROM players 
        WHERE (alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL)
        OR (roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL)
        ORDER BY overall DESC
        """
        
        cursor.execute(query)
        cards = cursor.fetchall()
        
        logging.info(f"🔍 Encontradas {len(cards)} cartas com posições/roles para verificar")
        
        # Filtra cartas com posições suspeitas
        suspicious_cards = []
        for card in cards:
            alt_positions = []
            roles = []
            
            try:
                if card['alt_position_json'] and card['alt_position_json'] != '[]':
                    alt_positions = json.loads(card['alt_position_json'])
                if card['roles_json'] and card['roles_json'] != '[]':
                    roles = json.loads(card['roles_json'])
            except:
                alt_positions = []
                roles = []
            
            # Considera suspeito se tem muitas posições ou roles
            if len(alt_positions) > 3 or len(roles) > 5:
                suspicious_cards.append(card)
                logging.info(f"⚠️ Carta suspeita: {card['name']} - Posições: {alt_positions}, Roles: {roles}")
        
        logging.info(f"🎯 {len(suspicious_cards)} cartas identificadas como suspeitas")
        return suspicious_cards
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao buscar cartas: {e}")
        return []
    finally:
        if connection:
            connection.close()

def clean_incorrect_positions(card_id):
    """Limpa posições incorretas de uma carta específica"""
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Limpa os campos de posições auxiliares e roles
        query = """
        UPDATE players 
        SET alt_position_json = '[]', roles_json = '[]', updated_at = NOW()
        WHERE id = %s
        """
        
        cursor.execute(query, (card_id,))
        connection.commit()
        
        logging.info(f"🧹 Posições limpas para carta ID: {card_id}")
        return True
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao limpar posições: {e}")
        return False
    finally:
        if connection:
            connection.close()

def scrape_player_data(url):
    """Scraping de dados de um jogador específico"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrai posições auxiliares (apenas se existirem explicitamente)
        alt_positions = []
        alt_pos_text = soup.find(string=re.compile(r'Alt POS|Alternative Positions', re.IGNORECASE))
        if alt_pos_text:
            # Procura por posições próximas ao texto
            parent = alt_pos_text.parent
            if parent:
                # Procura por siglas de posições (ST, CM, CB, etc.)
                pos_matches = re.findall(r'\b(ST|CF|LW|RW|LM|RM|CAM|CM|CDM|CB|LB|RB|GK)\b', parent.get_text(), re.IGNORECASE)
                alt_positions = list(set(pos_matches))
        
        # Extrai roles (apenas se existirem explicitamente)
        roles = []
        roles_text = soup.find(string=re.compile(r'Roles|Playstyles', re.IGNORECASE))
        if roles_text:
            # Procura por roles próximos ao texto
            parent = roles_text.parent
            if parent:
                # Procura por roles específicos
                role_matches = re.findall(r'\b(Finesse|Technical|Rapid|Low|High|Controlled|Explosive|Power|Precision|Glitch|Relentless|Incisive|Tiki Taka|Long Ball|Possession|Quick Counter|Out Wide|Route One|Gegenpressing|Park the Bus|Balanced|Attacking|Defensive)\b', parent.get_text(), re.IGNORECASE)
                roles = list(set(role_matches))
        
        return {
            'alt_positions': alt_positions,
            'roles': roles
        }
        
    except Exception as e:
        logging.error(f"❌ Erro ao scraping {url}: {e}")
        return {'alt_positions': [], 'roles': []}

def update_player_positions(card_id, alt_positions, roles):
    """Atualiza posições de uma carta no banco"""
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        query = """
        UPDATE players 
        SET alt_position_json = %s, roles_json = %s, updated_at = NOW()
        WHERE id = %s
        """
        
        cursor.execute(query, (json.dumps(alt_positions), json.dumps(roles), card_id))
        connection.commit()
        
        logging.info(f"✅ Posições atualizadas para carta ID: {card_id}")
        return True
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao atualizar posições: {e}")
        return False
    finally:
        if connection:
            connection.close()

def main():
    """Função principal"""
    logging.info("🧹 INICIANDO LIMPEZA DE POSIÇÕES INCORRETAS")
    send_telegram_message("🧹 <b>INICIANDO LIMPEZA DE POSIÇÕES INCORRETAS</b>")
    
    # Identifica cartas com posições incorretas
    suspicious_cards = identify_cards_with_incorrect_positions()
    
    if not suspicious_cards:
        logging.info("✅ Nenhuma carta com posições incorretas encontrada")
        send_telegram_message("✅ <b>Nenhuma carta com posições incorretas encontrada</b>")
        return
    
    logging.info(f"🎯 Iniciando correção de {len(suspicious_cards)} cartas")
    send_telegram_message(f"🎯 <b>Iniciando correção de {len(suspicious_cards)} cartas</b>")
    
    corrected_count = 0
    
    for i, card in enumerate(suspicious_cards, 1):
        try:
            logging.info(f"🔧 Corrigindo carta {i}/{len(suspicious_cards)}: {card['name']}")
            
            # Limpa posições incorretas
            if clean_incorrect_positions(card['id']):
                # Re-scraping para coletar dados corretos
                player_data = scrape_player_data(card['futbin_url'])
                
                # Atualiza com dados corretos
                if update_player_positions(card['id'], player_data['alt_positions'], player_data['roles']):
                    corrected_count += 1
                    logging.info(f"✅ Carta corrigida: {card['name']} - Posições: {player_data['alt_positions']}, Roles: {player_data['roles']}")
                else:
                    logging.error(f"❌ Erro ao atualizar carta: {card['name']}")
            
            # Pausa entre requests
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            logging.error(f"❌ Erro ao corrigir carta {card['name']}: {e}")
    
    # Relatório final
    logging.info(f"🎉 LIMPEZA CONCLUÍDA: {corrected_count}/{len(suspicious_cards)} cartas corrigidas")
    send_telegram_message(f"🎉 <b>LIMPEZA CONCLUÍDA</b>\n✅ Cartas corrigidas: {corrected_count}/{len(suspicious_cards)}")

if __name__ == "__main__":
    main() 