import os
import requests
import logging
from datetime import datetime

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

# Steam64 IDs de tus amigos
STEAM64_IDS = {
    "win": 76561199433152699,
    "Rayden": 76561199387357759,
    "chipi": 76561199406082220,
    "miguelo": 76561199302547911,
    "sunecko": 76561198873989123
}

def get_match_history(steam64, limit=20):
    """Obtiene el historial de partidas recientes usando la API Dev de Steam"""
    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/v1"
    params = {'key': STEAM_API_KEY, 'account_id': steam64, 'matches_requested': limit}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('result', {}).get('matches', [])
    except Exception as e:
        logging.error(f"Error obteniendo historial de {steam64}: {e}")
        return []

def get_match_details(match_id):
    """Obtiene detalles de la partida"""
    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1"
    params = {'key': STEAM_API_KEY, 'match_id': match_id}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get('result', {})
    except Exception as e:
        logging.error(f"Error obteniendo detalles de match {match_id}: {e}")
        return {}

def calculate_winrate(steam64, matches):
    """Calcula winrate basado en las partidas obtenidas"""
    wins = 0
    total = len(matches)
    for match in matches:
        details = get_match_details(match['match_id'])
        players = details.get('players', [])
        player = next((p for p in players if p['account_id'] == steam64), None)
        if not player:
            continue
        radiant_win = details.get('radiant_win')
        is_radiant = player['player_slot'] < 128
        if (is_radiant and radiant_win) or (not is_radiant and not radiant_win):
            wins += 1
    winrate = (wins / total * 100) if total else 0
    return wins, total, winrate

def create_discord_message(data):
    embed = {
        "title": "📊 Estadísticas Dota 2 (Steam Dev API)",
        "color": 5814783,
        "fields": [],
        "footer": {"text": f"Actualizado {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
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
    logging.info("Iniciando obtención de estadísticas de Dota 2 (Steam Dev API)")
    results = {}
    for name, s64 in STEAM64_IDS.items():
        logging.info(f"Procesando {name} ({s64})")
        matches = get_match_history(s64)
        if not matches:
            logging.warning(f"No se encontraron partidas para {name}")
            results[name] = {"wins": 0, "total": 0, "winrate": 0}
            continue
        wins, total, winrate = calculate_winrate(s64, matches)
        results[name] = {"wins": wins, "total": total, "winrate": winrate}
        logging.info(f"{name}: {wins}/{total} victorias ({winrate:.1f}%)")
    
    # Enviar mensaje a Discord
    message = create_discord_message(results)
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        if resp.status_code in [200, 204]:
            logging.info("Mensaje enviado correctamente a Discord")
        else:
            logging.error(f"Error enviando mensaje a Discord: {resp.status_code} - {resp.text}")
    except Exception as e:
        logging.error(f"Error al enviar mensaje a Discord: {e}")

if __name__ == "__main__":
    main()

