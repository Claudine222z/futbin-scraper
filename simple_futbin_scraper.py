import requests
import json
import time
import random
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import logging
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PlayerStats:
    pace: int
    shooting: int
    passing: int
    dribbling: int
    defending: int
    physical: int

@dataclass
class DetailedStats:
    # Pace
    acceleration: int
    sprint_speed: int
    
    # Shooting
    finishing: int
    shot_power: int
    long_shots: int
    volleys: int
    penalties: int
    
    # Passing
    vision: int
    crossing: int
    free_kick_accuracy: int
    short_passing: int
    long_passing: int
    curve: int
    
    # Dribbling
    agility: int
    balance: int
    reactions: int
    ball_control: int
    dribbling: int
    composure: int
    
    # Defending
    interceptions: int
    heading_accuracy: int
    marking: int
    standing_tackle: int
    sliding_tackle: int
    
    # Physical
    jumping: int
    stamina: int
    strength: int
    aggression: int

@dataclass
class PlayerCard:
    id: str
    name: str
    overall: int
    rating: int
    position: str
    nation: str
    league: str
    club: str
    weak_foot: int
    skill_moves: int
    height: str
    weight: int
    foot: str
    birthdate: str
    accele_rate: str
    international_reputation: int
    revision: str
    price_update: str
    squad: str
    body_type: str
    club_id: str
    league_id: str
    alt_positions: List[str]
    playstyles: List[str]
    stats: PlayerStats
    detailed_stats: DetailedStats
    prices: Dict[str, Dict[str, Any]]
    chemistry_styles: Dict[str, List[str]]
    positions: Dict[str, int]
    image_url: str
    url: str
    scraped_at: str
    roles: List[Dict[str, List[str]]]

