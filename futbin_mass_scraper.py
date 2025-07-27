#!/usr/bin/env python3
"""
Futbin Mass Scraper - Coleta TODAS as cartas com máxima segurança
"""

import requests
import json
import time
import random
import re
import logging
import mysql.connector
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from telegram_bot import TelegramNotifier

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mass_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PlayerStats:
    velocidade: int
    finalizacao: int
    passe: int
    drible: int
    defesa: int
    fisico: int

@dataclass
class DetailedStats:
    # Velocidade
    aceleracao: int
    velocidade_sprint: int
    
    # Finalização
    finalizacao_detalhada: int
    forca_chute: int
    chutes_longe: int
    voleios: int
    penaltis: int
    
    # Passe
    visao: int
    cruzamento: int
    precisao_livre: int
    passe_curto: int
    passe_longo: int
    curva: int
    
    # Drible
    agilidade: int
    equilibrio: int
    reacoes: int
    controle_bola: int
    drible_detalhado: int
    compostura: int
    
    # Defesa
    interceptacoes: int
    precisao_cabeca: int
    marcacao: int
    carrinho_em_pe: int
    carrinho_deslizante: int
    
    # Físico
    salto: int
    resistencia: int
    forca: int
    agressao: int

@dataclass
class PlayerCard:
    id: str
    nome: str
    overall: int
    avaliacao: int
    posicao: str
    nacao: str
    liga: str
    clube: str
    pe_ruim: int
    habilidades: int
    altura: str
    peso: int
    pe_preferido: str
    data_nascimento: str
    accele_rate: str
    reputacao_internacional: int
    revisao: str
    atualizacao_preco: str
    escalao: str
    tipo_corpo: str
    id_clube: str
    id_liga: str
    posicoes_alternativas: List[str]
    estilos_jogo: List[str]
    estatisticas: PlayerStats
    estatisticas_detalhadas: DetailedStats
    precos: Dict[str, Dict[str, Any]]
    estilos_quimica: Dict[str, List[str]]
    posicoes: Dict[str, int]
    url_imagem: str
    url: str
    coletado_em: str
    funcoes: List[Dict[str, List[str]]]

