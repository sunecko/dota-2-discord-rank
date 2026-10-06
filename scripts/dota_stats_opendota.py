import os
import requests
import json
from datetime import datetime
from itertools import groupby
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

# Primer dígito del rank_tier de OpenDota -> (icono, nombre)
MEDALS = {
    8: ("👑", "Immortal"),
    7: ("💎", "Divine"),
    6: ("🏛️", "Ancient"),
    5: ("🦁", "Legend"),
    4: ("🛡️", "Archon"),
    3: ("⚔️", "Crusader"),
    2: ("🪖", "Guardian"),
    1: ("🔰", "Heraldo"),
    0: ("❔", "Sin rango")
}

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

def get_opendota_winloss(steam_id_32, days=None):
    try:
        url = f"https://api.opendota.com/api/players/{steam_id_32}/wl"
        params = {"date": days} if days else None
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Error HTTP {response.status_code} para stats de: {steam_id_32}")
            return None

    except Exception as e:
        logging.error(f"Error obteniendo stats W/L: {e}")
        return None

def format_rank(player):
    if player['leaderboard_rank']:
        return f"#{player['leaderboard_rank']}"

    stars = player['rank_tier'] % 10
    return f"{stars}★" if stars else "—"

def format_player_line(player, is_last):
    prefix = "💩 " if is_last else ""

    if player['total_matches'] == 0:
        stats = "🔒 perfil privado"
    else:
        week_matches = player['week_wins'] + player['week_losses']
        week = f"{player['week_wins']}W-{player['week_losses']}L" if week_matches else "sin jugar"
        stats = f"{player['winrate']}% · semana {week}"

    return f"{prefix}**{player['name']}** · {format_rank(player)} · {stats}"

def create_discord_message(players_data):
    if not players_data:
        embed = {
            "title": "❌ Error al obtener estadísticas",
            "color": 16711680,
            "description": "No se pudieron obtener las estadísticas de OpenDota.",
            "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
        }
        return {"embeds": [embed]}

    # Medalla y estrellas, luego puesto en el leaderboard (menor es mejor), luego winrate
    players_data.sort(
        key=lambda p: (p['rank_tier'], -(p['leaderboard_rank'] or float('inf')), p['winrate']),
        reverse=True
    )

    last_place = players_data[-1]

    embed = {
        "title": "🏆 Ranking Secret Force",
        "color": 15844367,  # Oro
        "thumbnail": {"url": "https://riki.dotabuff.com/t/l/12wFjEZJmK.png"},
        "fields": [],
        "footer": {"text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · Próxima actualización: el lunes que viene"}
    }

    for medal_level, group in groupby(players_data, key=lambda p: p['rank_tier'] // 10):
        icon, medal_name = MEDALS.get(medal_level, MEDALS[0])
        lines = [format_player_line(player, player is last_place) for player in group]
        embed["fields"].append({
            "name": f"{icon} {medal_name}",
            "value": "\n".join(lines),
            "inline": False
        })

    embed["fields"].append({
        "name": "😅 Mención Especial",
        "value": f"**{last_place['name']}** — {random.choice(FUNNY_PHRASES)}",
        "inline": False
    })

    return {"embeds": [embed], "content": "📈 **RANKING SEMANAL SECRET FORCE**\n¡El ultimo en llegar a inmortal es gay 🏳️‍🌈! 🎮 @everyone "}

def main():
    logging.info("Iniciando obtención de estadísticas de OpenDota")

    players_data = []

    for steam_id_32, player_name in PLAYERS.items():
        logging.info(f"Procesando {player_name} (ID: {steam_id_32})")

        player_info = get_opendota_player_info(steam_id_32) or {}
        winloss_info = get_opendota_winloss(steam_id_32) or {}
        week_info = get_opendota_winloss(steam_id_32, days=7) or {}

        wins = winloss_info.get('win', 0)
        losses = winloss_info.get('lose', 0)
        total_matches = wins + losses
        winrate = (wins / total_matches * 100) if total_matches > 0 else 0

        players_data.append({
            'name': player_name,
            'wins': wins,
            'losses': losses,
            'total_matches': total_matches,
            'winrate': round(winrate, 1),
            'week_wins': week_info.get('win', 0),
            'week_losses': week_info.get('lose', 0),
            'rank_tier': player_info.get('rank_tier') or 0,
            'leaderboard_rank': player_info.get('leaderboard_rank'),
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
