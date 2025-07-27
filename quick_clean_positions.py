#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script RÁPIDO para limpar posições incorretas
Executa limpeza direta no banco de dados
"""

import mysql.connector
import json
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'futbin_scraper'
}

def get_database_connection():
    """Cria conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao conectar ao banco: {e}")
        return None

def clean_all_incorrect_positions():
    """Limpa TODAS as posições auxiliares e roles incorretos"""
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Limpa TODOS os campos de posições auxiliares e roles
        query = """
        UPDATE players 
        SET alt_position_json = '[]', roles_json = '[]', updated_at = NOW()
        WHERE alt_position_json != '[]' OR roles_json != '[]'
        """
        
        cursor.execute(query)
        affected_rows = cursor.rowcount
        connection.commit()
        
        logging.info(f"🧹 LIMPEZA CONCLUÍDA: {affected_rows} cartas limpas")
        return affected_rows
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao limpar posições: {e}")
        return False
    finally:
        if connection:
            connection.close()

def show_current_status():
    """Mostra status atual das posições no banco"""
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Conta cartas com posições
        query = """
        SELECT 
            COUNT(*) as total_cards,
            COUNT(CASE WHEN alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL THEN 1 END) as cards_with_alt_positions,
            COUNT(CASE WHEN roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL THEN 1 END) as cards_with_roles
        FROM players
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        logging.info(f"📊 STATUS ATUAL:")
        logging.info(f"   Total de cartas: {result['total_cards']}")
        logging.info(f"   Cartas com posições auxiliares: {result['cards_with_alt_positions']}")
        logging.info(f"   Cartas com roles: {result['cards_with_roles']}")
        
        # Mostra algumas cartas com posições incorretas
        query2 = """
        SELECT name, overall, alt_position_json, roles_json
        FROM players 
        WHERE (alt_position_json != '[]' AND alt_position_json != 'null' AND alt_position_json IS NOT NULL)
        OR (roles_json != '[]' AND roles_json != 'null' AND roles_json IS NOT NULL)
        ORDER BY overall DESC
        LIMIT 5
        """
        
        cursor.execute(query2)
        cards = cursor.fetchall()
        
        if cards:
            logging.info(f"⚠️ EXEMPLOS DE CARTAS COM POSIÇÕES:")
            for card in cards:
                alt_pos = json.loads(card['alt_position_json']) if card['alt_position_json'] else []
                roles = json.loads(card['roles_json']) if card['roles_json'] else []
                logging.info(f"   {card['name']} ({card['overall']}) - Posições: {alt_pos}, Roles: {roles}")
        
    except mysql.connector.Error as e:
        logging.error(f"❌ Erro ao verificar status: {e}")
    finally:
        if connection:
            connection.close()

def main():
    """Função principal"""
    logging.info("🧹 INICIANDO LIMPEZA RÁPIDA DE POSIÇÕES INCORRETAS")
    
    # Mostra status atual
    show_current_status()
    
    # Confirma com o usuário
    print("\n" + "="*50)
    print("⚠️  ATENÇÃO: Este script vai LIMPAR TODAS as posições auxiliares e roles!")
    print("   Isso significa que os campos alt_position_json e roles_json ficarão vazios.")
    print("   O sistema auxiliar vai re-coletar apenas os dados corretos depois.")
    print("="*50)
    
    confirm = input("\n🤔 Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if confirm.upper() != 'SIM':
        logging.info("❌ Operação cancelada pelo usuário")
        return
    
    # Executa a limpeza
    cleaned_count = clean_all_incorrect_positions()
    
    if cleaned_count:
        logging.info(f"🎉 SUCESSO! {cleaned_count} cartas foram limpas")
        logging.info("✅ Agora o sistema auxiliar vai re-coletar apenas os dados corretos")
    else:
        logging.error("❌ Erro na limpeza")

if __name__ == "__main__":
    main() 