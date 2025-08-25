import os
import requests
import json
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configuración
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STEAM_IDS = os.getenv('STEAM_IDS').split(',')  # Ahora usamos Steam ID 32
PLAYER_NAMES = os.getenv('PLAYER_NAMES', '').split(',')

# Mapeo de nombres si se proporcionan
if PLAYER_NAMES and len(PLAYER_NAMES) == len(STEAM_IDS):
    NAME_MAPPING = dict(zip(STEAM_IDS, PLAYER_NAMES))
else:
    NAME_MAPPING = {}

def get_opendota_player_info(steam_id_32):
    """Obtiene información del jugador de OpenDota API"""
    try:
        url = f"https://api.opendota.com/api/players/{steam_id_32}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Error HTTP {response.status_code} para Steam ID 32: {steam_id_32}")
            return None
            
    except Exception as e:
        logging.error(f"Error obteniendo datos de OpenDota: {e}")
        return None

def get_opendota_winloss(steam_id_32):
    """Obtiene estadísticas de wins/losses"""
    try:
        url = f"https://api.opendota.com/api/players/{steam_id_32}/wl"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Error HTTP {response.status_code} para stats de: {steam_id_32}")
            return None
            
    except Exception as e:
        logging.error(f"Error obteniendo stats W/L: {e}")
        return None

def get_opendota_rank(steam_id_32):
    """Obtiene información de ranking"""
    try:
        url = f"https://api.opendota.com/api/players/{steam_id_32}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('rank_tier'), data.get('leaderboard_rank')
        return None, None
            
    except Exception as e:
        logging.error(f"Error obteniendo rank: {e}")
        return None, None

def parse_rank_tier(rank_tier):
    """Convierte el rank_tier numérico a nombre de medalla"""
    if not rank_tier:
        return "No rank"
    
    rank_str = str(rank_tier)
    if len(rank_str) != 2:
        return "No rank"
    
    medal_level = int(rank_str[0])
    star_level = int(rank_str[1])
    
    medals = {
        1: "Heraldo",
        2: "Guardian", 
        3: "Crusader",
        4: "Archon",
        5: "Legend",
        6: "Ancient",
        7: "Divine",
        8: "Immortal"
    }
    
    medal_name = medals.get(medal_level, "Unknown")
    return f"{medal_name} {star_level}★"

def create_discord_message(players_data):
    """Crea el mensaje para Discord"""
    if not players_data:
        embed = {
            "title": "❌ Error al obtener estadísticas",
            "color": 16711680,
            "description": "No se pudieron obtener las estadísticas de OpenDota.",
            "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
        }
        return {"embeds": [embed]}
    
    # Ordenar por winrate descendente
    players_data.sort(key=lambda x: x.get('winrate', 0), reverse=True)
    
    embed = {
        "title": "🏆 Estadísticas de Dota 2 - OpenDota",
        "color": 3447003,  # Azul
        "thumbnail": {"url": "https://www.opendota.com/static/images/logos/opendota.png"},
        "fields": [],
        "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
    }
    
    for player in players_data:
        field_value = f"**Medalla:** {player.get('medal', 'No rank')}\n"
        field_value += f"**Partidas:** {player.get('total_matches', 0)}\n"
        field_value += f"**Victorias:** {player.get('wins', 0)}\n"
        field_value += f"**Derrotas:** {player.get('losses', 0)}\n"
        field_value += f"**Winrate:** {player.get('winrate', 0)}%"
        
        embed["fields"].append({
            "name": player['name'],
            "value": field_value,
            "inline": True
        })
    
    return {"embeds": [embed], "content": "📊 **Estadísticas del equipo - OpenDota API**"}

def main():
    logging.info("Iniciando obtención de estadísticas de OpenDota")
    
    players_data = []
    
    for steam_id_32 in STEAM_IDS:
        steam_id_32 = steam_id_32.strip()
        if not steam_id_32:
            continue
            
        logging.info(f"Procesando Steam ID 32: {steam_id_32}")
        
        # Obtener nombre del jugador
        player_name = NAME_MAPPING.get(steam_id_32, f"Jugador_{steam_id_32[-6:]}")
        
        # Obtener información de OpenDota
        player_info = get_opendota_player_info(steam_id_32)
        winloss_info = get_opendota_winloss(steam_id_32)
        rank_tier, leaderboard_rank = get_opendota_rank(steam_id_32)
        
        # Procesar datos
        wins = winloss_info.get('win', 0) if winloss_info else 0
        losses = winloss_info.get('lose', 0) if winloss_info else 0
        total_matches = wins + losses
        winrate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        # Parsear medalla
        medal = parse_rank_tier(rank_tier)
        if leaderboard_rank:
            medal = f"Inmortal Top {leaderboard_rank}"
        
        players_data.append({
            'name': player_name,
            'wins': wins,
            'losses': losses,
            'total_matches': total_matches,
            'winrate': round(winrate, 1),
            'medal': medal
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

