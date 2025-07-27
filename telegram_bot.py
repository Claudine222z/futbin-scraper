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
    
    def send_notification(self, message: str) -> bool:
        """Envia notificação simples"""
        return self.send_message(message)
    
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
🚀 <b>FUTBIN SCRAPER INICIADO</b>

📊 <b>OBJETIVO:</b> {total_players:,} cartas
⏱️ <b>DURAÇÃO ESTIMADA:</b> {time_estimate}
🎯 <b>META:</b> TODAS as cartas do site

📋 <b>CONFIGURAÇÃO:</b>
• 786 páginas para coletar
• 200 cartas por seção
• Pausa de 5 min entre seções
• 4.5 segundos por carta

🔄 <b>STATUS:</b> Iniciando coleta...
⚡ <b>VELOCIDADE:</b> Rápida (coleta inicial)
🔧 <b>Qualidade:</b> Correção automática de dados incompletos

📈 <b>Monitoramento:</b> Atualizações a cada 50 cartas
        """
        return self.send_message(message)
    
    def send_progress_notification(self, current: int, total, success_count: int, error_count: int, skipped_count: int, current_player: str, message: str = None) -> bool:
        """Notifica progresso do scraping"""
        if isinstance(total, str) and total == "TODAS":
            # Modo "TODAS as cartas"
            progress_text = f"{current:,} cartas coletadas"
            time_estimate = "Coletando todas as cartas disponíveis"
        else:
            # Modo normal com meta específica
            progress_percent = (current / total) * 100
            remaining = total - current
            progress_text = f"{current:,}/{total:,} ({progress_percent:.1f}%)"
            
            # Calcular tempo estimado (baseado em 4.5 segundos por jogador)
            estimated_seconds = remaining * 4.5
            estimated_minutes = estimated_seconds // 60
            estimated_hours = estimated_minutes // 60
            
            if estimated_hours > 0:
                time_estimate = f"{estimated_hours}h {estimated_minutes % 60}min"
            else:
                time_estimate = f"{estimated_minutes}min"
        
        message = f"""
📊 <b>PROGRESSO ATUAL</b>

🎯 <b>COLETADAS:</b> {progress_text}
✅ <b>SUCESSOS:</b> {success_count:,}
❌ <b>ERROS:</b> {error_count:,}
⏭️ <b>PULADAS:</b> {skipped_count:,}

⏱️ <b>TEMPO RESTANTE:</b> ~{time_estimate}
📍 <b>POSIÇÃO:</b> {current_player}

🔄 <b>STATUS:</b> Coletando ativamente...
        """
        return self.send_message(message)
    
    def send_error_notification(self, error: str, player_url: str) -> bool:
        """Notifica erro no scraping"""
        # Limpar caracteres especiais que podem causar problemas no Telegram
        clean_error = str(error).replace('<', '').replace('>', '').replace('&', 'e')
        clean_url = str(player_url).replace('<', '').replace('>', '').replace('&', 'e')
        
        message = f"""
⚠️ <b>ERRO DETECTADO</b>

❌ <b>PROBLEMA:</b> {clean_error[:100]}...
🔗 <b>URL:</b> {clean_url[:50]}...
⏰ <b>HORA:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

🔄 <b>STATUS:</b> Tentando novamente...
        """
        return self.send_message(message)
    
    def send_completion_notification(self, total_scraped: int, total_errors: int, total_skipped: int, duration_minutes: int, final_count: int = None) -> bool:
        """Notifica conclusão do scraping"""
        total_processed = total_scraped + total_errors + total_skipped
        success_rate = (total_scraped / total_processed * 100) if total_processed > 0 else 0
        
        message = f"""
🎉 <b>COLETA INICIAL CONCLUÍDA!</b>

✅ <b>COLETADAS:</b> {total_scraped:,} cartas
❌ <b>ERROS:</b> {total_errors:,}
⏭️ <b>PULADAS:</b> {total_skipped:,}
📊 <b>TAXA DE SUCESSO:</b> {success_rate:.1f}%
"""
        
        if final_count is not None:
            message += f"🎯 <b>TOTAL NO BANCO:</b> {final_count:,}\n"
            message += f"📋 <b>META:</b> TODAS as cartas do site\n"
        
        message += f"""
⏱️ <b>DURAÇÃO:</b> {duration_minutes} minutos

💾 <b>STATUS:</b> Dados salvos no MySQL
🔄 <b>PRÓXIMO:</b> Iniciando monitoramento contínuo

