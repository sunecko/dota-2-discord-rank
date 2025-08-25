import os
import requests
import json
from datetime import datetime, timedelta
import logging

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
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STEAM_IDS = os.getenv('STEAM_IDS').split(',')

def get_steam_id(steam_id):
    """Obtiene el SteamID64"""
    try:
        if isinstance(steam_id, int) or steam_id.isdigit():
            return str(steam_id)
        else:
            url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
            params = {
                'key': STEAM_API_KEY,
                'vanityurl': steam_id
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data['response']['success'] == 1:
                return data['response']['steamid']
            else:
                logging.error(f"No se pudo resolver el SteamID para: {steam_id}")
                return None
    except Exception as e:
        logging.error(f"Error obteniendo SteamID: {e}")
        return None

def get_player_summaries(steam_id):
    """Obtiene información básica del jugador"""
    try:
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {
            'key': STEAM_API_KEY,
            'steamids': steam_id
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['response']['players'][0] if data['response']['players'] else None
    except Exception as e:
        logging.error(f"Error obteniendo resumen del jugador: {e}")
        return None

def get_dota2_player_info(steam_id):
    """Obtiene información específica de Dota 2 del jugador"""
    try:
        url = "https://api.steampowered.com/IEconDOTA2_570/GetPlayerOfficialInfo/v1/"
        params = {
            'key': STEAM_API_KEY,
            'steamid': steam_id
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # Algunas respuestas pueden estar vacías para jugadores sin datos
        if response.text.strip():
            return response.json()
        else:
            return {}
    except Exception as e:
        logging.error(f"Error obteniendo info de Dota 2: {e}")
        return {}

def get_dota2_medal_info(steam_id):
    """Obtiene información de medallas y ranking (usando endpoint alternativo)"""
    try:
        # Este es un endpoint no oficial pero ampliamente usado
        # La API oficial no expone fácilmente las medallas
        url = f"https://api.opendota.com/api/players/{steam_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        if response.text.strip():
            data = response.json()
            return data
        else:
            return {}
    except Exception as e:
        logging.warning(f"No se pudo obtener info de medalla: {e}")
        return {}

def get_win_loss_stats(steam_id):
    """Obtiene estadísticas de wins/losses"""
    try:
        url = "https://api.steampowered.com/IDOTA2Match_570/GetWinLossStats/v1/"
        params = {
            'key': STEAM_API_KEY,
            'steamid': steam_id
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        if response.text.strip():
            return response.json()
        else:
            return {}
    except Exception as e:
        logging.error(f"Error obteniendo stats W/L: {e}")
        return {}

def create_discord_message(players_data):
    """Crea el mensaje para Discord"""
    if not players_data:
        embed = {
            "title": "❌ Error al obtener estadísticas de Dota 2",
            "color": 16711680,  # Rojo
            "description": "No se pudieron obtener las estadísticas. Verifica la configuración.",
            "footer": {
                "text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            }
        }
        return {"embeds": [embed]}
    
    embed = {
        "title": "🏆 Estadísticas de Dota 2",
        "color": 5814783,  # Púrpura
        "thumbnail": {
            "url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota2_social.jpg"
        },
        "fields": [],
        "footer": {
            "text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
    }
    
    for player in players_data:
        field_value = f"**Medalla:** {player.get('medal', 'No disponible')}\n"
        field_value += f"**Nivel:** {player.get('level', 'N/A')}\n"
        field_value += f"**Partidas:** {player.get('matches', 'N/A')}\n"
        field_value += f"**Winrate:** {player.get('winrate', 'N/A')}%"
        
        embed["fields"].append({
            "name": player['personaname'],
            "value": field_value,
            "inline": True
        })
    
    return {"embeds": [embed], "content": "📊 **Estadísticas diarias de Dota 2**"}

def main():
    logging.info("Iniciando obtención de estadísticas de Dota 2")
    
    players_data = []
    
    for steam_id in STEAM_IDS:
        steam_id = steam_id.strip()
        if not steam_id:
            continue
            
        logging.info(f"Procesando SteamID: {steam_id}")
        
        # Obtener ID de Steam válido
        valid_steam_id = get_steam_id(steam_id)
        if not valid_steam_id:
            logging.error(f"SteamID inválido: {steam_id}")
            continue
        
        # Obtener información del jugador
        player_summary = get_player_summaries(valid_steam_id)
        if not player_summary:
            logging.error(f"No se pudo obtener info para SteamID: {valid_steam_id}")
            continue
        
        # Obtener información de Dota 2
        dota_info = get_dota2_player_info(valid_steam_id)
        medal_info = get_dota2_medal_info(valid_steam_id)
        win_loss_info = get_win_loss_stats(valid_steam_id)
        
        # Procesar datos
        medal = "Desconocida"
        if medal_info and 'rank_tier' in medal_info:
            rank = medal_info['rank_tier']
            if rank:
                division = str(rank)[-1] if len(str(rank)) > 1 else "1"
                stars = str(rank)[0] if len(str(rank)) > 1 else str(rank)
                medal = f"Heraldo {stars} estrellas (Div {division})"
        
        # Calcular winrate si hay datos disponibles
        winrate = "N/A"
        if win_loss_info and 'win_loss_stats' in win_loss_info:
            wins = win_loss_info['win_loss_stats'].get('wins', 0)
            losses = win_loss_info['win_loss_stats'].get('losses', 0)
            total = wins + losses
            if total > 0:
                winrate = f"{(wins/total)*100:.1f}"
        
        players_data.append({
            'personaname': player_summary.get('personaname', 'Jugador'),
            'medal': medal,
            'level': medal_info.get('profile', {}).get('level', 'N/A'),
            'matches': medal_info.get('profile', {}).get('games', 'N/A'),
            'winrate': winrate
        })
    
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