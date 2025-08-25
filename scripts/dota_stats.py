import os
import requests
import logging
from datetime import datetime

# Configuración
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Steam64 IDs de tus amigos
STEAM64_IDS = {
    "win": 76561199433152699,
    "Rayden": 76561199387357759,
    "chipi": 76561199406082220,
    "miguelo": 76561199302547911,
    "sunecko": 76561198873989123
}

def steam64_to_steam32(s64):
    return s64 - 76561197960265728

def get_match_history(steam32):
    url = f"https://api.steampowered.com/IDOTA2Match_205790/GetMatchHistory/v1"
    params = {'key': STEAM_API_KEY, 'account_id': steam32}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get('result', {}).get('matches', [])

def get_match_details(match_id):
    url = f"https://api.steampowered.com/IDOTA2Match_205790/GetMatchDetails/v1"
    params = {'key': STEAM_API_KEY, 'match_id': match_id}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get('result', {})

def calculate_winrate(steam32, matches):
    wins = 0
    total = len(matches)
    for m in matches[:20]:  # Limitar procesado (últimas 20)
        details = get_match_details(m['match_id'])
        player_slot = next(p for p in details.get('players', []) if p['account_id'] == steam32)
        radiant_win = details.get('radiant_win')
        is_radiant = player_slot['player_slot'] < 128
        if (is_radiant and radiant_win) or (not is_radiant and not radiant_win):
            wins += 1
    return wins, total, (wins / total * 100) if total else 0

def create_discord_message(data):
    embed = {
        "title": "📊 Estadísticas Dota 2 (Dev API)",
        "color": 5814783,
        "fields": [],
        "footer": { "text": f"Actualizado {datetime.now().strftime('%Y-%m-%d %H:%M')}" }
    }
    for name, stats in data.items():
        v = (
            f"Partidas procesadas: {stats['total']}\n"
            f"Victorias: {stats['wins']}\n"
            f"Winrate: {stats['winrate']:.1f}%"
        )
        embed["fields"].append({"name": name, "value": v, "inline": True})
    return {"embeds": [embed]}

def main():
    logging.basicConfig(level=logging.INFO)
    results = {}
    for name, s64 in STEAM64_IDS.items():
        steam32 = steam64_to_steam32(s64)
        matches = get_match_history(steam32)
        wins, total, winrate = calculate_winrate(steam32, matches)
        results[name] = {"wins": wins, "total": total, "winrate": winrate}
    msg = create_discord_message(results)
    requests.post(DISCORD_WEBHOOK_URL, json=msg, timeout=10)

if __name__=="__main__":
    main()
