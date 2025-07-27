#!/usr/bin/env python3
"""
Telegram Bot para Notificações do Scraper
"""

import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        
        # Auto-detect chat_id se não fornecido
        if not self.chat_id:
            self.chat_id = self._get_chat_id()
    
    def _get_chat_id(self) -> str:
        """Obtém o chat_id automaticamente"""
        try:
            # Enviar mensagem de teste para obter chat_id
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                # Pegar o último chat_id
                for update in reversed(data['result']):
                    if 'message' in update:
                        return str(update['message']['chat']['id'])
            
            # Se não conseguir detectar, usar método alternativo
            return self._request_chat_id()
            
        except Exception as e:
            logger.error(f"Erro ao obter chat_id: {e}")
            return self._request_chat_id()
    
    def _request_chat_id(self) -> str:
        """Solicita chat_id manualmente"""
        print("🤖 Para receber notificações, envie uma mensagem para o bot:")
        print(f"https://t.me/your_bot_username")
        print("Depois execute novamente o scraper.")
        return "CHAT_ID_AQUI"  # Placeholder
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Envia mensagem via Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                logger.info("✅ Mensagem enviada via Telegram")
                return True
            else:
                logger.error(f"❌ Erro ao enviar mensagem: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem Telegram: {e}")
            return False
    
    def send_start_notification(self, total_players: int) -> bool:
        """Notifica início do scraping"""
        # Calcular tempo estimado (baseado em 4.5 segundos por jogador)
        estimated_seconds = total_players * 4.5
        estimated_hours = estimated_seconds // 3600
        estimated_minutes = (estimated_seconds % 3600) // 60
        
        time_estimate = ""
        if estimated_hours > 0:
            time_estimate = f"{estimated_hours}h {estimated_minutes}min"
        else:
            time_estimate = f"{estimated_minutes}min"
        
        message = f"""
🚀 <b>SCRAPING COMPLETO INICIADO!</b>

📊 <b>Total estimado:</b> {total_players:,} cartas
🎯 <b>Meta:</b> TODAS as cartas do Futbin
⏱️ <b>Tempo estimado:</b> ~{time_estimate}

📄 <b>Páginas:</b> 786 páginas
🎯 <b>Seções:</b> 200 cartas por seção
⏸️ <b>Pausas:</b> 5 minutos entre seções

🔄 <b>Status:</b> Iniciando coleta completa...
⚡ <b>Velocidade:</b> ~4.5 segundos por carta
🔧 <b>Qualidade:</b> Correção automática de dados incompletos

📈 <b>Monitoramento:</b> Atualizações a cada 50 cartas
        """
        return self.send_message(message)
    
    def send_progress_notification(self, current: int, total, success_count: int, error_count: int, skipped_count: int, current_player: str, message: str = None) -> bool:
        """Notifica progresso do scraping"""
        if isinstance(total, str) and total == "TODAS":
            # Modo "TODAS as cartas"
            progress_text = f"{current} jogadores coletados"
            time_estimate = "Coletando todas as cartas disponíveis"
        else:
            # Modo normal com meta específica
            progress_percent = (current / total) * 100
            remaining = total - current
            progress_text = f"{current:,}/{total:,} ({progress_percent:.1f}%)"
            
            # Calcular tempo estimado (baseado em 3 segundos por jogador)
            estimated_seconds = remaining * 3
            estimated_minutes = estimated_seconds // 60
            estimated_hours = estimated_minutes // 60
            
            if estimated_hours > 0:
                time_estimate = f"{estimated_hours}h {estimated_minutes % 60}min"
            else:
                time_estimate = f"{estimated_minutes}min"
        
        message = f"""
📈 <b>PROGRESSO ATUALIZADO</b>

🎯 <b>Progresso:</b> {progress_text}
✅ <b>Sucessos:</b> {success_count:,}
❌ <b>Erros:</b> {error_count:,}
⏭️ <b>Pulados:</b> {skipped_count:,}
⏱️ <b>Tempo restante:</b> ~{time_estimate}

👤 <b>Jogador atual:</b> {current_player}

🔄 <b>Status:</b> Coletando dados...
        """
        return self.send_message(message)
    
    def send_error_notification(self, error: str, player_url: str) -> bool:
        """Notifica erro no scraping"""
        # Limpar caracteres especiais que podem causar problemas no Telegram
        clean_error = str(error).replace('<', '').replace('>', '').replace('&', 'e')
        clean_url = str(player_url).replace('<', '').replace('>', '').replace('&', 'e')
        
        message = f"""
⚠️ <b>ERRO DETECTADO</b>

❌ <b>Erro:</b> {clean_error[:100]}...
🔗 <b>URL:</b> {clean_url[:50]}...
⏰ <b>Hora:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

🔄 <b>Status:</b> Tentando novamente...
        """
        return self.send_message(message)
    
    def send_completion_notification(self, total_scraped: int, total_errors: int, total_skipped: int, duration_minutes: int, final_count: int = None) -> bool:
        """Notifica conclusão do scraping"""
        total_processed = total_scraped + total_errors + total_skipped
        success_rate = (total_scraped / total_processed * 100) if total_processed > 0 else 0
        
        message = f"""
🎉 <b>SCRAPING CONCLUÍDO!</b>

✅ <b>Jogadores coletados:</b> {total_scraped:,}
❌ <b>Erros:</b> {total_errors:,}
⏭️ <b>Pulados (já existiam):</b> {total_skipped:,}
📊 <b>Taxa de sucesso:</b> {success_rate:.1f}%
"""
        
        if final_count is not None:
            message += f"🎯 <b>Total no Banco:</b> {final_count}\n"
            message += f"📋 <b>Meta:</b> TODAS as cartas disponíveis\n"
        
        message += f"""
⏱️ <b>Duração:</b> {duration_minutes} minutos

💾 <b>Status:</b> Dados salvos no MySQL
🎯 <b>Próximo passo:</b> Verificar banco de dados

🚀 <b>Scraper finalizado com sucesso!</b>
        """
        return self.send_message(message)
    
    def send_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Envia resumo diário"""
        message = f"""
📊 <b>RESUMO DIÁRIO</b>

📅 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}
✅ <b>Jogadores coletados:</b> {stats.get('total_scraped', 0):,}
❌ <b>Erros:</b> {stats.get('total_errors', 0):,}
⏱️ <b>Tempo total:</b> {stats.get('duration_minutes', 0)} min
📈 <b>Taxa de sucesso:</b> {stats.get('success_rate', 0):.1f}%

🎯 <b>Status:</b> Sistema funcionando normalmente
        """
        return self.send_message(message) 