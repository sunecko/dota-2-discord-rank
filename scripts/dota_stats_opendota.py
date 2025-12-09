import os
import requests
import json
from datetime import datetime
import logging
import time
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

PLAYERS = json.loads(os.getenv("PLAYERS"))

FUNNY_PHRASES = [
    "🏆 Rey del Tutorial - ¡Sigue intentándolo!",
    "💩 Especialista en alimentar al equipo enemigo",
    "😴 Profesional del afk farming",
    "🎯 Precisión legendaria... para fallar spells",
    "🚑 Récord mundial en viajes a la fountain",
    "🍗 Chef especializado en feed",
    "🌪️ Maestro del throw épico",
    "👻 Fantasma en las teamfights",
    "🏳️‍🌈 Culidefondado"
]

def get_opendota_player_info(steam_id_32):
    try:
        url = f"https://api.opendota.com/api/players/{steam_id_32}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Error HTTP {response.status_code} para {steam_id_32}")
            return None
            
    except Exception as e:
        logging.error(f"Error obteniendo datos de OpenDota: {e}")
        return None

def get_opendota_winloss(steam_id_32):
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

def parse_rank_tier(rank_tier):
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

def get_medal_value(medal_name):
    medal_order = {
        "Immortal": 8,
        "Divine": 7,
        "Ancient": 6,
        "Legend": 5,
        "Archon": 4,
        "Crusader": 3,
        "Guardian": 2,
        "Heraldo": 1,
        "No rank": 0
    }
    
    for medal_key in medal_order:
        if medal_key in medal_name:
            return medal_order[medal_key]
    return 0

def create_discord_message(players_data):
    if not players_data:
        embed = {
            "title": "❌ Error al obtener estadísticas",
            "color": 16711680,
            "description": "No se pudieron obtener las estadísticas de OpenDota.",
            "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
        }
        return {"embeds": [embed]}
    
    players_data.sort(key=lambda x: (get_medal_value(x.get('medal', 'No rank')), x.get('winrate', 0)), reverse=True)
    
    last_place = players_data[-1] if players_data else None
    funny_phrase = random.choice(FUNNY_PHRASES) if last_place else ""
    
    embeds = []
    
    top_embed = {
        "title": "🏆 TOP 3 - Ranking Secret Force",
        "color": 15844367,  # Oro
        "thumbnail": {"url": "https://riki.dotabuff.com/t/l/12wFjEZJmK.png"},
        "description": "",
        "fields": [],
        "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
    }
    
    position_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "💩"]
    
    for i, player in enumerate(players_data[:3]):
        emoji = position_emojis[i]
        top_embed["fields"].append({
            "name": f"{emoji} {player['name']} - {player.get('medal', 'No rank')}",
            "value": f"**Winrate:** {player.get('winrate', 0)}% | **W/L:** {player.get('wins', 0)}/{player.get('losses', 0)} | **Partidas:** {player.get('total_matches', 0)}",
            "inline": False
        })
    
    embeds.append(top_embed)
    
    if len(players_data) > 3:
        rest_embed = {
            "title": "📊 Resto del Equipo",
            "color": 3447003,
            "fields": [],
            "footer": {"text": "Siguiente actualización: Mañana a las 18:00"}
        }
        
        for i, player in enumerate(players_data[3:], 3):
            emoji = position_emojis[i] if i < len(position_emojis) else "🔹"
            rest_embed["fields"].append({
                "name": f"{emoji} {player['name']} - {player.get('medal', 'No rank')}",
                "value": f"**WR:** {player.get('winrate', 0)}% | **W/L:** {player.get('wins', 0)}/{player.get('losses', 0)} | **Total:** {player.get('total_matches', 0)}",
                "inline": False
            })
        
        embeds.append(rest_embed)
    
    if last_place:
        last_embed = {
            "title": "😅 Mención Especial",
            "color": 15105570,  
            "description": f"**{last_place['name']}** - {funny_phrase}",
            "fields": [{
                "name": "🏆 Estadísticas del Campeón",
                "value": f"**Medalla:** {last_place.get('medal', 'No rank')}\n**Winrate:** {last_place.get('winrate', 0)}%\n**Récord:** {last_place.get('wins', 0)}W - {last_place.get('losses', 0)}L\n**Total:** {last_place.get('total_matches', 0)} partidas",
                "inline": False
            }],
            "footer": {"text": "¡Ánimo, la próxima será mejor! 💪"}
        }
        embeds.append(last_embed)
    
    return {"embeds": embeds, "content": "📈 **RANKING SEMANAL SECRET FORCE**\n¡El ultimo en llegar a inmortal es gay 🏳️‍🌈! 🎮 @everyone "}

def main():
    logging.info("Iniciando obtención de estadísticas de OpenDota")
    
    players_data = []
    
    for steam_id_32, player_name in PLAYERS.items():
        logging.info(f"Procesando {player_name} (ID: {steam_id_32})")
        
        player_info = get_opendota_player_info(steam_id_32)
        winloss_info = get_opendota_winloss(steam_id_32)
        
        wins = winloss_info.get('win', 0) if winloss_info else 0
        losses = winloss_info.get('lose', 0) if winloss_info else 0
        total_matches = wins + losses
        winrate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        rank_tier = player_info.get('rank_tier') if player_info else None
        medal = parse_rank_tier(rank_tier)
        
        leaderboard_rank = player_info.get('leaderboard_rank') if player_info else None
        if leaderboard_rank:
            medal = f"Immortal Top {leaderboard_rank}"
        
        players_data.append({
            'name': player_name,
            'wins': wins,
            'losses': losses,
            'total_matches': total_matches,
            'winrate': round(winrate, 1),
            'medal': medal,
            'steam_id': steam_id_32
        })
        
        time.sleep(1)
    
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