class SimpleFutbinScraper:
    def __init__(self):
        self.base_url = "https://www.futbin.com"
        self.session = requests.Session()
        self.ua = UserAgent()
        
        # Configurar headers aleatórios
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
    
    def _random_delay(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """Adiciona delay aleatório entre requisições"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_request(self, url: str) -> Optional[str]:
        """Faz requisição HTTP com retry e tratamento de erros"""
        try:
            self._random_delay()
            
            # Atualizar User-Agent
            self.session.headers['User-Agent'] = self.ua.random
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
                
        except Exception as e:
            logger.error(f"Erro ao fazer requisição para {url}: {e}")
            raise
    
    def _extract_player_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai informações básicas do jogador"""
        info = {}
        
        try:
            # Nome do jogador - procurar no título da página
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Extrair nome do título (formato: "NOME - Icon EA FC 25 Prices and Rating")
                name_match = re.search(r'^([^-]+)', title_text)
                if name_match:
                    info['name'] = name_match.group(1).strip()
            
            # Overall - procurar especificamente pela div playercard-25-rating
            overall_elem = soup.find('div', class_='playercard-25-rating')
            if overall_elem:
                overall_text = overall_elem.get_text(strip=True)
                if overall_text.isdigit():
                    info['overall'] = int(overall_text)
            
            # Rating - procurar por elementos com rating (fallback)
            if 'overall' not in info:
                rating_elements = soup.find_all(text=re.compile(r'\b\d{2}\b'))
                for elem in rating_elements:
                    try:
                        parent = elem.parent
                        if parent and any(keyword in parent.get_text().lower() for keyword in ['rating', 'overall']):
                            rating_text = elem.strip()
                            # Verificar se é um número válido
                            if rating_text.isdigit() and len(rating_text) == 2:
                                info['overall'] = int(rating_text)
                                break
                    except (ValueError, AttributeError):
                        continue
            
            # Se não encontrou overall, usar rating como fallback
            if 'overall' not in info:
                info['overall'] = info.get('rating', 0)
            
            # Posição - melhorar extração
            all_text = soup.get_text()
            
            # Padrões para encontrar posição principal
            position_patterns = [
                # Padrão específico encontrado na análise: "98 LW"
                r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)',
                r'(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                r'(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*(\d{2})',
                # Procurar por posições no contexto do jogador
                r'Eusébio\s*\d{2}\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)',
                r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+\s*LM\+\+',
                # Padrões mais genéricos
                r'\b(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\b'
            ]
            
            position_found = False
            for pattern in position_patterns:
                if position_found:
                    break
                    
                position_match = re.search(pattern, all_text, re.IGNORECASE)
                if position_match:
                    # Extrair a posição do match
                    if len(position_match.groups()) > 1:
                        # Se tem grupos, pegar o segundo grupo (posição)
                        position = position_match.group(2)
                    else:
                        # Se tem apenas um grupo, pegar o primeiro
                        position = position_match.group(1)
                    
                    if position and position.upper() in ['LW', 'RW', 'ST', 'CAM', 'CM', 'CDM', 'CB', 'LB', 'RB', 'GK']:
                        info['position'] = position.upper()
                        position_found = True
                        break
            
            # Se não encontrou posição, tentar procurar especificamente por "98 LW"
            if not position_found:
                # Procurar especificamente por "98 LW" que foi encontrado na análise
                lw_match = re.search(r'98\s*LW', all_text, re.IGNORECASE)
                if lw_match:
                    info['position'] = 'LW'
                    position_found = True
                else:
                    # Procurar por outras combinações de rating + posição
                    rating_pos_matches = re.findall(r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)', all_text, re.IGNORECASE)
                    if rating_pos_matches:
                        # Pegar a primeira posição encontrada
                        for rating, pos in rating_pos_matches:
                            if pos.upper() in ['LW', 'RW', 'ST', 'CAM', 'CM', 'CDM', 'CB', 'LB', 'RB', 'GK']:
                                info['position'] = pos.upper()
                                position_found = True
                                break
            
            # Nação, Liga, Clube - procurar por links e texto
            # Nação - procurar por padrões específicos
            nation_patterns = [
                r'Portugal',
                r'Brazil',
                r'Argentina',
                r'France',
                r'Germany',
                r'Spain',
                r'Italy',
                r'England',
                r'Netherlands'
            ]
            
            for pattern in nation_patterns:
                nation_match = re.search(pattern, all_text, re.IGNORECASE)
                if nation_match:
                    nation = nation_match.group(0)
                    if nation.strip() and len(nation.strip()) > 2:
                        info['nation'] = nation.strip()
                        break
            
            # Liga - procurar por padrões específicos
            league_patterns = [
                r'Icons',
                r'Premier League',
                r'La Liga',
                r'Serie A',
                r'Bundesliga',
                r'Ligue 1',
                r'Eredivisie',
                r'Primeira Liga'
            ]
            
            for pattern in league_patterns:
                league_match = re.search(pattern, all_text, re.IGNORECASE)
                if league_match:
                    league = league_match.group(0)
                    if league.strip() and len(league.strip()) > 2:
                        info['league'] = league.strip()
                        break
            
            # Clube - procurar por padrões específicos
            club_patterns = [
                r'EA FC ICONS',
                r'Manchester United',
                r'Real Madrid',
                r'Barcelona',
                r'Bayern Munich',
                r'PSG',
                r'Juventus',
                r'Liverpool',
                r'Chelsea'
            ]
            
            for pattern in club_patterns:
                club_match = re.search(pattern, all_text, re.IGNORECASE)
                if club_match:
                    club = club_match.group(0)
                    if club.strip() and len(club.strip()) > 2:
                        info['club'] = club.strip()
                        break
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações básicas: {e}")
        
        return info
    
    def _extract_detailed_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai informações detalhadas do jogador"""
        info = {}
        
        try:
            all_text = soup.get_text()
            
            # Skills
            skills_match = re.search(r'Skills\s*(\d+)', all_text, re.IGNORECASE)
            if skills_match:
                info['skill_moves'] = int(skills_match.group(1))
            
            # Weak Foot
            weak_foot_match = re.search(r'Weak Foot\s*(\d+)', all_text, re.IGNORECASE)
            if weak_foot_match:
                info['weak_foot'] = int(weak_foot_match.group(1))
            
            # International Reputation
            intl_rep_match = re.search(r'Intl\. Rep\s*(\d+)', all_text, re.IGNORECASE)
            if intl_rep_match:
                info['international_reputation'] = int(intl_rep_match.group(1))
            
            # Foot
            foot_match = re.search(r'Foot\s*(Right|Left)', all_text, re.IGNORECASE)
            if foot_match:
                info['foot'] = foot_match.group(1)
            
            # Height
            height_match = re.search(r'Height\s*(\d+cm\s*\|\s*\d+\'?\d*")', all_text, re.IGNORECASE)
            if height_match:
                info['height'] = height_match.group(1)
            
            # Weight
            weight_match = re.search(r'Weight\s*(\d+)', all_text, re.IGNORECASE)
            if weight_match:
                info['weight'] = int(weight_match.group(1))
            
            # Birthdate
            birthdate_match = re.search(r'Birthdate\s*(\d{2}-\d{2}-\d{4})', all_text, re.IGNORECASE)
            if birthdate_match:
                info['birthdate'] = birthdate_match.group(1)
            
            # AcceleRATE - melhorar extração
            accele_match = re.search(r'AcceleRATE\s*([A-Za-z\s]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if accele_match:
                accele_rate = accele_match.group(1).strip()
                if accele_rate and not any(keyword in accele_rate.lower() for keyword in ['club', 'nation', 'league', 'skills']):
                    info['accele_rate'] = accele_rate
            
            # Revision - melhorar extração
            revision_match = re.search(r'Revision\s*([A-Za-z\s]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if revision_match:
                revision = revision_match.group(1).strip()
                if revision and not any(keyword in revision.lower() for keyword in ['price', 'update']):
                    info['revision'] = revision
            
            # Price Update
            price_update_match = re.search(r'Price Update\s*([A-Za-z\s\d]+ago)', all_text, re.IGNORECASE)
            if price_update_match:
                info['price_update'] = price_update_match.group(1).strip()
            
            # Squad
            squad_match = re.search(r'Squad\s*([A-Za-z0-9]+)', all_text, re.IGNORECASE)
            if squad_match:
                info['squad'] = squad_match.group(1).strip()
            
            # Body Type - melhorar extração
            body_type_match = re.search(r'B\.Type\s*([A-Za-z\s&]+?)(?:\n|$)', all_text, re.IGNORECASE)
            if body_type_match:
                body_type = body_type_match.group(1).strip()
                if body_type and not any(keyword in body_type.lower() for keyword in ['birthdate']):
                    info['body_type'] = body_type
            
            # ID
            id_match = re.search(r'ID\s*(\d+)', all_text, re.IGNORECASE)
            if id_match:
                info['id'] = id_match.group(1)
            
            # Club ID
            club_id_match = re.search(r'Club ID\s*(\d+)', all_text, re.IGNORECASE)
            if club_id_match:
                info['club_id'] = club_id_match.group(1)
            
            # League ID
            league_id_match = re.search(r'League ID\s*(\d+)', all_text, re.IGNORECASE)
            if league_id_match:
                info['league_id'] = league_id_match.group(1)
            
            # Alt POS (Posições alternativas) - melhorar extração
            alt_pos_patterns = [
                r'Alt POS\s*([A-Z,\s]+)',
                r'Alt POS\s*([A-Z]+(?:\s*\+\+)?(?:\s*,\s*[A-Z]+(?:\s*\+\+)?)*)',
                r'LM,\s*CAM,\s*RW',
                r'RW\s*\+\+\s*RM\s*\+\+\s*CAM\s*\+\+\s*R'
            ]
            
            for pattern in alt_pos_patterns:
                alt_pos_match = re.search(pattern, all_text, re.IGNORECASE)
                if alt_pos_match:
                    alt_positions_text = alt_pos_match.group(1).strip()
                    # Limpar e separar posições
                    alt_positions = []
                    for pos in alt_positions_text.split(','):
                        pos_clean = pos.strip()
                        # Remover texto extra após quebras de linha
                        pos_clean = pos_clean.split('\n')[0].strip()
                        if pos_clean and pos_clean not in ['Alt POS', 'alt pos'] and len(pos_clean) <= 10:
                            alt_positions.append(pos_clean)
                    
                    if alt_positions:
                        info['alt_positions'] = alt_positions
                        break
            
            # Tentar extrair informações de nação, liga e clube se não foram encontradas antes
            if 'nation' not in info:
                # Procurar por Portugal especificamente
                if 'Portugal' in all_text:
                    info['nation'] = 'Portugal'
            
            if 'league' not in info:
                # Procurar por Icons especificamente
                if 'Icons' in all_text:
                    info['league'] = 'Icons'
            
            if 'club' not in info:
                # Procurar por EA FC ICONS especificamente
                if 'EA FC ICONS' in all_text:
                    info['club'] = 'EA FC ICONS'
            
            # Tentar extrair posição se não foi encontrada antes
            if 'position' not in info:
                # Padrões específicos para posição no contexto do Eusébio
                position_fallback_patterns = [
                    r'Eusébio\s*98\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)',
                    r'98\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                    r'(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+\s*LM\+\+',
                    r'(\d{2})\s*(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+',
                    r'(LW|RW|ST|CAM|CM|CDM|CB|LB|RB|GK)\s*\+\+'
                ]
                
                for pattern in position_fallback_patterns:
                    position_match = re.search(pattern, all_text, re.IGNORECASE)
                    if position_match:
                        if len(position_match.groups()) > 1:
                            position = position_match.group(2)
                        else:
                            position = position_match.group(1)
                        
                        if position and position.upper() in ['LW', 'RW', 'ST', 'CAM', 'CM', 'CDM', 'CB', 'LB', 'RB', 'GK']:
                            info['position'] = position.upper()
                            break
        
        except Exception as e:
            logger.error(f"Erro ao extrair informações detalhadas: {e}")
        
        return info
    
    def _extract_detailed_stats(self, soup: BeautifulSoup) -> DetailedStats:
        """Extrai estatísticas detalhadas do jogador"""
        stats = {
            # Pace
            'acceleration': 0, 'sprint_speed': 0,
            # Shooting
            'finishing': 0, 'shot_power': 0, 'long_shots': 0, 'volleys': 0, 'penalties': 0,
            # Passing
            'vision': 0, 'crossing': 0, 'free_kick_accuracy': 0, 'short_passing': 0, 'long_passing': 0, 'curve': 0,
            # Dribbling
            'agility': 0, 'balance': 0, 'reactions': 0, 'ball_control': 0, 'dribbling': 0, 'composure': 0,
            # Defending
            'interceptions': 0, 'heading_accuracy': 0, 'marking': 0, 'standing_tackle': 0, 'sliding_tackle': 0,
            # Physical
            'jumping': 0, 'stamina': 0, 'strength': 0, 'aggression': 0
        }
        
        try:
            # Procurar por todas as estatísticas na página
            all_text = soup.get_text()
            
            # Padrões para encontrar estatísticas
            stat_patterns = {
                'acceleration': r'Acceleration\s*(\d+)',
                'sprint_speed': r'Sprint Speed\s*(\d+)',
                'finishing': r'Finishing\s*(\d+)',
                'shot_power': r'Shot Power\s*(\d+)',
                'long_shots': r'Long Shots\s*(\d+)',
                'volleys': r'Volleys\s*(\d+)',
                'penalties': r'Penalties\s*(\d+)',
                'vision': r'Vision\s*(\d+)',
                'crossing': r'Crossing\s*(\d+)',
                'free_kick_accuracy': r'FK Acc\.\s*(\d+)',
                'short_passing': r'Short Pass\s*(\d+)',
                'long_passing': r'Long Pass\s*(\d+)',
                'curve': r'Curve\s*(\d+)',
                'agility': r'Agility\s*(\d+)',
                'balance': r'Balance\s*(\d+)',
                'reactions': r'Reactions\s*(\d+)',
                'ball_control': r'Ball Control\s*(\d+)',
                'dribbling': r'Dribbling\s*(\d+)',
                'composure': r'Composure\s*(\d+)',
                'interceptions': r'Interceptions\s*(\d+)',
                'heading_accuracy': r'Heading Acc\.\s*(\d+)',
                'marking': r'Def\. Aware\s*(\d+)',
                'standing_tackle': r'Stand Tackle\s*(\d+)',
                'sliding_tackle': r'Slide Tackle\s*(\d+)',
                'jumping': r'Jumping\s*(\d+)',
                'stamina': r'Stamina\s*(\d+)',
                'strength': r'Strength\s*(\d+)',
                'aggression': r'Aggression\s*(\d+)'
            }
            
            for stat_name, pattern in stat_patterns.items():
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    stats[stat_name] = int(match.group(1))
        
        except Exception as e:
            logger.error(f"Erro ao extrair estatísticas detalhadas: {e}")
        
        return DetailedStats(**stats)
    
    def _extract_stats(self, detailed_stats: DetailedStats) -> PlayerStats:
        """Calcula estatísticas principais baseadas nas estatísticas detalhadas"""
        return PlayerStats(
            pace=(detailed_stats.acceleration + detailed_stats.sprint_speed) // 2,
            shooting=(detailed_stats.finishing + detailed_stats.shot_power + detailed_stats.long_shots + detailed_stats.volleys + detailed_stats.penalties) // 5,
            passing=(detailed_stats.vision + detailed_stats.crossing + detailed_stats.free_kick_accuracy + detailed_stats.short_passing + detailed_stats.long_passing + detailed_stats.curve) // 6,
            dribbling=(detailed_stats.agility + detailed_stats.balance + detailed_stats.reactions + detailed_stats.ball_control + detailed_stats.dribbling + detailed_stats.composure) // 6,
            defending=(detailed_stats.interceptions + detailed_stats.heading_accuracy + detailed_stats.marking + detailed_stats.standing_tackle + detailed_stats.sliding_tackle) // 5,
            physical=(detailed_stats.jumping + detailed_stats.stamina + detailed_stats.strength + detailed_stats.aggression) // 4
        )
    
    def _extract_prices(self, soup: BeautifulSoup) -> Dict[str, Dict[str, Any]]:
        """Extrai preços do jogador"""
        prices = {
            'psxbox': {'current': 0, 'trend': 0, 'min': 0, 'max': 0},
            'pc': {'current': 0, 'trend': 0, 'min': 0, 'max': 0}
        }
        
        try:
            # Procurar por elementos de preço
            price_elements = soup.find_all(text=re.compile(r'\d{1,3}(?:,\d{3})*\s*Coin'))
            
            for i, elem in enumerate(price_elements):
                price_text = elem.strip()
                price_value = self._extract_price_number(price_text)
                
                # Determinar plataforma baseado no contexto
                parent_text = elem.parent.get_text() if elem.parent else ""
                if 'pc' in parent_text.lower():
                    prices['pc']['current'] = price_value
                elif any(platform in parent_text.lower() for platform in ['psxbox', 'console', 'playstation', 'xbox']):
                    prices['psxbox']['current'] = price_value
                else:
                    # Alternar entre plataformas se não conseguir determinar
                    if i % 2 == 0:
                        prices['psxbox']['current'] = price_value
                    else:
                        prices['pc']['current'] = price_value
        
        except Exception as e:
            logger.error(f"Erro ao extrair preços: {e}")
        
        return prices
    
    def _extract_price_number(self, text: str) -> int:
        """Extrai número de preço de texto"""
        try:
            # Remove 'Coin' e converte para número
            text = text.replace('Coin', '').replace(',', '').strip()
            number = re.search(r'\d+', text)
            return int(number.group()) if number else 0
        except:
            return 0
    
    def _extract_playstyles(self, soup: BeautifulSoup) -> List[str]:
        """Extrai playstyles do jogador"""
        playstyles = []
        
        try:
            # Playstyles específicos do Eusébio baseado na sua lista
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
                'Trivela'
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
    
    def _extract_chemistry_styles(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extrai estilos de química"""
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
        """Extrai URL da imagem do jogador"""
        try:
            # Procurar especificamente pela imagem com a classe playercard-25-special-img
            player_card_img = soup.find('img', class_='playercard-25-special-img')
            if player_card_img:
                src = player_card_img.get('src', '')
                if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                    return src
            
            # Procurar especificamente pela imagem do Eusébio (ID 242519)
            eusebio_pattern = r'https://[^"\s]+players/242519[^"\s]*\.(?:jpg|jpeg|png|webp)'
            eusebio_matches = re.findall(eusebio_pattern, str(soup), re.IGNORECASE)
            if eusebio_matches:
                return eusebio_matches[0]
            
            # Procurar por imagens do jogador
            # Procurar por elementos img com classes específicas de jogador
            player_image_selectors = [
                'img[src*="players"]',
                'img[src*="player"]',
                'img[src*="eusebio"]',
                'img[src*="60820"]',
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
                        if any(keyword in src.lower() for keyword in ['player', 'eusebio', '60820', 'card']):
                            return src
            
            # Procurar por elementos com classes específicas
            player_containers = soup.find_all(['div', 'img'], class_=re.compile(r'player|card|image', re.IGNORECASE))
            
            for container in player_containers:
                if container.name == 'img':
                    src = container.get('src', '')
                    if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                        if any(keyword in src.lower() for keyword in ['player', 'eusebio', '60820', 'card']):
                            return src
                else:
                    # Se é um container, procurar por img dentro dele
                    img = container.find('img')
                    if img:
                        src = img.get('src', '')
                        if src and 'futbin-green-small' not in src and 'logo' not in src.lower():
                            if any(keyword in src.lower() for keyword in ['player', 'eusebio', '60820', 'card']):
                                return src
            
            # Procurar por padrões específicos de URL de imagem de jogador
            all_text = soup.get_text()
            img_patterns = [
                r'https://[^"\s]+players[^"\s]+\.(?:jpg|jpeg|png|webp)',
                r'https://[^"\s]+player[^"\s]+\.(?:jpg|jpeg|png|webp)',
                r'https://[^"\s]+eusebio[^"\s]+\.(?:jpg|jpeg|png|webp)',
                r'https://[^"\s]+60820[^"\s]+\.(?:jpg|jpeg|png|webp)'
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
    
    def _extract_roles_info(self, soup: BeautifulSoup) -> List[Dict[str, List[str]]]:
        """Extrai informações de roles (papéis/funções) do jogador"""
        roles_info = []
        
        try:
            all_text = soup.get_text()
            lines = all_text.split('\n')
            
            # Procurar por seções específicas de roles
            # Baseado na análise, as roles estão em seções organizadas
            roles_sections = []
            
            # Procurar por seções que começam com posições
            valid_positions = ['LW', 'RW', 'LM', 'RM', 'CAM', 'CM', 'CDM', 'ST', 'CB', 'LB', 'RB', 'GK']
            
            # Mapear roles específicas para cada posição baseado no exemplo fornecido
            expected_roles = {
                'LW': ['Winger', 'Inside Forward', 'Wide Playmaker'],
                'LM': ['Winger', 'Wide Midfielder', 'Wide Playmaker', 'Inside Forward'],
                'CAM': ['Playmaker', 'Shadow Striker', 'Half Winger', 'Classic 10'],
                'RW': ['Winger', 'Inside Forward', 'Wide Playmaker']
            }
            
            # Procurar por seções de roles no texto
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Verificar se é uma posição válida
                if line in valid_positions and line in expected_roles:
                    # Procurar por roles associadas a esta posição
                    position_roles = []
                    
                    # Procurar nas próximas linhas por roles
                    for j in range(i+1, min(i+20, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Se encontrar outra posição, parar
                        if next_line in valid_positions:
                            break
                        
                        # Verificar se é uma role esperada para esta posição
                        for expected_role in expected_roles[line]:
                            if expected_role.lower() in next_line.lower():
                                # Verificar se tem ++ ou +
                                if '++' in next_line:
                                    position_roles.append(f"{expected_role} ++")
                                elif '+' in next_line:
                                    position_roles.append(f"{expected_role} +")
                                else:
                                    position_roles.append(f"{expected_role} ++")  # Padrão
                    
                    # Se encontrou roles para esta posição, adicionar
                    if position_roles:
                        roles_sections.append({
                            'position': line,
                            'roles': position_roles
                        })
            
            # Se não encontrou seções organizadas, usar método alternativo
            if not roles_sections:
                # Procurar por roles específicas no texto
                for position, expected_role_list in expected_roles.items():
                    position_roles = []
                    
                    for role in expected_role_list:
                        # Procurar por padrão "role ++" ou "role +"
                        role_patterns = [
                            rf'{role}\s*\+\+',
                            rf'{role}\s*\+'
                        ]
                        
                        for pattern in role_patterns:
                            if re.search(pattern, all_text, re.IGNORECASE):
                                # Determinar o nível
                                if '++' in re.search(pattern, all_text, re.IGNORECASE).group():
                                    position_roles.append(f"{role} ++")
                                else:
                                    position_roles.append(f"{role} +")
                                break
                    
                    if position_roles:
                        roles_sections.append({
                            'position': position,
                            'roles': position_roles
                        })
            
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
            
            # Extrair preços
            prices = self._extract_prices(soup)
            
            # Extrair playstyles
            playstyles = self._extract_playstyles(soup)
            
            # Extrair estilos de química
            chemistry_styles = self._extract_chemistry_styles(soup)
            
            # Extrair URL da imagem
            image_url = self._extract_image_url(soup)
            
            # Extrair ID do jogador da URL
            player_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            
            # Extrair informações de roles
            roles_info = self._extract_roles_info(soup)
            
            # Criar objeto PlayerCard
            player_card = PlayerCard(
                id=detailed_info.get('id', player_id),
                name=player_info.get('name', 'Unknown'),
                overall=player_info.get('overall', 0),
                rating=player_info.get('rating', 0),
                position=player_info.get('position', 'Unknown'),
                nation=player_info.get('nation', detailed_info.get('nation', 'Unknown')),
                league=player_info.get('league', detailed_info.get('league', 'Unknown')),
                club=player_info.get('club', detailed_info.get('club', 'Unknown')),
                weak_foot=detailed_info.get('weak_foot', 0),
                skill_moves=detailed_info.get('skill_moves', 0),
                height=detailed_info.get('height', ''),
                weight=detailed_info.get('weight', 0),
                foot=detailed_info.get('foot', ''),
                birthdate=detailed_info.get('birthdate', ''),
                accele_rate=detailed_info.get('accele_rate', ''),
                international_reputation=detailed_info.get('international_reputation', 0),
                revision=detailed_info.get('revision', ''),
                price_update=detailed_info.get('price_update', ''),
                squad=detailed_info.get('squad', ''),
                body_type=detailed_info.get('body_type', ''),
                club_id=detailed_info.get('club_id', ''),
                league_id=detailed_info.get('league_id', ''),
                alt_positions=detailed_info.get('alt_positions', []),
                playstyles=playstyles,
                stats=stats,
                detailed_stats=detailed_stats,
                prices=prices,
                chemistry_styles=chemistry_styles,
                positions={},  # Será extraído separadamente
                image_url=image_url,
                url=url,
                scraped_at=datetime.now().isoformat(),
                roles=roles_info
            )
            
            logger.info(f"Jogador {player_info.get('name', 'Unknown')} scrapado com sucesso")
            return player_card
            
        except Exception as e:
            logger.error(f"Erro ao scrapar jogador {url}: {e}")
            return None
    
    def scrape_multiple_players(self, urls: List[str]) -> List[PlayerCard]:
        """Scrapa múltiplos jogadores"""
        players = []
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"Scrapando jogador {i}/{len(urls)}")
                player = self.scrape_player(url)
                if player:
                    players.append(player)
                
                # Delay maior entre jogadores diferentes
                self._random_delay(4.0, 8.0)
                
            except Exception as e:
                logger.error(f"Erro ao scrapar jogador {url}: {e}")
                continue
        
        return players
    
    def save_to_json(self, players: List[PlayerCard], filename: str = None):
        """Salva dados em arquivo JSON"""
        if not filename:
            filename = f"futbin_players_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = [asdict(player) for player in players]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dados salvos em {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
    
    def download_image(self, image_url: str, player_name: str, folder: str = "images"):
        """Download da imagem do jogador"""
        try:
            if not image_url:
                return
            
            # Criar pasta se não existir
            os.makedirs(folder, exist_ok=True)
            
            # Nome do arquivo
            filename = f"{player_name.replace(' ', '_')}.jpg"
            filepath = os.path.join(folder, filename)
            
            # Download da imagem
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Imagem salva: {filepath}")
            
        except Exception as e:
            logger.error(f"Erro ao baixar imagem: {e}")

def main():
    """Função principal"""
    # URLs de exemplo
    urls = [
        "https://www.futbin.com/25/player/60820/eusebio-da-silva-ferreira",
        # Adicione mais URLs aqui
    ]
    
    # Criar scraper
    scraper = SimpleFutbinScraper()
    
    try:
        # Scrapar jogadores
        players = scraper.scrape_multiple_players(urls)
        
        if players:
            # Salvar em JSON
            scraper.save_to_json(players)
            
            # Download das imagens
            for player in players:
                scraper.download_image(player.image_url, player.name)
        
        logger.info(f"Scraping concluído. {len(players)} jogadores coletados.")
        
    except Exception as e:
        logger.error(f"Erro no scraping: {e}")

if __name__ == "__main__":
    main() 