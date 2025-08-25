import os
import requests
import json
from datetime import datetime

# Configuración
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STEAM_IDS = os.getenv('STEAM_IDS').split(',')

def get_steam_id(steam_id):
    """Obtiene el SteamID64 a partir de cualquier formato de SteamID"""
    if isinstance(steam_id, int) or steam_id.isdigit():
        # Asumimos que ya es un SteamID64
        return str(steam_id)
    else:
        # Para IDs personalizados, necesitarías la API de Steam
        # Esta es una implementación simplificada
        url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        params = {
            'key': STEAM_API_KEY,
            'vanityurl': steam_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data['response']['success'] == 1:
            return data['response']['steamid']
        else:
            return None

def get_player_summaries(steam_id):
    """Obtiene información básica del jugador"""
    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {
        'key': STEAM_API_KEY,
        'steamids': steam_id
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data['response']['players'][0] if data['response']['players'] else None

def get_dota_stats(steam_id):
    """Obtiene estadísticas de Dota 2 (ejemplo simplificado)"""
    # Nota: La API de Dota 2 es más compleja y requiere endpoints específicos
    # Esta es una implementación de ejemplo
    url = "https://api.steampowered.com/IEconDOTA2_570/GetPlayerSummaries/v0001/"
    params = {
        'key': STEAM_API_KEY,
        'steamid': steam_id
    }
    response = requests.get(url, params=params)
    return response.json()

def create_discord_message(players_data):
    """Crea el mensaje embellecido para Discord"""
    # Crear un embed de Discord
    embed = {
        "title": "🏆 Estadísticas Diarias de Dota 2",
        "color": 5814783,
        "thumbnail": {
            "url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota2_social.jpg"
        },
        "fields": [],
        "footer": {
            "text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
    }
    
    for player in players_data:
        # Formatear la información del jugador
        field_value = f"**Medalla:** {player.get('medal', 'No disponible')}\n"
        field_value += f"**Partidas:** {player.get('matches', 'N/A')}\n"
        field_value += f"**Winrate:** {player.get('winrate', 'N/A')}%"
        
        embed["fields"].append({
            "name": player['personaname'],
            "value": field_value,
            "inline": True
        })
    
    return {"embeds": [embed]}

def main():
    players_data = []
    
    for steam_id in STEAM_IDS:
        
        valid_steam_id = get_steam_id(steam_id.strip())
        if not valid_steam_id:
            print(f"Error: No se pudo obtener el SteamID para {steam_id}")
            continue
        
        # Obtener información del jugador
        player_summary = get_player_summaries(valid_steam_id)
        if not player_summary:
            print(f"Error: No se pudo obtener información para SteamID {valid_steam_id}")
            continue
        
        # Obtener estadísticas de Dota (aquí simplificado)
        dota_stats = get_dota_stats(valid_steam_id)
        
        # En un caso real, procesarías las estadísticas reales de la API de Dota 2
        players_data.append({
            'personaname': player_summary['personaname'],
            'medal': 'Arconte',  # Esto sería obtenido de la API real
            'matches': 42,       # Esto sería obtenido de la API real
            'winrate': 58.7      # Esto sería obtenido de la API real
        })
    
    # Crear y enviar mensaje a Discord
    message = create_discord_message(players_data)
    response = requests.post(DISCORD_WEBHOOK_URL, json=message)
    
    if response.status_code == 204:
        print("Mensaje enviado correctamente a Discord")
    else:
        print(f"Error al enviar mensaje: {response.status_code}")

if __name__ == "__main__":
    main()