🚀 <b>SCRAPER FUNCIONANDO PERFEITAMENTE!</b>
        """
        return self.send_message(message)
    
    def send_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Envia resumo diário"""
        message = f"""
📊 <b>RESUMO DIÁRIO</b>

📅 <b>DATA:</b> {datetime.now().strftime('%d/%m/%Y')}
✅ <b>COLETADAS:</b> {stats.get('total_scraped', 0):,} cartas
❌ <b>ERROS:</b> {stats.get('total_errors', 0):,}
⏱️ <b>TEMPO TOTAL:</b> {stats.get('duration_minutes', 0)} min
📈 <b>TAXA DE SUCESSO:</b> {stats.get('success_rate', 0):.1f}%

🎯 <b>STATUS:</b> Sistema funcionando normalmente
        """
        return self.send_message(message)
    
    def send_monitoring_start(self, check_interval_hours: int) -> bool:
        """Notifica início do monitoramento contínuo"""
        message = f"""
🔄 <b>MONITORAMENTO CONTÍNUO INICIADO</b>

⏰ <b>VERIFICAÇÃO:</b> A cada {check_interval_hours} horas
🐌 <b>VELOCIDADE:</b> Modo lento (seguro)
📄 <b>PÁGINAS:</b> 1-10 (onde novas cartas aparecem)

🎯 <b>OBJETIVO:</b> Detectar novas cartas automaticamente
📊 <b>STATUS:</b> Monitorando ativamente...

💡 <b>DICA:</b> O sistema agora opera 24/7!
        """
        return self.send_message(message)
    
    def send_new_card_found(self, player_name: str, overall: int, position: str, club: str, total_in_db: int) -> bool:
        """Notifica quando uma nova carta é encontrada"""
        message = f"""
🆕 <b>NOVA CARTA DETECTADA!</b>

👤 <b>JOGADOR:</b> {player_name}
⭐ <b>OVERALL:</b> {overall}
📍 <b>POSIÇÃO:</b> {position}
🏟️ <b>CLUBE:</b> {club}

📊 <b>TOTAL NO BANCO:</b> {total_in_db:,} cartas

🎉 <b>STATUS:</b> Carta coletada automaticamente!
        """
        return self.send_message(message)
    
    def send_monitoring_cycle_complete(self, new_cards_found: int, total_in_db: int, next_check_hours: int) -> bool:
        """Notifica conclusão de um ciclo de monitoramento"""
        if new_cards_found > 0:
            message = f"""
🎉 <b>CICLO DE VERIFICAÇÃO COMPLETO</b>

🆕 <b>NOVAS CARTAS:</b> {new_cards_found} encontradas
📊 <b>TOTAL NO BANCO:</b> {total_in_db:,} cartas
⏰ <b>PRÓXIMA VERIFICAÇÃO:</b> Em {next_check_hours} horas

✅ <b>STATUS:</b> Sistema funcionando perfeitamente!
            """
        else:
            message = f"""
✅ <b>CICLO DE VERIFICAÇÃO COMPLETO</b>

📊 <b>TOTAL NO BANCO:</b> {total_in_db:,} cartas
🆕 <b>NOVAS CARTAS:</b> Nenhuma encontrada
⏰ <b>PRÓXIMA VERIFICAÇÃO:</b> Em {next_check_hours} horas

🔄 <b>STATUS:</b> Monitoramento ativo - aguardando novas cartas
            """
        return self.send_message(message)
    
    def send_status_notification(self, total_scraped: int, current_position: str, success_count: int, error_count: int) -> bool:
        """Notifica status simples a cada 10 minutos"""
        message = f"""
📊 <b>STATUS ATUAL</b>

🎯 <b>COLETADAS:</b> {total_scraped:,} cartas
📍 <b>POSIÇÃO:</b> {current_position}
✅ <b>SUCESSOS:</b> {success_count:,}
❌ <b>ERROS:</b> {error_count:,}

🔄 <b>STATUS:</b> Funcionando normalmente
        """
        return self.send_message(message)
    
    def send_summary_notification(self, total_scraped: int, total_estimated, success_count: int, error_count: int, skipped_count: int) -> bool:
        """Notifica resumo detalhado a cada 20 minutos"""
        # Calcular porcentagem
        if total_estimated == "TODAS":
            percentage = "∞"
            progress_text = f"{total_scraped:,}"
        else:
            percentage = int((total_scraped / total_estimated) * 100) if total_estimated > 0 else 0
            progress_text = f"{total_scraped:,}/{total_estimated:,}"
        
        message = f"""
📈 <b>RESUMO DETALHADO</b>

🎯 <b>PROGRESSO:</b> {progress_text} ({percentage}%)
✅ <b>SUCESSOS:</b> {success_count:,}
❌ <b>ERROS:</b> {error_count:,}
⏭️ <b>PULADAS:</b> {skipped_count:,}

📊 <b>TAXA DE SUCESSO:</b> {(success_count/(success_count+error_count)*100):.1f}%

🔄 <b>STATUS:</b> Sistema funcionando perfeitamente
        """
        return self.send_message(message)
        return self.send_message(message) 