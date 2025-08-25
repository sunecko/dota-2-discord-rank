import os
import requests
import json
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import time
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dota_stats.log'),
        logging.StreamHandler()
    ]
)

# Configuración
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STEAM_IDS = os.getenv('STEAM_IDS').split(',')

# Constante para conversión de Steam ID
STEAM_ID64_BASE = 76561197960265728

def get_steam_id_32(steam_id_64):
    """Convierte Steam ID 64 a Steam ID 32 (account_id)"""
    try:
        return int(steam_id_64) - STEAM_ID64_BASE
    except (ValueError, TypeError):
        logging.error(f"Error convirtiendo Steam ID: {steam_id_64}")
        return None

def get_player_name(steam_id_64):
    """Obtiene el nombre del jugador desde Steam API (opcional)"""
    # Si no tienes API key de Steam, usarás solo los IDs
    return f"Jugador_{steam_id_64[-8:]}"

def scrape_dotabuff_basic(steam_id_32):
    """Obtiene solo medalla y win rate de Dotabuff"""
    try:
        url = f"https://www.dotabuff.com/players/{steam_id_32}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Esperar un tiempo aleatorio para evitar detección
        time.sleep(random.uniform(2, 4))
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {'steam_id_32': steam_id_32}
            
            # Obtener medalla/ranking
            medal_elem = soup.find('div', class_='rank-tier')
            if medal_elem:
                medal_title = medal_elem.get('title', '')
                if 'Rank: ' in medal_title:
                    stats['medal'] = medal_title.replace('Rank: ', '')
                else:
                    stats['medal'] = medal_title
            
            # Obtener winrate
            winrate_elem = soup.find('div', class_='header-content-secondary')
            if winrate_elem:
                winrate_text = winrate_elem.text.strip()
                if 'Win Rate' in winrate_text:
                    # Extraer el porcentaje de winrate
                    lines = winrate_text.split('\n')
                    for line in lines:
                        if '%' in line and 'Win Rate' in line:
                            stats['winrate'] = line.split('Win Rate')[-1].strip()
                            break
            
            return stats
            
        elif response.status_code == 404:
            logging.warning(f"Perfil de Dotabuff no encontrado: {steam_id_32}")
            return None
        elif response.status_code == 429:
            logging.warning("Demasiadas solicitudes - Rate limiting")
            return None
        else:
            logging.warning(f"Error HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error scraping Dotabuff: {e}")
        return None

def create_discord_message(players_data):
    """Crea el mensaje para Discord con datos básicos"""
    if not players_data:
        embed = {
            "title": "❌ Error al obtener estadísticas",
            "color": 16711680,
            "description": "No se pudieron obtener las estadísticas de Dotabuff.",
            "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
        }
        return {"embeds": [embed]}
    
    embed = {
        "title": "🏆 Estadísticas Básicas de Dota 2",
        "color": 5814783,
        "thumbnail": {"url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota2_social.jpg"},
        "fields": [],
        "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
    }
    
    for player in players_data:
        medal = player.get('medal', 'No disponible')
        winrate = player.get('winrate', 'N/A')
        
        field_value = f"**Medalla:** {medal}\n"
        field_value += f"**Win Rate:** {winrate}"
        
        embed["fields"].append({
            "name": player['name'],
            "value": field_value,
            "inline": True
        })
    
    return {"embeds": [embed], "content": "📊 **Estadísticas básicas del equipo**"}

def main():
    logging.info("Iniciando obtención de estadísticas básicas de Dotabuff")
    
    players_data = []
    
    for steam_id in STEAM_IDS:
        steam_id = steam_id.strip()
        if not steam_id:
            continue
            
        logging.info(f"Procesando SteamID: {steam_id}")
        
        # Convertir a Steam ID 32 para Dotabuff
        steam_id_32 = get_steam_id_32(steam_id)
        if not steam_id_32:
            continue
        
        # Obtener nombre del jugador
        player_name = get_player_name(steam_id)
        
        # Obtener estadísticas de Dotabuff
        dotabuff_stats = scrape_dotabuff_basic(steam_id_32)
        
        if dotabuff_stats:
            players_data.append({
                'name': player_name,
                'medal': dotabuff_stats.get('medal', 'No disponible'),
                'winrate': dotabuff_stats.get('winrate', 'N/A')
            })
        else:
            # Si no se pueden obtener datos, agregar información básica
            players_data.append({
                'name': player_name,
                'medal': 'No disponible',
                'winrate': 'N/A'
            })
        
        # Esperar entre solicitudes para evitar rate limiting
        time.sleep(1)
    
    # Crear y enviar mensaje a Discord
    message = create_discord_message(players_data)
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        if response.status_code in [200, 204]:
            logging.info("Mensaje enviado correctamente a Discord")
        else:
            logging.error(f"Error al enviar mensaje: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error en la solicitud a Discord: {e}")

if __name__ == "__main__":
    main()