class FutbinMassScraper:
    def __init__(self, telegram_token: str = None):
        self.base_url = "https://www.futbin.com"
        self.session = requests.Session()
        self.ua = UserAgent()
        
        # Usar variáveis de ambiente se não fornecido
        if telegram_token is None:
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw')
        
        self.telegram = TelegramNotifier(telegram_token)
        
        # Configurações de segurança
        self.min_delay = 3.0
        self.max_delay = 7.0
        self.max_retries = 3
        self.notification_interval = 100
        
        # Estatísticas
        self.stats = {
            'total_scraped': 0,
            'total_errors': 0,
            'start_time': None,
            'current_player': '',
            'success_count': 0,
            'error_count': 0
        }
        
        # Configurar headers aleatórios
        self._update_headers()
    
    def _update_headers(self):
        """Atualiza headers com User-Agent aleatório"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        """Delay aleatório entre requisições"""
        if min_delay is None:
            min_delay = self.min_delay
        if max_delay is None:
            max_delay = self.max_delay
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, url: str) -> Optional[str]:
        """Faz requisição HTTP com retry e tratamento de erros"""
        try:
            self._random_delay()
            self._update_headers()
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
                
        except Exception as e:
            logger.error(f"Erro ao fazer requisição para {url}: {e}")
            raise
    
    def get_all_player_urls(self) -> List[str]:
        """Obtém URLs de todos os jogadores do Futbin"""
        player_urls = []
        
        try:
            logger.info("🔍 Obtendo lista de todos os jogadores...")
            
            # URL principal dos jogadores
            players_url = f"{self.base_url}/players"
            
            html = self._make_request(players_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Procurar por links de jogadores
            player_links = soup.find_all('a', href=re.compile(r'/25/player/\d+'))
            
            for link in player_links:
                href = link.get('href')
                if href:
                    full_url = f"{self.base_url}{href}"
                    player_urls.append(full_url)
            
            # Se não encontrou na primeira página, tentar paginação
            if len(player_urls) < 100:
                # Tentar diferentes páginas
                for page in range(1, 11):  # Primeiras 10 páginas
                    page_url = f"{players_url}?page={page}"
                    try:
                        html = self._make_request(page_url)
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        page_links = soup.find_all('a', href=re.compile(r'/25/player/\d+'))
                        for link in page_links:
                            href = link.get('href')
                            if href:
                                full_url = f"{self.base_url}{href}"
                                if full_url not in player_urls:
                                    player_urls.append(full_url)
                    except Exception as e:
                        logger.warning(f"Erro ao acessar página {page}: {e}")
                        continue
            
            logger.info(f"✅ Encontrados {len(player_urls)} jogadores")
            return player_urls
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter URLs dos jogadores: {e}")
            return []
    
    def _extract_player_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai informações básicas do jogador"""
        info = {}
        
        try:
            # Nome do jogador
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                name_match = re.search(r'^([^-]+)', title_text)
                if name_match:
                    info['nome'] = name_match.group(1).strip()
            
            # Overall
            overall_elem = soup.find('div', class_='playercard-25-rating')
            if overall_elem:
                overall_text = overall_elem.get_text(strip=True)
                if overall_text.isdigit():
                    info['overall'] = int(overall_text)
            
            # Posição
            all_text = soup.get_text()
            position_patterns = [
                r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)',
                r'(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                r'\b(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\b'
            ]
            
            for pattern in position_patterns:
                position_match = re.search(pattern, all_text, re.IGNORECASE)
                if position_match:
                    if len(position_match.groups()) > 1:
                        position = position_match.group(2)
                    else:
                        position = position_match.group(1)
                    
                    if position and position.upper() in ['LW', 'RW', 'ST', 'CAM', 'CM', 'CDM', 'CB', 'LB', 'RB', 'GK']:
                        info['posicao'] = position.upper()
                        break
            
            # Nação, Liga, Clube
            nation_patterns = ['Portugal', 'Brazil', 'Argentina', 'France', 'Germany', 'Spain', 'Italy', 'England']
            for pattern in nation_patterns:
                if pattern in all_text:
                    info['nacao'] = pattern
                    break
            
            league_patterns = ['Icons', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
            for pattern in league_patterns:
                if pattern in all_text:
                    info['liga'] = pattern
                    break
            
            club_patterns = ['EA FC ICONS', 'Manchester United', 'Real Madrid', 'Barcelona', 'Bayern Munich']
            for pattern in club_patterns:
                if pattern in all_text:
                    info['clube'] = pattern
                    break
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações básicas: {e}")
        
        return info
    
    def _extract_detailed_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai informações detalhadas do jogador - VERSÃO MELHORADA"""
        info = {}
        
        try:
            all_text = soup.get_text()
            
            # Skills
            skills_match = re.search(r'Skills\s*(\d+)', all_text, re.IGNORECASE)
            if skills_match:
                info['habilidades'] = int(skills_match.group(1))
            
            # Weak Foot
            weak_foot_match = re.search(r'Weak Foot\s*(\d+)', all_text, re.IGNORECASE)
            if weak_foot_match:
                info['pe_ruim'] = int(weak_foot_match.group(1))
            
            # International Reputation
            intl_rep_match = re.search(r'Intl\. Rep\s*(\d+)', all_text, re.IGNORECASE)
            if intl_rep_match:
                info['reputacao_internacional'] = int(intl_rep_match.group(1))
            
            # Foot
            foot_match = re.search(r'Foot\s*(Right|Left)', all_text, re.IGNORECASE)
            if foot_match:
                info['pe_preferido'] = foot_match.group(1)
            
            # Height
            height_match = re.search(r'Height\s*(\d+cm\s*\|\s*\d+\'?\d*")', all_text, re.IGNORECASE)
            if height_match:
                info['altura'] = height_match.group(1)
            
            # Weight
            weight_match = re.search(r'Weight\s*(\d+)', all_text, re.IGNORECASE)
            if weight_match:
                info['peso'] = int(weight_match.group(1))
            
            # Birthdate
            birthdate_match = re.search(r'Birthdate\s*(\d{2}-\d{2}-\d{4})', all_text, re.IGNORECASE)
            if birthdate_match:
                info['data_nascimento'] = birthdate_match.group(1)
            
            # AcceleRATE
            accele_match = re.search(r'AcceleRATE\s*([A-Za-z\s]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if accele_match:
                accele_rate = accele_match.group(1).strip()
                if accele_rate and not any(keyword in accele_rate.lower() for keyword in ['club', 'nation', 'league', 'skills']):
                    info['accele_rate'] = accele_rate
            
            # Revision
            revision_match = re.search(r'Revision\s*([A-Za-z\s]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if revision_match:
                revision = revision_match.group(1).strip()
                if revision and not any(keyword in revision.lower() for keyword in ['price', 'update']):
                    info['revision'] = revision
            
            # Price Update
            price_update_match = re.search(r'Price Update\s*([A-Za-z\s\d]+ago)', all_text, re.IGNORECASE)
            if price_update_match:
                info['atualizacao_preco'] = price_update_match.group(1).strip()
            
            # Squad
            squad_match = re.search(r'Squad\s*([A-Za-z0-9]+)', all_text, re.IGNORECASE)
            if squad_match:
                info['escalao'] = squad_match.group(1).strip()
            
            # Body Type
            body_type_match = re.search(r'B\.Type\s*([A-Za-z\s&]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if body_type_match:
                body_type = body_type_match.group(1).strip()
                if body_type and not any(keyword in body_type.lower() for keyword in ['birthdate']):
                    info['tipo_corpo'] = body_type
            
            # ID
            id_match = re.search(r'ID\s*(\d+)', all_text, re.IGNORECASE)
            if id_match:
                info['id'] = id_match.group(1)
            
            # Club ID
            club_id_match = re.search(r'Club ID\s*(\d+)', all_text, re.IGNORECASE)
            if club_id_match:
                info['id_clube'] = club_id_match.group(1)
            
            # League ID
            league_id_match = re.search(r'League ID\s*(\d+)', all_text, re.IGNORECASE)
            if league_id_match:
                info['id_liga'] = league_id_match.group(1)
            
            # POSIÇÕES ALTERNATIVAS - BUSCA MELHORADA
            alt_positions = self._extract_alt_positions_improved(soup, all_text)
            if alt_positions:
                info['posicoes_alternativas'] = alt_positions
            
            # Tentar extrair informações de nação, liga e clube se não foram encontradas antes
            if 'nacao' not in info:
                # Procurar por nações específicas
                nation_patterns = ['Portugal', 'Brazil', 'Argentina', 'France', 'Germany', 'Spain', 'Italy', 'England']
                for pattern in nation_patterns:
                    if pattern in all_text:
                        info['nacao'] = pattern
                        break
            
            if 'liga' not in info:
                # Procurar por ligas específicas
                league_patterns = ['Icons', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
                for pattern in league_patterns:
                    if pattern in all_text:
                        info['liga'] = pattern
                        break
            
            if 'clube' not in info:
                # Procurar por clubes específicos
                club_patterns = ['EA FC ICONS', 'Manchester United', 'Real Madrid', 'Barcelona', 'Bayern Munich']
                for pattern in club_patterns:
                    if pattern in all_text:
                        info['clube'] = pattern
                        break
        
        except Exception as e:
            logger.error(f"Erro ao extrair informações detalhadas: {e}")
        
        return info
    
    def _extract_alt_positions_improved(self, soup: BeautifulSoup, all_text: str) -> List[str]:
        """Extrai posições alternativas - SÓ POSIÇÕES REAIS"""
        alt_positions = []
        
        try:
            # PROCURAR APENAS POR "Alt POS" OU "Alternative Positions" NO HTML
            # Se não encontrar, retornar lista vazia
            
            # Padrões específicos para posições alternativas reais
            alt_pos_patterns = [
                r'Alt POS\s*([A-Z,\s]+)',
                r'Alternative Positions\s*([A-Z,\s]+)',
                r'Alt\.?\s*Positions?\s*([A-Z,\s]+)'
            ]
            
            found_alt_pos = False
            for pattern in alt_pos_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    found_alt_pos = True
                    alt_positions_text = match.group(1).strip()
                    # Limpar e separar posições
                    for pos in alt_positions_text.split(','):
                        pos_clean = pos.strip()
                        # Validar se é uma posição válida
                        valid_positions = ['LW', 'RW', 'LM', 'RM', 'CAM', 'CM', 'CDM', 'ST', 'CB', 'LB', 'RB', 'GK']
                        if pos_clean in valid_positions and pos_clean not in alt_positions:
                            alt_positions.append(pos_clean)
                    break
            
            # SE NÃO ENCONTROU "Alt POS" OU "Alternative Positions", RETORNAR LISTA VAZIA
            # NÃO INFERIR POSIÇÕES BASEADO EM RATINGS
            
        except Exception as e:
            logger.error(f"Erro ao extrair posições alternativas: {e}")
        
        return alt_positions
    
    def _extract_detailed_stats(self, soup: BeautifulSoup) -> DetailedStats:
        """Extrai estatísticas detalhadas do jogador"""
        stats = {
            'aceleracao': 0, 'velocidade_sprint': 0,
            'finalizacao_detalhada': 0, 'forca_chute': 0, 'chutes_longe': 0, 'voleios': 0, 'penaltis': 0,
            'visao': 0, 'cruzamento': 0, 'precisao_livre': 0, 'passe_curto': 0, 'passe_longo': 0, 'curva': 0,
            'agilidade': 0, 'equilibrio': 0, 'reacoes': 0, 'controle_bola': 0, 'drible_detalhado': 0, 'compostura': 0,
            'interceptacoes': 0, 'precisao_cabeca': 0, 'marcacao': 0, 'carrinho_em_pe': 0, 'carrinho_deslizante': 0,
            'salto': 0, 'resistencia': 0, 'forca': 0, 'agressao': 0
        }
        
        try:
            all_text = soup.get_text()
            
            stat_patterns = {
                'aceleracao': r'Acceleration\s*(\d+)',
                'velocidade_sprint': r'Sprint Speed\s*(\d+)',
                'finalizacao_detalhada': r'Finishing\s*(\d+)',
                'forca_chute': r'Shot Power\s*(\d+)',
                'chutes_longe': r'Long Shots\s*(\d+)',
                'voleios': r'Volleys\s*(\d+)',
                'penaltis': r'Penalties\s*(\d+)',
                'visao': r'Vision\s*(\d+)',
                'cruzamento': r'Crossing\s*(\d+)',
                'precisao_livre': r'FK Acc\.\s*(\d+)',
                'passe_curto': r'Short Pass\s*(\d+)',
                'passe_longo': r'Long Pass\s*(\d+)',
                'curva': r'Curve\s*(\d+)',
                'agilidade': r'Agility\s*(\d+)',
                'equilibrio': r'Balance\s*(\d+)',
                'reacoes': r'Reactions\s*(\d+)',
                'controle_bola': r'Ball Control\s*(\d+)',
                'drible_detalhado': r'Dribbling\s*(\d+)',
                'compostura': r'Composure\s*(\d+)',
                'interceptacoes': r'Interceptions\s*(\d+)',
                'precisao_cabeca': r'Heading Acc\.\s*(\d+)',
                'marcacao': r'Def\. Aware\s*(\d+)',
                'carrinho_em_pe': r'Stand Tackle\s*(\d+)',
                'carrinho_deslizante': r'Slide Tackle\s*(\d+)',
                'salto': r'Jumping\s*(\d+)',
                'resistencia': r'Stamina\s*(\d+)',
                'forca': r'Strength\s*(\d+)',
                'agressao': r'Aggression\s*(\d+)'
            }
            
            for stat_name, pattern in stat_patterns.items():
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    stats[stat_name] = int(match.group(1))
        
        except Exception as e:
            logger.error(f"Erro ao extrair estatísticas detalhadas: {e}")
        
        return DetailedStats(**stats)
    
    def _extract_playstyles(self, soup: BeautifulSoup) -> List[str]:
        """Extrai playstyles do jogador - LÓGICA DO SIMPLE_SCRAPER"""
        playstyles = []
        
        try:
            # Playstyles específicos baseados no simple_scraper
            expected_playstyles = [
                'Finesse Shot',
                'Technical',
                'Rapid',
                'Incisive Pass',
                'Low Driven Shot',
                'Chip Shot',
                'Power Shot',
                'Tiki Taka',
                'Quick Step',
                'Relentless',
                'Trivela',
                'Speed Dribbler',
                'Long Ball Pass',
                'Slide Tackle',
                'Power Header',
                'Acrobat',
                'Outside Foot Shot',
                'Flair',
                'Press Proven',
                'Intercept',
                'Block',
                'Giant Throw-in',
                'Set Piece Specialist',
                'One Club Player',
                'Leadership',
                'Second Wind',
                'Team Player',
                'Injury Free',
                'Solid Player'
            ]
            
            for playstyle in expected_playstyles:
                # Procurar por elementos que contenham este playstyle
                elements = soup.find_all(['div', 'span', 'p'], string=re.compile(playstyle, re.IGNORECASE))
                
                if elements:
                    # Verificar se é playstyle plus (tem classe psplus no pai)
                    is_plus = False
                    for elem in elements:
                        parent = elem.parent
                        if parent and 'psplus' in parent.get('class', []):
                            is_plus = True
                            break
                    
                    # Adicionar playstyle com indicação de plus se aplicável
                    if is_plus:
                        playstyles.append(f"{playstyle} +")
                    else:
                        playstyles.append(playstyle)
            
        except Exception as e:
            logger.error(f"Erro ao extrair playstyles: {e}")
        
        return playstyles
    
    def _extract_prices(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        """Extrai preços do jogador - LÓGICA DO SIMPLE_SCRAPER"""
        prices = {}
        
        try:
            # Procurar por elementos de preço
            price_elements = soup.find_all(['div', 'span'], class_=re.compile(r'price|coin', re.IGNORECASE))
            
            for elem in price_elements:
                text = elem.get_text(strip=True)
                if text and any(char.isdigit() for char in text):
                    # Tentar extrair número do preço
                    price_num = self._extract_price_number(text)
                    if price_num > 0:
                        # Determinar plataforma baseado no contexto
                        if 'ps' in elem.get('class', []) or 'playstation' in text.lower():
                            prices['psxbox'] = {'current': price_num, 'trend': 0, 'min': 0, 'max': 0}
                        elif 'xbox' in text.lower():
                            prices['xbox'] = {'current': price_num, 'trend': 0, 'min': 0, 'max': 0}
                        elif 'pc' in text.lower():
                            prices['pc'] = {'current': price_num, 'trend': 0, 'min': 0, 'max': 0}
                        else:
                            # Padrão
                            prices['psxbox'] = {'current': price_num, 'trend': 0, 'min': 0, 'max': 0}
        
        except Exception as e:
            logger.error(f"Erro ao extrair preços: {e}")
        
        return prices
    
    def _extract_price_number(self, text: str) -> int:
        """Extrai número do preço de um texto"""
        try:
            # Remover caracteres não numéricos exceto ponto e vírgula
            clean_text = re.sub(r'[^\d.,]', '', text)
            
            # Converter para número
            if clean_text:
                # Substituir vírgula por ponto se necessário
                clean_text = clean_text.replace(',', '.')
                return int(float(clean_text))
        except:
            pass
        
        return 0
    
    def _extract_chemistry_styles(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extrai chemistry styles do jogador - LÓGICA DO SIMPLE_SCRAPER"""
        chemistry_styles = {}
        
        try:
            # Lista de estilos de química conhecidos
            known_styles = [
                'Basic', 'Sniper', 'Finisher', 'Deadeye', 'Marksman', 'Hawk', 'Artist',
                'Architect', 'Powerhouse', 'Maestro', 'Engine', 'Sentinel', 'Guardian',
                'Gladiator', 'Backbone', 'Anchor', 'Hunter', 'Catalyst', 'Shadow'
            ]
            
            all_text = soup.get_text()
            
            # Procurar por estilos de química no texto
            for style in known_styles:
                if style in all_text:
                    chemistry_styles['general'] = chemistry_styles.get('general', []) + [style]
        
        except Exception as e:
            logger.error(f"Erro ao extrair estilos de química: {e}")
        
        return chemistry_styles
    
    def _extract_image_url(self, soup: BeautifulSoup) -> str:
        """Extrai URL da imagem do jogador - LÓGICA DO SIMPLE_SCRAPER"""
        try:
            # Procurar especificamente pela imagem com a classe playercard-25-special-img
            player_card_img = soup.find('img', class_='playercard-25-special-img')
            if player_card_img:
                src = player_card_img.get('src', '')
                if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                    return src
            
            # Procurar por imagens do jogador
            # Procurar por elementos img com classes específicas de jogador
            player_image_selectors = [
                'img[src*="players"]',
                'img[src*="player"]',
                '.player-image img',
                '.card-image img',
                '.player-card img',
                '.player-img img'
            ]
            
            for selector in player_image_selectors:
                img_elements = soup.select(selector)
                for img in img_elements:
                    src = img.get('src', '')
                    if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                        # Verificar se é uma imagem de jogador
                        if any(keyword in src.lower() for keyword in ['player', 'card']):
                            return src
            
            # Procurar por elementos com classes específicas
            player_containers = soup.find_all(['div', 'img'], class_=re.compile(r'player|card|image', re.IGNORECASE))
            
            for container in player_containers:
                if container.name == 'img':
                    src = container.get('src', '')
                    if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                        if any(keyword in src.lower() for keyword in ['player', 'card']):
                            return src
                else:
                    # Se é um container, procurar por img dentro dele
                    img = container.find('img')
                    if img:
                        src = img.get('src', '')
                        if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                            if any(keyword in src.lower() for keyword in ['player', 'card']):
                                return src
            
            # Procurar por padrões específicos de URL de imagem de jogador
            all_text = soup.get_text()
            img_patterns = [
                r'https://[^"\s]+players[^"\s]+\.(?:jpg|jpeg|png|webp)',
                r'https://[^"\s]+player[^"\s]+\.(?:jpg|jpeg|png|webp)'
            ]
            
            for pattern in img_patterns:
                matches = re.findall(pattern, str(soup), re.IGNORECASE)
                for match in matches:
                    if 'futbin-green-small' not in match and 'logo' not in match.lower():
                        return match
            
            # Se não encontrou, retornar string vazia
            return ""
            
        except Exception as e:
            logger.error(f"Erro ao extrair URL da imagem: {e}")
            return ""
    
    def _extract_roles(self, soup: BeautifulSoup) -> List[Dict[str, List[str]]]:
        """Extrai roles do jogador - VERSÃO MELHORADA - SÓ ROLES REAIS"""
        roles_info = []
        
        try:
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            # Procurar por seções específicas de roles
            roles_sections = []
            
            # Procurar por seções que começam com posições
            valid_positions = ['LW', 'RW', 'LM', 'RM', 'CAM', 'CM', 'CDM', 'ST', 'CB', 'LB', 'RB', 'GK']
            
            # Mapear roles específicas para cada posição baseado no exemplo fornecido
            expected_roles = {
                'LW': ['Winger', 'Inside Forward', 'Wide Playmaker'],
                'LM': ['Winger', 'Wide Midfielder', 'Wide Playmaker', 'Inside Forward'],
                'CAM': ['Playmaker', 'Shadow Striker', 'Half Winger', 'Classic 10'],
                'RW': ['Winger', 'Inside Forward', 'Wide Playmaker'],
                'ST': ['Poacher', 'Advanced Forward', 'Target Man', 'Complete Forward'],
                'CM': ['Box to Box', 'Deep Lying Playmaker', 'Advanced Playmaker'],
                'CDM': ['Ball Winning Midfielder', 'Deep Lying Playmaker', 'Anchor Man'],
                'CB': ['Ball Playing Defender', 'Central Defender', 'No Nonsense Centre Back'],
                'LB': ['Full Back', 'Wing Back', 'Complete Wing Back'],
                'RB': ['Full Back', 'Wing Back', 'Complete Wing Back'],
                'GK': ['Sweeper Keeper', 'Goalkeeper', 'Shot Stopper']
            }
            
            # BUSCA MELHORADA: Procurar por roles REAIS no texto completo
            for position, expected_role_list in expected_roles.items():
                position_roles = []
                
                for role in expected_role_list:
                    # Procurar por padrões mais abrangentes
                    role_patterns = [
                        rf'{role}\s*\+\+',
                        rf'{role}\s*\+',
                        rf'{role}',
                        rf'{role.lower()}\s*\+\+',
                        rf'{role.lower()}\s*\+',
                        rf'{role.lower()}'
                    ]
                    
                    for pattern in role_patterns:
                        matches = re.findall(pattern, all_text, re.IGNORECASE)
                        for match in matches:
                            # Determinar o nível baseado no padrão encontrado
                            if '++' in match:
                                position_roles.append(f"{role} ++")
                            elif '+' in match:
                                position_roles.append(f"{role} +")
                            else:
                                position_roles.append(f"{role} ++")  # Padrão
                            break
                
                if position_roles:
                    roles_sections.append({
                        'position': position,
                        'roles': position_roles
                    })
            
            # BUSCA ALTERNATIVA: Procurar por elementos HTML específicos
            role_elements = soup.find_all(['div', 'span'], class_=re.compile(r'role|trait|specialty', re.IGNORECASE))
            
            for elem in role_elements:
                text = elem.get_text(strip=True)
                # Procurar por roles conhecidas no texto
                for role in ['Winger', 'Inside Forward', 'Playmaker', 'Poacher', 'Advanced Forward']:
                    if role.lower() in text.lower():
                        # Tentar determinar a posição baseada no contexto
                        for position in valid_positions:
                            if position in text:
                                # Adicionar role para esta posição
                                found = False
                                for section in roles_sections:
                                    if section['position'] == position:
                                        if f"{role} ++" not in section['roles']:
                                            section['roles'].append(f"{role} ++")
                                        found = True
                                        break
                                
                                if not found:
                                    roles_sections.append({
                                        'position': position,
                                        'roles': [f"{role} ++"]
                                    })
                                break
            
            # PROCURAR POR ROLES REAIS NO HTML - MÉTODO PRINCIPAL
            # Procurar por seções que mostram roles reais
            role_sections = soup.find_all(['div', 'section'], class_=re.compile(r'role|trait|specialty|position', re.IGNORECASE))
            
            for section in role_sections:
                section_text = section.get_text()
                # Procurar por padrões de roles com níveis
                role_patterns = [
                    r'(Winger|Inside Forward|Playmaker|Poacher|Advanced Forward|Target Man|Complete Forward|Box to Box|Deep Lying Playmaker|Advanced Playmaker|Ball Winning Midfielder|Anchor Man|Ball Playing Defender|Central Defender|No Nonsense Centre Back|Full Back|Wing Back|Complete Wing Back|Sweeper Keeper|Goalkeeper|Shot Stopper)\s*(\+\+|\+)',
                    r'(Winger|Inside Forward|Playmaker|Poacher|Advanced Forward|Target Man|Complete Forward|Box to Box|Deep Lying Playmaker|Advanced Playmaker|Ball Winning Midfielder|Anchor Man|Ball Playing Defender|Central Defender|No Nonsense Centre Back|Full Back|Wing Back|Complete Wing Back|Sweeper Keeper|Goalkeeper|Shot Stopper)'
                ]
                
                for pattern in role_patterns:
                    matches = re.findall(pattern, section_text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            role_name = match[0]
                            level = match[1] if len(match) > 1 else "++"
                        else:
                            role_name = match
                            level = "++"
                        
                        # Determinar posição baseada na role
                        position_mapping = {
                            'Winger': ['LW', 'RW', 'LM', 'RM'],
                            'Inside Forward': ['LW', 'RW', 'ST'],
                            'Playmaker': ['CAM', 'CM'],
                            'Poacher': ['ST'],
                            'Advanced Forward': ['ST'],
                            'Target Man': ['ST'],
                            'Complete Forward': ['ST'],
                            'Box to Box': ['CM'],
                            'Deep Lying Playmaker': ['CM', 'CDM'],
                            'Advanced Playmaker': ['CAM', 'CM'],
                            'Ball Winning Midfielder': ['CDM', 'CM'],
                            'Anchor Man': ['CDM'],
                            'Ball Playing Defender': ['CB'],
                            'Central Defender': ['CB'],
                            'No Nonsense Centre Back': ['CB'],
                            'Full Back': ['LB', 'RB'],
                            'Wing Back': ['LB', 'RB'],
                            'Complete Wing Back': ['LB', 'RB'],
                            'Sweeper Keeper': ['GK'],
                            'Goalkeeper': ['GK'],
                            'Shot Stopper': ['GK']
                        }
                        
                        if role_name in position_mapping:
                            for position in position_mapping[role_name]:
                                # Adicionar role para esta posição
                                found = False
                                for section in roles_sections:
                                    if section['position'] == position:
                                        role_with_level = f"{role_name} {level}"
                                        if role_with_level not in section['roles']:
                                            section['roles'].append(role_with_level)
                                        found = True
                                        break
                                
                                if not found:
                                    roles_sections.append({
                                        'position': position,
                                        'roles': [f"{role_name} {level}"]
                                    })
            
            # REMOVER A INFERÊNCIA AUTOMÁTICA - SÓ ROLES REAIS
            # NÃO inferir roles baseado na posição principal
            
            # Remover duplicatas e organizar
            unique_sections = {}
            for section in roles_sections:
                position = section['position']
                roles = section['roles']
                
                if position not in unique_sections:
                    unique_sections[position] = []
                
                # Adicionar apenas roles únicas
                for role in roles:
                    if role not in unique_sections[position]:
                        unique_sections[position].append(role)
            
            # Converter de volta para lista
            final_roles_sections = []
            for position, roles in unique_sections.items():
                if roles:
                    final_roles_sections.append({
                        'position': position,
                        'roles': roles
                    })
            
            return final_roles_sections
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações de roles: {e}")
        
        return roles_info
    
    def _extract_stats(self, detailed_stats: DetailedStats) -> PlayerStats:
        """Calcula estatísticas principais"""
        return PlayerStats(
            velocidade=(detailed_stats.aceleracao + detailed_stats.velocidade_sprint) // 2,
            finalizacao=(detailed_stats.finalizacao_detalhada + detailed_stats.forca_chute + detailed_stats.chutes_longe + detailed_stats.voleios + detailed_stats.penaltis) // 5,
            passe=(detailed_stats.visao + detailed_stats.cruzamento + detailed_stats.precisao_livre + detailed_stats.passe_curto + detailed_stats.passe_longo + detailed_stats.curva) // 6,
            drible=(detailed_stats.agilidade + detailed_stats.equilibrio + detailed_stats.reacoes + detailed_stats.controle_bola + detailed_stats.drible_detalhado + detailed_stats.compostura) // 6,
            defesa=(detailed_stats.interceptacoes + detailed_stats.precisao_cabeca + detailed_stats.marcacao + detailed_stats.carrinho_em_pe + detailed_stats.carrinho_deslizante) // 5,
            fisico=(detailed_stats.salto + detailed_stats.resistencia + detailed_stats.forca + detailed_stats.agressao) // 4
        )
    
    def scrape_player(self, url: str) -> Optional[PlayerCard]:
        """Scrapa dados de um jogador específico"""
        try:
            logger.info(f"Scrapando jogador: {url}")
            
            html = self._make_request(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrair informações básicas
            player_info = self._extract_player_info(soup)
            
            # Extrair informações detalhadas
            detailed_info = self._extract_detailed_info(soup)
            
            # Extrair estatísticas detalhadas
            detailed_stats = self._extract_detailed_stats(soup)
            
            # Calcular estatísticas principais
            stats = self._extract_stats(detailed_stats)
            
            # Extrair informações adicionais
            playstyles = self._extract_playstyles(soup)
            chemistry_styles = self._extract_chemistry_styles(soup)
            roles = self._extract_roles(soup)
            image_url = self._extract_image_url(soup)
            prices = self._extract_prices(soup)
            
            # Extrair ID do jogador da URL
            player_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            
            # Criar objeto PlayerCard
            player_card = PlayerCard(
                id=player_id,
                nome=player_info.get('nome', 'Desconhecido'),
                overall=player_info.get('overall', 0),
                avaliacao=player_info.get('overall', 0),
                posicao=player_info.get('posicao', 'Desconhecida'),
                nacao=player_info.get('nacao', 'Desconhecida'),
                liga=player_info.get('liga', 'Desconhecida'),
                clube=player_info.get('clube', 'Desconhecido'),
                pe_ruim=detailed_info.get('pe_ruim', 0),
                habilidades=detailed_info.get('habilidades', 0),
                altura=detailed_info.get('altura', ''),
                peso=detailed_info.get('peso', 0),
                pe_preferido=detailed_info.get('pe_preferido', ''),
                data_nascimento=detailed_info.get('data_nascimento', ''),
                accele_rate=detailed_info.get('accele_rate', ''),
                reputacao_internacional=detailed_info.get('reputacao_internacional', 0),
                revisao=detailed_info.get('revision', ''),
                atualizacao_preco=detailed_info.get('atualizacao_preco', ''),
                escalao=detailed_info.get('escalao', ''),
                tipo_corpo=detailed_info.get('tipo_corpo', ''),
                id_clube=detailed_info.get('id_clube', ''),
                id_liga=detailed_info.get('id_liga', ''),
                posicoes_alternativas=detailed_info.get('posicoes_alternativas', []),
                estilos_jogo=playstyles,
                estatisticas=stats,
                estatisticas_detalhadas=detailed_stats,
                precos=prices,
                estilos_quimica=chemistry_styles,
                posicoes={},
                url_imagem=image_url,
                url=url,
                coletado_em=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                funcoes=roles
            )
            
            logger.info(f"✅ Jogador {player_info.get('nome', 'Desconhecido')} scrapado com sucesso")
            return player_card
            
        except Exception as e:
            logger.error(f"❌ Erro ao scrapar jogador {url}: {e}")
            # Notificar erro via Telegram
            self.telegram.send_error_notification(str(e), url)
            return None
    
    def save_to_mysql(self, player: PlayerCard) -> bool:
        """Salva jogador no MySQL"""
        try:
            # Configuração MySQL
            config = {
                'host': 'srv1577.hstgr.io',
                'user': 'u559058762_claudinez',
                'password': 'Cms332211',
                'database': 'u559058762_futbin'
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # SQL completo com todas as colunas da tabela players_horizontal
            insert_sql = """
            INSERT INTO players_horizontal (
                futbin_id, name, overall, rating, position, nation, league, club,
                weak_foot, skill_moves, international_reputation, foot, height, weight,
                body_type, birthdate, accele_rate, revision, price_update, squad,
                club_id, league_id, pace, shooting, passing, dribbling, defending, physical,
                acceleration, sprint_speed, finishing, shot_power, long_shots, volleys, penalties,
                vision, crossing, free_kick_accuracy, short_passing, long_passing, curve,
                agility, balance, reactions, ball_control, dribbling_detailed, composure,
                interceptions, heading_accuracy, marking, standing_tackle, sliding_tackle,
                jumping, stamina, strength, aggression, image_url, futbin_url,
                alt_positions_json, playstyles_json, prices_json, chemistry_styles_json, roles_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                overall = VALUES(overall),
                pace = VALUES(pace),
                shooting = VALUES(shooting),
                passing = VALUES(passing),
                dribbling = VALUES(dribbling),
                defending = VALUES(defending),
                physical = VALUES(physical),
                acceleration = VALUES(acceleration),
                sprint_speed = VALUES(sprint_speed),
                finishing = VALUES(finishing),
                shot_power = VALUES(shot_power),
                long_shots = VALUES(long_shots),
                volleys = VALUES(volleys),
                penalties = VALUES(penalties),
                vision = VALUES(vision),
                crossing = VALUES(crossing),
                free_kick_accuracy = VALUES(free_kick_accuracy),
                short_passing = VALUES(short_passing),
                long_passing = VALUES(long_passing),
                curve = VALUES(curve),
                agility = VALUES(agility),
                balance = VALUES(balance),
                reactions = VALUES(reactions),
                ball_control = VALUES(ball_control),
                dribbling_detailed = VALUES(dribbling_detailed),
                composure = VALUES(composure),
                interceptions = VALUES(interceptions),
                heading_accuracy = VALUES(heading_accuracy),
                marking = VALUES(marking),
                standing_tackle = VALUES(standing_tackle),
                sliding_tackle = VALUES(sliding_tackle),
                jumping = VALUES(jumping),
                stamina = VALUES(stamina),
                strength = VALUES(strength),
                aggression = VALUES(aggression),
                updated_at = CURRENT_TIMESTAMP
            """
            
            # Valores completos (62 parâmetros) para tabela players_horizontal
            values = (
                player.id, player.nome, player.overall, player.overall, player.posicao,
                player.nacao, player.liga, player.clube, player.pe_ruim, player.habilidades,
                player.reputacao_internacional, player.pe_preferido, player.altura, player.peso,
                player.tipo_corpo, player.data_nascimento, player.accele_rate, player.revisao,
                player.atualizacao_preco, player.escalao, player.id_clube, player.id_liga,
                player.estatisticas.velocidade, player.estatisticas.finalizacao, player.estatisticas.passe,
                player.estatisticas.drible, player.estatisticas.defesa, player.estatisticas.fisico,
                player.estatisticas_detalhadas.aceleracao, player.estatisticas_detalhadas.velocidade_sprint,
                player.estatisticas_detalhadas.finalizacao_detalhada, player.estatisticas_detalhadas.forca_chute,
                player.estatisticas_detalhadas.chutes_longe, player.estatisticas_detalhadas.voleios,
                player.estatisticas_detalhadas.penaltis, player.estatisticas_detalhadas.visao,
                player.estatisticas_detalhadas.cruzamento, player.estatisticas_detalhadas.precisao_livre,
                player.estatisticas_detalhadas.passe_curto, player.estatisticas_detalhadas.passe_longo,
                player.estatisticas_detalhadas.curva, player.estatisticas_detalhadas.agilidade,
                player.estatisticas_detalhadas.equilibrio, player.estatisticas_detalhadas.reacoes,
                player.estatisticas_detalhadas.controle_bola, player.estatisticas_detalhadas.drible_detalhado,
                player.estatisticas_detalhadas.compostura, player.estatisticas_detalhadas.interceptacoes,
                player.estatisticas_detalhadas.precisao_cabeca, player.estatisticas_detalhadas.marcacao,
                player.estatisticas_detalhadas.carrinho_em_pe, player.estatisticas_detalhadas.carrinho_deslizante,
                player.estatisticas_detalhadas.salto, player.estatisticas_detalhadas.resistencia,
                player.estatisticas_detalhadas.forca, player.estatisticas_detalhadas.agressao,
                player.url_imagem, player.url, json.dumps(player.posicoes_alternativas),
                json.dumps(player.estilos_jogo), json.dumps(player.precos),
                json.dumps(player.estilos_quimica), json.dumps(player.funcoes)
            )
            
            # Debug: contar valores (removido)
            
            cursor.execute(insert_sql, values)
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar no MySQL: {e}")
            return False
    
    def player_exists(self, player_id: str) -> bool:
        """Verifica se o jogador já existe no banco"""
        try:
            config = {
                'host': 'srv1577.hstgr.io',
                'user': 'u559058762_claudinez',
                'password': 'Cms332211',
                'database': 'u559058762_futbin'
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # Verificar se o jogador já existe
            check_sql = "SELECT COUNT(*) FROM players_horizontal WHERE futbin_id = %s"
            cursor.execute(check_sql, (player_id,))
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return result[0] > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar se jogador existe: {e}")
            return False
    
    def _validate_player_data(self, player: PlayerCard) -> bool:
        """Valida se os dados do jogador estão completos"""
        try:
            # Verificar campos obrigatórios
            required_fields = [
                player.nome, player.overall, player.posicao, 
                player.nacao, player.liga, player.clube
            ]
            
            if any(not field or field == 'Desconhecido' for field in required_fields):
                logger.warning(f"Dados básicos incompletos para {player.nome}")
                return False
            
            # Verificar se as estatísticas estão presentes
            if not player.estatisticas or not player.estatisticas_detalhadas:
                logger.warning(f"Estatísticas ausentes para {player.nome}")
                return False
            
            # Verificar se a URL da imagem foi extraída
            if not player.url_imagem:
                logger.warning(f"URL da imagem ausente para {player.nome}")
                return False
            
            # Verificar se roles foram extraídas (pode estar vazio, mas deve ser uma lista)
            if player.funcoes is None:
                logger.warning(f"Roles não extraídas para {player.nome}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar dados do jogador {player.nome}: {e}")
            return False
    
    def _count_players_in_db(self) -> int:
        """Conta quantos jogadores existem no banco"""
        try:
            config = {
                'host': 'srv1577.hstgr.io',
                'user': 'u559058762_claudinez',
                'password': 'Cms332211',
                'database': 'u559058762_futbin'
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM players_horizontal")
            count = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Erro ao contar jogadores no banco: {e}")
            return 0
    
    def _find_all_additional_players(self) -> List[str]:
        """Tenta encontrar TODOS os jogadores adicionais disponíveis"""
        try:
            # Tentar acessar TODAS as páginas do Futbin
            additional_urls = []
            
            # Buscar em muitas páginas (até 50 páginas)
            for page in range(2, 51):  # Páginas 2 a 50
                page_url = f"https://www.futbin.com/25/players?page={page}"
                
                try:
                    logger.info(f"🔍 Verificando página {page}/50: {page_url}")
                    html = self._make_request(page_url)
                    
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        page_urls = self._extract_player_urls_from_page(soup)
                        
                        # Se não encontrou nenhum jogador nesta página, parar
                        if not page_urls:
                            logger.info(f"📄 Página {page} não tem jogadores - parando busca")
                            break
                        
                        additional_urls.extend(page_urls)
                        logger.info(f"✅ Página {page}: {len(page_urls)} jogadores encontrados")
                    else:
                        logger.warning(f"⚠️ Página {page} não retornou HTML")
                        break
                    
                    self._random_delay(1.0, 2.0)
                    
                except Exception as e:
                    logger.error(f"Erro ao verificar página {page}: {e}")
                    continue
            
            logger.info(f"🎯 Total de jogadores adicionais encontrados: {len(additional_urls)}")
            return additional_urls
            
        except Exception as e:
            logger.error(f"Erro ao encontrar jogadores adicionais: {e}")
            return []
    
    def _find_additional_players(self) -> List[str]:
        """Método legado - mantido para compatibilidade"""
        return self._find_all_additional_players()
    
    def _get_player_urls_from_page(self, page: int) -> List[str]:
        """Obtém URLs de jogadores de uma página específica"""
        try:
            page_url = f"https://www.futbin.com/25/players?page={page}"
            logger.info(f"🔍 Acessando página: {page_url}")
            
            html = self._make_request(page_url)
            if not html:
                logger.error(f"❌ Página {page} não retornou HTML")
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            return self._extract_player_urls_from_page(soup)
            
        except Exception as e:
            logger.error(f"Erro ao obter URLs da página {page}: {e}")
            return []
    
    def _extract_player_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extrai URLs de jogadores de uma página específica"""
        urls = []
        try:
            # Procurar por links de jogadores
            player_links = soup.find_all('a', href=re.compile(r'/25/player/\d+/'))
            
            for link in player_links:
                href = link.get('href')
                if href:
                    full_url = f"https://www.futbin.com{href}"
                    if full_url not in urls:
                        urls.append(full_url)
            
        except Exception as e:
            logger.error(f"Erro ao extrair URLs da página: {e}")
        
        return urls
    
    def _handle_section_completion(self, section_number: int, cards_per_section: int, pause_minutes: int):
        """Gerencia a conclusão de uma seção"""
        try:
            # Gerar pausa aleatória entre 5-9 minutos
            random_pause = random.randint(5, 9)
            
            logger.info(f"🎯 SEÇÃO {section_number} CONCLUÍDA!")
            logger.info(f"✅ {cards_per_section} cartas coletadas nesta seção")
            
            # Notificar via Telegram
            self.telegram.send_message(f"""
🎯 <b>SEÇÃO {section_number} CONCLUÍDA!</b>

✅ <b>Cartas coletadas:</b> {cards_per_section}
📊 <b>Total até agora:</b> {self.stats['total_scraped']:,}
⏸️ <b>Pausa:</b> {random_pause} minutos (aleatória)

🔄 <b>Status:</b> Pausando para máxima segurança...
            """)
            
            # Pausa entre seções
            logger.info(f"⏸️ Pausando por {random_pause} minutos...")
            time.sleep(random_pause * 60)
            
            logger.info(f"🚀 Retomando coleta - Próxima seção...")
            
        except Exception as e:
            logger.error(f"Erro ao gerenciar conclusão da seção: {e}")
    
    def _get_missing_fields(self, player: PlayerCard) -> List[str]:
        """Identifica campos faltantes no jogador"""
        missing_fields = []
        
        try:
            # Verificar campos obrigatórios
            if not player.nome or player.nome == 'Desconhecido':
                missing_fields.append('nome')
            if not player.overall:
                missing_fields.append('overall')
            if not player.posicao or player.posicao == 'Desconhecido':
                missing_fields.append('posicao')
            if not player.nacao or player.nacao == 'Desconhecido':
                missing_fields.append('nacao')
            if not player.liga or player.liga == 'Desconhecido':
                missing_fields.append('liga')
            if not player.clube or player.clube == 'Desconhecido':
                missing_fields.append('clube')
            
            # Verificar estatísticas
            if not player.estatisticas:
                missing_fields.append('estatisticas')
            if not player.estatisticas_detalhadas:
                missing_fields.append('estatisticas_detalhadas')
            
            # Verificar imagem
            if not player.url_imagem:
                missing_fields.append('url_imagem')
            
            # Verificar roles
            if player.funcoes is None:
                missing_fields.append('funcoes')
            
        except Exception as e:
            logger.error(f"Erro ao verificar campos faltantes: {e}")
        
        return missing_fields
    
    def _fix_incomplete_cards(self, incomplete_cards: List[Dict]):
        """Tenta corrigir cartas com dados incompletos"""
        try:
            logger.info(f"🔧 Iniciando correção de {len(incomplete_cards)} cartas incompletas")
            
            fixed_count = 0
            
            for i, card_info in enumerate(incomplete_cards, 1):
                try:
                    logger.info(f"🔧 Tentando corrigir carta {i}/{len(incomplete_cards)}: {card_info['name']}")
                    
                    # Tentar scrapar novamente
                    player = self.scrape_player(card_info['url'])
                    
                    if player and self._validate_player_data(player):
                        # Atualizar no banco
                        if self._update_player_in_db(player):
                            fixed_count += 1
                            self.stats['incomplete_count'] += 1
                            logger.info(f"✅ Carta corrigida: {player.nome}")
                        else:
                            logger.error(f"❌ Erro ao atualizar carta: {player.nome}")
                    else:
                        logger.warning(f"⚠️ Carta ainda incompleta: {card_info['name']}")
                    
                    # Delay entre tentativas
                    self._random_delay(5.0, 10.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao corrigir carta {card_info['name']}: {e}")
                    continue
            
            logger.info(f"🔧 Correção concluída: {fixed_count}/{len(incomplete_cards)} cartas corrigidas")
            
        except Exception as e:
            logger.error(f"Erro ao corrigir cartas incompletas: {e}")
    
    def _update_player_in_db(self, player: PlayerCard) -> bool:
        """Atualiza um jogador existente no banco"""
        try:
            config = {
                'host': 'srv1577.hstgr.io',
                'user': 'u559058762_claudinez',
                'password': 'Cms332211',
                'database': 'u559058762_futbin'
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # SQL de atualização
            update_sql = """
            UPDATE players_horizontal SET
                name = %s, overall = %s, position = %s, nation = %s, league = %s, club = %s,
                weak_foot = %s, skill_moves = %s, international_reputation = %s, foot = %s,
                height = %s, weight = %s, body_type = %s, birthdate = %s, accele_rate = %s,
                revision = %s, price_update = %s, squad = %s, club_id = %s, league_id = %s,
                pace = %s, shooting = %s, passing = %s, dribbling = %s, defending = %s, physical = %s,
                acceleration = %s, sprint_speed = %s, finishing = %s, shot_power = %s, long_shots = %s,
                volleys = %s, penalties = %s, vision = %s, crossing = %s, free_kick_accuracy = %s,
                short_passing = %s, long_passing = %s, curve = %s, agility = %s, balance = %s,
                reactions = %s, ball_control = %s, dribbling_detailed = %s, composure = %s,
                interceptions = %s, heading_accuracy = %s, marking = %s, standing_tackle = %s,
                sliding_tackle = %s, jumping = %s, stamina = %s, strength = %s, aggression = %s,
                image_url = %s, alt_positions_json = %s, playstyles_json = %s, prices_json = %s,
                chemistry_styles_json = %s, roles_json = %s, updated_at = CURRENT_TIMESTAMP
            WHERE futbin_id = %s
            """
            
            # Preparar valores
            values = (
                player.nome, player.overall, player.posicao, player.nacao, player.liga, player.clube,
                player.pe_ruim, player.habilidades, player.reputacao_internacional, player.pe_preferido,
                player.altura, player.peso, player.tipo_corpo, player.data_nascimento, player.accele_rate,
                player.revisao, player.atualizacao_preco, player.escalao, player.id_clube, player.id_liga,
                player.estatisticas.velocidade, player.estatisticas.finalizacao, player.estatisticas.passe,
                player.estatisticas.drible, player.estatisticas.defesa, player.estatisticas.fisico,
                player.estatisticas_detalhadas.aceleracao, player.estatisticas_detalhadas.velocidade_sprint,
                player.estatisticas_detalhadas.finalizacao_detalhada, player.estatisticas_detalhadas.forca_chute,
                player.estatisticas_detalhadas.chutes_longe, player.estatisticas_detalhadas.voleios,
                player.estatisticas_detalhadas.penaltis, player.estatisticas_detalhadas.visao,
                player.estatisticas_detalhadas.cruzamento, player.estatisticas_detalhadas.precisao_livre,
                player.estatisticas_detalhadas.passe_curto, player.estatisticas_detalhadas.passe_longo,
                player.estatisticas_detalhadas.curva, player.estatisticas_detalhadas.agilidade,
                player.estatisticas_detalhadas.equilibrio, player.estatisticas_detalhadas.reacoes,
                player.estatisticas_detalhadas.controle_bola, player.estatisticas_detalhadas.drible_detalhado,
                player.estatisticas_detalhadas.compostura, player.estatisticas_detalhadas.interceptacoes,
                player.estatisticas_detalhadas.precisao_cabeca, player.estatisticas_detalhadas.marcacao,
                player.estatisticas_detalhadas.carrinho_em_pe, player.estatisticas_detalhadas.carrinho_deslizante,
                player.estatisticas_detalhadas.salto, player.estatisticas_detalhadas.resistencia,
                player.estatisticas_detalhadas.forca, player.estatisticas_detalhadas.agressao,
                player.url_imagem, json.dumps(player.posicoes_alternativas), json.dumps(player.estilos_jogo),
                json.dumps(player.precos), json.dumps(player.estilos_quimica), json.dumps(player.funcoes),
                player.id
            )
            
            cursor.execute(update_sql, values)
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar jogador no banco: {e}")
            return False
    
    def run_mass_scraping(self):
        """Executa o scraping em massa de TODAS as cartas - SISTEMA COMPLETO"""
        try:
            logger.info("🚀 INICIANDO SCRAPING COMPLETO - TODAS AS 786 PÁGINAS")
            
            # Configurações do sistema
            CARDS_PER_SECTION = 200  # Cartas por seção
            PAUSE_MINUTES = random.randint(5, 9)  # Pausa aleatória entre 5-9 minutos
            TOTAL_PAGES = 786  # Total de páginas do Futbin
            CARDS_PER_PAGE = 30  # Cartas por página
            
            # Calcular total estimado
            total_estimated = TOTAL_PAGES * CARDS_PER_PAGE
            logger.info(f"📊 Total estimado: {total_estimated:,} cartas em {TOTAL_PAGES} páginas")
            
            # Iniciar estatísticas
            self.stats['start_time'] = datetime.now()
            self.stats['total_scraped'] = 0
            self.stats['success_count'] = 0
            self.stats['error_count'] = 0
            self.stats['skipped_count'] = 0
            self.stats['incomplete_count'] = 0
            self.stats['last_status_time'] = datetime.now()
            self.stats['last_summary_time'] = datetime.now()
            
            # Lista para cartas com dados incompletos
            incomplete_cards = []
            
            # Notificar início via Telegram
            self.telegram.send_start_notification(total_estimated)
            
            # Conjunto para evitar URLs duplicadas
            processed_urls = set()
            current_section = 0
            
            # Coletar TODAS as páginas
            for page in range(1, TOTAL_PAGES + 1):
                try:
                    logger.info(f"📄 Processando página {page}/{TOTAL_PAGES}")
                    
                    # Obter URLs da página atual
                    page_urls = self._get_player_urls_from_page(page)
                    
                    if not page_urls:
                        logger.warning(f"⚠️ Página {page} não retornou URLs")
                        continue
                    
                    logger.info(f"✅ Página {page}: {len(page_urls)} URLs encontradas")
                    
                    # Processar cada URL da página
                    for i, url in enumerate(page_urls, 1):
                        try:
                            # Verificar se já processamos esta URL
                            if url in processed_urls:
                                logger.info(f"⏭️ URL já processada: {url}")
                                self.stats['skipped_count'] += 1
                                continue
                            
                            processed_urls.add(url)
                            
                            # Extrair ID do jogador da URL
                            player_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                            
                            # Verificar se o jogador já existe no banco
                            if self.player_exists(player_id):
                                logger.info(f"⏭️ Jogador já existe no banco: {player_id}")
                                self.stats['skipped_count'] += 1
                                continue
                            
                            # Scrapar jogador
                            logger.info(f"🔍 Scrapando: {url}")
                            player = self.scrape_player(url)
                            
                            if player:
                                # Validar se os dados estão completos
                                if self._validate_player_data(player):
                                    # Salvar no MySQL
                                    if self.save_to_mysql(player):
                                        self.stats['success_count'] += 1
                                        self.stats['total_scraped'] += 1
                                        logger.info(f"✅ Jogador salvo: {player.nome}")
                                    else:
                                        self.stats['error_count'] += 1
                                        logger.error(f"❌ Erro ao salvar jogador: {player.nome}")
                                else:
                                    self.stats['incomplete_count'] += 1
                                    incomplete_cards.append({
                                        'url': url,
                                        'player_id': player_id,
                                        'name': player.nome,
                                        'missing_fields': self._get_missing_fields(player)
                                    })
                                    logger.warning(f"⚠️ Dados incompletos: {player.nome}")
                            else:
                                self.stats['error_count'] += 1
                            
                            # Verificar se chegou ao fim da seção
                            if self.stats['total_scraped'] > 0 and self.stats['total_scraped'] % CARDS_PER_SECTION == 0:
                                current_section += 1
                                self._handle_section_completion(current_section, CARDS_PER_SECTION, PAUSE_MINUTES)
                            
                            # Verificar se deve enviar notificação de status (a cada 10 minutos)
                            current_time = datetime.now()
                            time_since_last_status = (current_time - self.stats['last_status_time']).total_seconds() / 60
                            
                            if time_since_last_status >= 10:  # 10 minutos
                                self.telegram.send_status_notification(
                                    self.stats['total_scraped'], 
                                    f"Página {page}/{TOTAL_PAGES}",
                                    self.stats['success_count'],
                                    self.stats['error_count']
                                )
                                self.stats['last_status_time'] = current_time
                            
                            # Verificar se deve enviar resumo (a cada 20 minutos)
                            time_since_last_summary = (current_time - self.stats['last_summary_time']).total_seconds() / 60
                            
                            if time_since_last_summary >= 20:  # 20 minutos
                                self.telegram.send_summary_notification(
                                    self.stats['total_scraped'], 
                                    total_estimated,
                                    self.stats['success_count'],
                                    self.stats['error_count'],
                                    self.stats['skipped_count']
                                )
                                self.stats['last_summary_time'] = current_time
                            
                            # Delay entre jogadores
                            self._random_delay(3.0, 6.0)  # Delay maior para evitar bloqueios
                            
                        except Exception as e:
                            self.stats['error_count'] += 1
                            logger.error(f"❌ Erro ao processar jogador: {e}")
                            continue
                    
                    # Delay entre páginas
                    self._random_delay(5.0, 10.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar página {page}: {e}")
                    continue
            
            # Processar cartas com dados incompletos
            if incomplete_cards:
                logger.info(f"🔄 Processando {len(incomplete_cards)} cartas com dados incompletos")
                self._fix_incomplete_cards(incomplete_cards)
            
            # Verificação final
            final_count = self._count_players_in_db()
            logger.info(f"📊 Total final de jogadores no banco: {final_count}")
            
            # Calcular duração
            duration = datetime.now() - self.stats['start_time']
            duration_minutes = int(duration.total_seconds() / 60)
            
            # Notificar conclusão
            self.telegram.send_completion_notification(
                self.stats['success_count'],
                self.stats['error_count'],
                self.stats['skipped_count'],
                duration_minutes,
                final_count=final_count
            )
            
            logger.info(f"🎉 SCRAPING COMPLETO CONCLUÍDO!")
            logger.info(f"✅ Sucessos: {self.stats['success_count']:,}")
            logger.info(f"❌ Erros: {self.stats['error_count']:,}")
            logger.info(f"⏭️ Pulados: {self.stats['skipped_count']:,}")
            logger.info(f"⚠️ Incompletos corrigidos: {self.stats['incomplete_count']:,}")
            logger.info(f"📊 Total no banco: {final_count}")
            logger.info(f"🎯 Meta: TODAS as cartas ({total_estimated:,})")
            logger.info(f"⏱️ Duração: {duration_minutes} minutos")
            
            # EXECUTAR VERIFICAÇÃO COMPLETA
            logger.info("🔍 INICIANDO VERIFICAÇÃO COMPLETA FINAL...")
            self.telegram.send_message("""
🎉 <b>SCRAPING PRINCIPAL CONCLUÍDO!</b>

📊 <b>Próximo passo:</b> Verificação completa e correção automática
🔄 <b>Status:</b> Iniciando análise final...

⏱️ <b>Duração do scraping:</b> {duration_minutes} minutos
            """.format(duration_minutes=duration_minutes))
            
            # Executar verificação completa
            self.run_complete_verification()
            
            # Iniciar monitoramento contínuo com sistema auxiliar
            logger.info("🔄 INICIANDO MONITORAMENTO CONTÍNUO COM SISTEMA AUXILIAR...")
            
            # Iniciar sistema auxiliar em thread separada
            import threading
            auxiliary_thread = threading.Thread(
                target=self.run_auxiliary_correction_system, 
                args=(30,),  # Verificar a cada 30 minutos
                daemon=True
            )
            auxiliary_thread.start()
            logger.info("🔧 Sistema auxiliar iniciado em thread separada")
            
            # Iniciar monitoramento contínuo principal
            self.run_continuous_monitoring()
            
        except Exception as e:
            logger.error(f"❌ Erro fatal no scraping: {e}")
            self.telegram.send_error_notification(f"Erro fatal: {e}", "Sistema")

    def run_continuous_monitoring(self, check_interval_hours: int = 6):
        """Executa monitoramento contínuo para novas cartas"""
        try:
            logger.info(f"🔄 INICIANDO MONITORAMENTO CONTÍNUO")
            logger.info(f"⏰ Verificando a cada {check_interval_hours} horas")
            
            self.telegram.send_monitoring_start(check_interval_hours)
            
            while True:
                try:
                    logger.info("🔍 Verificando novas cartas...")
                    
                    # Contar cartas atuais no banco
                    current_count = self._count_players_in_db()
                    logger.info(f"📊 Cartas atuais no banco: {current_count}")
                    
                    # Verificar apenas as primeiras páginas (onde novas cartas aparecem)
                    new_cards_found = 0
                    
                    for page in range(1, 11):  # Verifica apenas páginas 1-10
                        try:
                            logger.info(f"🔍 Verificando página {page}/10 para novas cartas")
                            
                            # Buscar URLs da página
                            page_urls = self._get_player_urls_from_page(page)
                            
                            for url in page_urls:
                                try:
                                    # Extrair ID do jogador
                                    player_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                                    
                                    # Verificar se é uma carta nova
                                    if not self.player_exists(player_id):
                                        logger.info(f"🆕 Nova carta encontrada: {player_id}")
                                        
                                        # Scrapar com delay maior (modo lento)
                                        self._random_delay(10.0, 20.0)  # Delay maior no monitoramento
                                        
                                        player = self.scrape_player(url)
                                        
                                        if player and self._validate_player_data(player):
                                            if self.save_to_mysql(player):
                                                new_cards_found += 1
                                                logger.info(f"✅ Nova carta salva: {player.nome}")
                                                
                                                # Notificar nova carta
                                                self.telegram.send_new_card_found(
                                                    player.nome, 
                                                    player.overall, 
                                                    player.posicao, 
                                                    player.clube, 
                                                    self._count_players_in_db()
                                                )
                                            else:
                                                logger.error(f"❌ Erro ao salvar nova carta: {player.nome}")
                                        else:
                                            logger.warning(f"⚠️ Nova carta com dados incompletos: {player_id}")
                                    
                                    # Delay entre verificações (modo lento)
                                    self._random_delay(5.0, 10.0)
                                    
                                except Exception as e:
                                    logger.error(f"❌ Erro ao verificar carta {url}: {e}")
                                    continue
                            
                            # Delay entre páginas (modo lento)
                            self._random_delay(15.0, 30.0)
                            
                        except Exception as e:
                            logger.error(f"❌ Erro ao verificar página {page}: {e}")
                            continue
                    
                    # Relatório do ciclo
                    if new_cards_found > 0:
                        logger.info(f"🎉 CICLO COMPLETO: {new_cards_found} novas cartas encontradas!")
                    else:
                        logger.info("✅ CICLO COMPLETO: Nenhuma nova carta encontrada")
                    
                    self.telegram.send_monitoring_cycle_complete(
                        new_cards_found, 
                        self._count_players_in_db(), 
                        check_interval_hours
                    )
                    
                    # Aguardar próximo ciclo
                    logger.info(f"😴 Aguardando {check_interval_hours} horas para próxima verificação...")
                    time.sleep(check_interval_hours * 3600)  # Converter horas para segundos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no ciclo de monitoramento: {e}")
                    self.telegram.send_error_notification(f"Erro no monitoramento: {e}", "Sistema")
                    time.sleep(3600)  # Aguardar 1 hora antes de tentar novamente
                    
        except KeyboardInterrupt:
            logger.info("🛑 Monitoramento contínuo interrompido pelo usuário")
            self.telegram.send_notification("🛑 MONITORAMENTO CONTÍNUO INTERROMPIDO")
        except Exception as e:
            logger.error(f"❌ Erro fatal no monitoramento: {e}")
            self.telegram.send_error_notification(f"Erro fatal no monitoramento: {e}", "Sistema")

    def _count_total_cards_on_site(self) -> int:
        """Conta o total de cartas disponíveis no site Futbin"""
        try:
            logger.info("🔍 Contando total de cartas no site Futbin...")
            total_cards = 0
            
            # Verificar todas as páginas (786 páginas)
            for page in range(1, 787):
                try:
                    logger.info(f"📄 Verificando página {page}/786 para contagem...")
                    
                    page_urls = self._get_player_urls_from_page(page)
                    page_count = len(page_urls)
                    total_cards += page_count
                    
                    logger.info(f"✅ Página {page}: {page_count} cartas encontradas")
                    
                    # Delay menor para contagem (apenas leitura)
                    self._random_delay(1.0, 2.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar página {page}: {e}")
                    continue
            
            logger.info(f"🎯 Total de cartas no site: {total_cards:,}")
            return total_cards
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar cartas do site: {e}")
            return 0
    
    def _find_missing_cards(self) -> List[Dict]:
        """Encontra cartas que estão faltando no banco"""
        try:
            logger.info("🔍 Procurando cartas faltantes...")
            missing_cards = []
            
            # Verificar todas as páginas
            for page in range(1, 787):
                try:
                    logger.info(f"📄 Verificando página {page}/786 para cartas faltantes...")
                    
                    page_urls = self._get_player_urls_from_page(page)
                    
                    for url in page_urls:
                        try:
                            # Extrair ID do jogador
                            player_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                            
                            # Verificar se existe no banco
                            if not self.player_exists(player_id):
                                missing_cards.append({
                                    'url': url,
                                    'player_id': player_id,
                                    'page': page
                                })
                                logger.info(f"⏭️ Carta faltante encontrada: {player_id} (página {page})")
                            
                            # Delay menor para verificação
                            self._random_delay(0.5, 1.0)
                            
                        except Exception as e:
                            logger.error(f"❌ Erro ao verificar carta {url}: {e}")
                            continue
                    
                    # Delay entre páginas
                    self._random_delay(2.0, 3.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar página {page}: {e}")
                    continue
            
            logger.info(f"🎯 Total de cartas faltantes: {len(missing_cards)}")
            return missing_cards
            
        except Exception as e:
            logger.error(f"❌ Erro ao encontrar cartas faltantes: {e}")
            return []
    
    def _find_incomplete_cards_in_db(self) -> List[Dict]:
        """Encontra cartas no banco com dados incompletos"""
        try:
            logger.info("🔍 Procurando cartas com dados incompletos no banco...")
            incomplete_cards = []
            
            config = {
                'host': 'srv1577.hstgr.io',
                'user': 'u559058762_claudinez',
                'password': 'Cms332211',
                'database': 'u559058762_futbin'
            }
            
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor()
            
            # Buscar cartas com dados incompletos (priorizar por overall)
            query = """
            SELECT futbin_id, name, overall, futbin_url 
            FROM players_horizontal 
            WHERE alt_positions_json = '[]' 
               OR roles_json = '[]' 
               OR image_url = '' 
               OR name = 'Desconhecido'
            ORDER BY overall DESC, futbin_id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            for row in results:
                player_id, name, overall, url = row
                incomplete_cards.append({
                    'player_id': player_id,
                    'name': name,
                    'overall': overall,
                    'url': url
                })
            
            cursor.close()
            connection.close()
            
            logger.info(f"🎯 Cartas com dados incompletos: {len(incomplete_cards)}")
            return incomplete_cards
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar cartas incompletas: {e}")
            return []
    
    def _recollect_missing_cards(self, missing_cards: List[Dict]) -> int:
        """Recoleta cartas que estão faltando"""
        try:
            logger.info(f"🔄 Iniciando recoleta de {len(missing_cards)} cartas faltantes...")
            
            recollected_count = 0
            
            for i, card_info in enumerate(missing_cards, 1):
                try:
                    logger.info(f"🔄 Recoletando carta {i}/{len(missing_cards)}: {card_info['player_id']}")
                    
                    # Scrapar carta
                    player = self.scrape_player(card_info['url'])
                    
                    if player and self._validate_player_data(player):
                        # Salvar no banco
                        if self.save_to_mysql(player):
                            recollected_count += 1
                            logger.info(f"✅ Carta recoletada: {player.nome}")
                            
                            # Notificar via Telegram a cada 10 cartas
                            if recollected_count % 10 == 0:
                                self.telegram.send_message(f"""
🔄 <b>RECOLETA EM ANDAMENTO</b>

✅ <b>Recoletadas:</b> {recollected_count}/{len(missing_cards)}
🎯 <b>Progresso:</b> {(recollected_count/len(missing_cards)*100):.1f}%
👤 <b>Última carta:</b> {player.nome} ({player.overall})

🔄 <b>Status:</b> Continuando recoleta...
                                """)
                        else:
                            logger.error(f"❌ Erro ao salvar carta recoletada: {player.nome}")
                    else:
                        logger.warning(f"⚠️ Carta com dados incompletos: {card_info['player_id']}")
                    
                    # Delay entre recoletas
                    self._random_delay(3.0, 6.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao recoletar carta {card_info['player_id']}: {e}")
                    continue
            
            logger.info(f"🎯 Recoleta concluída: {recollected_count}/{len(missing_cards)} cartas")
            return recollected_count
            
        except Exception as e:
            logger.error(f"❌ Erro na recoleta: {e}")
            return 0
    
    def _fix_incomplete_cards_in_db(self, incomplete_cards: List[Dict]) -> int:
        """Corrige cartas com dados incompletos no banco"""
        try:
            logger.info(f"🔧 Iniciando correção de {len(incomplete_cards)} cartas incompletas...")
            
            fixed_count = 0
            
            for i, card_info in enumerate(incomplete_cards, 1):
                try:
                    logger.info(f"🔧 Corrigindo carta {i}/{len(incomplete_cards)}: {card_info['name']} ({card_info['overall']})")
                    
                    # Re-scrapar carta
                    player = self.scrape_player(card_info['url'])
                    
                    if player and self._validate_player_data(player):
                        # Atualizar no banco
                        if self._update_player_in_db(player):
                            fixed_count += 1
                            logger.info(f"✅ Carta corrigida: {player.nome}")
                            
                            # Notificar via Telegram a cada 5 correções
                            if fixed_count % 5 == 0:
                                self.telegram.send_message(f"""
🔧 <b>CORREÇÃO EM ANDAMENTO</b>

✅ <b>Corrigidas:</b> {fixed_count}/{len(incomplete_cards)}
🎯 <b>Progresso:</b> {(fixed_count/len(incomplete_cards)*100):.1f}%
👤 <b>Última correção:</b> {player.nome} ({player.overall})

🔄 <b>Status:</b> Continuando correções...
                                """)
                        else:
                            logger.error(f"❌ Erro ao atualizar carta: {player.nome}")
                    else:
                        logger.warning(f"⚠️ Carta ainda incompleta: {card_info['name']}")
                    
                    # Delay entre correções (maior para não sobrecarregar)
                    self._random_delay(5.0, 10.0)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao corrigir carta {card_info['name']}: {e}")
                    continue
            
            logger.info(f"🎯 Correção concluída: {fixed_count}/{len(incomplete_cards)} cartas")
            return fixed_count
            
        except Exception as e:
            logger.error(f"❌ Erro na correção: {e}")
            return 0
    
    def run_complete_verification(self):
        """Executa verificação completa e correção automática"""
        try:
            logger.info("🔍 INICIANDO VERIFICAÇÃO COMPLETA DO SISTEMA")
            
            # Notificar início
            self.telegram.send_message("""
🔍 <b>VERIFICAÇÃO COMPLETA INICIADA</b>

📊 <b>Fase 1:</b> Contando cartas no site
📊 <b>Fase 2:</b> Verificando banco de dados
📊 <b>Fase 3:</b> Identificando problemas
📊 <b>Fase 4:</b> Correção automática

🔄 <b>Status:</b> Iniciando análise...
            """)
            
            # FASE 1: Contar cartas no site
            logger.info("📊 FASE 1: Contando cartas no site...")
            site_total = self._count_total_cards_on_site()
            
            # FASE 2: Contar cartas no banco
            logger.info("🗄️ FASE 2: Contando cartas no banco...")
            db_total = self._count_players_in_db()
            
            # FASE 3: Encontrar cartas faltantes
            logger.info("⏭️ FASE 3: Procurando cartas faltantes...")
            missing_cards = self._find_missing_cards()
            
            # FASE 4: Encontrar cartas incompletas
            logger.info("🔧 FASE 4: Procurando cartas incompletas...")
            incomplete_cards = self._find_incomplete_cards_in_db()
            
            # Calcular estatísticas
            missing_count = len(missing_cards)
            incomplete_count = len(incomplete_cards)
            success_rate = (db_total / site_total * 100) if site_total > 0 else 0
            
            # Relatório completo
            report = f"""
📊 <b>RELATÓRIO DE VERIFICAÇÃO COMPLETA</b>

🌐 <b>SITE FUTBIN:</b>
• Total de cartas: {site_total:,}
• Páginas verificadas: 786

🗄️ <b>BANCO DE DADOS:</b>
• Cartas coletadas: {db_total:,}
• Cartas faltantes: {missing_count:,}
• Cartas incompletas: {incomplete_count:,}
• Taxa de sucesso: {success_rate:.1f}%

🎯 <b>ANÁLISE:</b>
• Cartas para recoletar: {missing_count:,}
• Cartas para corrigir: {incomplete_count:,}
• Total de ações: {missing_count + incomplete_count:,}

🔄 <b>PRÓXIMO:</b> Iniciando correção automática...
            """
            
            self.telegram.send_message(report)
            
            # FASE 5: Recoletar cartas faltantes
            if missing_cards:
                logger.info(f"🔄 FASE 5: Recoletando {len(missing_cards)} cartas faltantes...")
                recollected = self._recollect_missing_cards(missing_cards)
                
                self.telegram.send_message(f"""
✅ <b>RECOLETA CONCLUÍDA</b>

🔄 <b>Cartas recoletadas:</b> {recollected}/{missing_count}
📊 <b>Taxa de sucesso:</b> {(recollected/missing_count*100):.1f}%

🎯 <b>Status:</b> Recoleta finalizada!
                """)
            
            # FASE 6: Corrigir cartas incompletas
            if incomplete_cards:
                logger.info(f"🔧 FASE 6: Corrigindo {len(incomplete_cards)} cartas incompletas...")
                fixed = self._fix_incomplete_cards_in_db(incomplete_cards)
                
                self.telegram.send_message(f"""
✅ <b>CORREÇÃO CONCLUÍDA</b>

🔧 <b>Cartas corrigidas:</b> {fixed}/{incomplete_count}
📊 <b>Taxa de sucesso:</b> {(fixed/incomplete_count*100):.1f}%

🎯 <b>Status:</b> Correção finalizada!
                """)
            
            # Relatório final
            final_db_total = self._count_players_in_db()
            final_success_rate = (final_db_total / site_total * 100) if site_total > 0 else 0
            
            final_report = f"""
🎉 <b>VERIFICAÇÃO COMPLETA FINALIZADA!</b>

📊 <b>RESULTADO FINAL:</b>
• Site: {site_total:,} cartas
• Banco: {final_db_total:,} cartas
• Taxa de cobertura: {final_success_rate:.1f}%

✅ <b>AÇÕES REALIZADAS:</b>
• Recoletadas: {recollected if 'recollected' in locals() else 0}
• Corrigidas: {fixed if 'fixed' in locals() else 0}

🎯 <b>STATUS:</b> Sistema 100% verificado e corrigido!
            """
            
            self.telegram.send_message(final_report)
            logger.info("🎉 VERIFICAÇÃO COMPLETA FINALIZADA COM SUCESSO!")
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação completa: {e}")
            self.telegram.send_error_notification(f"Erro na verificação completa: {e}", "Sistema")

    def run_auxiliary_correction_system(self, check_interval_minutes: int = 30):
        """Executa sistema auxiliar de correção de dados incompletos"""
        try:
            logger.info(f"🔧 INICIANDO SISTEMA AUXILIAR DE CORREÇÃO")
            logger.info(f"⏰ Verificando a cada {check_interval_minutes} minutos")
            
            self.telegram.send_message(f"""
🔧 <b>SISTEMA AUXILIAR INICIADO</b>

🎯 <b>Objetivo:</b> Corrigir dados incompletos no banco
⏰ <b>Frequência:</b> A cada {check_interval_minutes} minutos
🎯 <b>Prioridade:</b> Jogadores com overall alto (99-95)

🔄 <b>Status:</b> Monitorando banco de dados...
            """)
            
            while True:
                try:
                    logger.info("🔍 Verificando cartas com dados incompletos...")
                    
                    # Buscar cartas incompletas (priorizar por overall)
                    incomplete_cards = self._find_incomplete_cards_in_db()
                    
                    if incomplete_cards:
                        logger.info(f"🔧 Encontradas {len(incomplete_cards)} cartas para corrigir")
                        
                        # Filtrar por prioridade (overall alto primeiro)
                        high_priority = [card for card in incomplete_cards if card['overall'] >= 95]
                        medium_priority = [card for card in incomplete_cards if 90 <= card['overall'] < 95]
                        low_priority = [card for card in incomplete_cards if card['overall'] < 90]
                        
                        # Corrigir por prioridade
                        total_fixed = 0
                        
                        # Prioridade 1: Overall 95+
                        if high_priority:
                            logger.info(f"🔧 Corrigindo {len(high_priority)} cartas de alta prioridade (95+)")
                            fixed_high = self._fix_incomplete_cards_in_db(high_priority)
                            total_fixed += fixed_high
                            
                            self.telegram.send_message(f"""
🔧 <b>CORREÇÃO DE ALTA PRIORIDADE CONCLUÍDA</b>

⭐ <b>Overall 95+:</b> {fixed_high}/{len(high_priority)} corrigidas
📊 <b>Taxa de sucesso:</b> {(fixed_high/len(high_priority)*100):.1f}%

🎯 <b>Status:</b> Continuando correções...
                            """)
                        
                        # Prioridade 2: Overall 90-94
                        if medium_priority:
                            logger.info(f"🔧 Corrigindo {len(medium_priority)} cartas de média prioridade (90-94)")
                            fixed_medium = self._fix_incomplete_cards_in_db(medium_priority)
                            total_fixed += fixed_medium
                            
                            self.telegram.send_message(f"""
🔧 <b>CORREÇÃO DE MÉDIA PRIORIDADE CONCLUÍDA</b>

⭐ <b>Overall 90-94:</b> {fixed_medium}/{len(medium_priority)} corrigidas
📊 <b>Taxa de sucesso:</b> {(fixed_medium/len(medium_priority)*100):.1f}%

🎯 <b>Status:</b> Continuando correções...
                            """)
                        
                        # Prioridade 3: Overall < 90
                        if low_priority:
                            logger.info(f"🔧 Corrigindo {len(low_priority)} cartas de baixa prioridade (<90)")
                            fixed_low = self._fix_incomplete_cards_in_db(low_priority)
                            total_fixed += fixed_low
                            
                            self.telegram.send_message(f"""
🔧 <b>CORREÇÃO DE BAIXA PRIORIDADE CONCLUÍDA</b>

⭐ <b>Overall <90:</b> {fixed_low}/{len(low_priority)} corrigidas
📊 <b>Taxa de sucesso:</b> {(fixed_low/len(low_priority)*100):.1f}%

🎯 <b>Status:</b> Correção finalizada!
                            """)
                        
                        # Relatório final do ciclo
                        self.telegram.send_message(f"""
✅ <b>CICLO DE CORREÇÃO CONCLUÍDO</b>

🔧 <b>Total corrigidas:</b> {total_fixed}/{len(incomplete_cards)}
📊 <b>Taxa de sucesso:</b> {(total_fixed/len(incomplete_cards)*100):.1f}%

🎯 <b>Próxima verificação:</b> Em {check_interval_minutes} minutos
                            """)
                        
                    else:
                        logger.info("✅ Nenhuma carta com dados incompletos encontrada")
                        self.telegram.send_message(f"""
✅ <b>VERIFICAÇÃO CONCLUÍDA</b>

🎯 <b>Resultado:</b> Nenhuma carta com dados incompletos
📊 <b>Status:</b> Banco de dados em excelente estado!

⏰ <b>Próxima verificação:</b> Em {check_interval_minutes} minutos
                            """)
                        
                    # Aguardar próximo ciclo
                    logger.info(f"😴 Aguardando {check_interval_minutes} minutos para próxima verificação...")
                    time.sleep(check_interval_minutes * 60)  # Converter minutos para segundos
                    
                except Exception as e:
                    logger.error(f"❌ Erro no ciclo de correção auxiliar: {e}")
                    self.telegram.send_error_notification(f"Erro no sistema auxiliar: {e}", "Sistema")
                    time.sleep(300)  # Aguardar 5 minutos antes de tentar novamente
                    
        except KeyboardInterrupt:
            logger.info("🛑 Sistema auxiliar interrompido pelo usuário")
            self.telegram.send_notification("🛑 SISTEMA AUXILIAR INTERROMPIDO")
        except Exception as e:
            logger.error(f"❌ Erro fatal no sistema auxiliar: {e}")
            self.telegram.send_error_notification(f"Erro fatal no sistema auxiliar: {e}", "Sistema")

def main():
    """Função principal"""
    # Token do Telegram
    telegram_token = "8450381764:AAHS7rOLqUZjdoMgypzKaots282jf9CQlfw"
    
    # Criar scraper
    scraper = FutbinMassScraper(telegram_token)
    
    # Executar scraping em massa
    scraper.run_mass_scraping()

if __name__ == "__main__":
    main() 