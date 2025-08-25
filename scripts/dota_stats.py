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
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Tus amigos en formato Steam32 ID
PLAYERS = {
    "win": 1168439971,
    "Rayden": 1220652031,
    "chipi": 1166030492,
    "miguelo": 1122906683,
    "sunecko": 76561198873989123,
}

# Mapeo de medallas
RANKS = {
    1: "Herald", 2: "Guardian", 3: "Crusader",
    4: "Archon", 5: "Legend", 6: "Ancient",
    7: "Divine", 8: "Immortal"
}

def get_player_stats(account_id):
    """Obtiene perfil y win/loss de OpenDota"""
    try:
        # Perfil (rank, mmr, nombre)
        profile_resp = requests.get(f"https://api.opendota.com/api/players/{account_id}", timeout=10)
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        # Win/loss
        wl_resp = requests.get(f"https://api.opendota.com/api/players/{account_id}/wl", timeout=10)
        wl_resp.raise_for_status()
        wl = wl_resp.json()

        wins = wl.get("win", 0)
        losses = wl.get("lose", 0)
        total = wins + losses
        winrate = (wins / total * 100) if total > 0 else 0

        # Rank tier
        rank_tier = profile.get("rank_tier")
        if rank_tier:
            rank_digit = int(str(rank_tier)[0])   # Ej: 6 → Ancient
            star = int(str(rank_tier)[1])         # Ej: 3 → III
            rank_name = f"{RANKS.get(rank_digit, 'Uncalibrated')} {star}"
        else:
            rank_name = "Uncalibrated"

        return {
            "name": profile.get("profile", {}).get("personaname", "Unknown"),
            "rank": rank_name,
            "mmr_estimate": profile.get("mmr_estimate", {}).get("estimate", "N/A"),
            "wins": wins,
            "losses": losses,
            "winrate": f"{winrate:.1f}"
        }

    except Exception as e:
        logging.error(f"Error obteniendo stats de {account_id}: {e}")
        return None

def create_discord_message(players_data):
    """Crea embed de Discord"""
    embed = {
        "title": "🏆 Estadísticas de Dota 2",
        "color": 5814783,
        "thumbnail": {
            "url": "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota2_social.jpg"
        },
        "fields": [],
        "footer": {
            "text": f"Actualizado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
    }

    for nickname, data in players_data.items():
        if not data:
            continue

        field_value = (
            f"**Medalla:** {data['rank']}\n"
            f"**MMR estimado:** {data['mmr_estimate']}\n"
            f"**Partidas:** {data['wins'] + data['losses']}\n"
            f"**Winrate:** {data['winrate']}%"
        )

        embed["fields"].append({
            "name": f"{nickname} ({data['name']})",
            "value": field_value,
            "inline": True
        })

    return {"embeds": [embed], "content": "📊 **Estadísticas diarias de Dota 2**"}

def main():
    logging.info("Iniciando obtención de estadísticas de Dota 2")

    players_data = {}
    for nickname, account_id in PLAYERS.items():
        logging.info(f"Procesando {nickname} ({account_id})")
        stats = get_player_stats(account_id)
        players_data[nickname] = stats

    # Crear embed
    message = create_discord_message(players_data)

    # Enviar a Discord
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        if resp.status_code in [200, 204]:
            logging.info("✅ Mensaje enviado correctamente a Discord")
        else:
            logging.error(f"❌ Error al enviar mensaje: {resp.status_code} - {resp.text}")
    except Exception as e:
        logging.error(f"❌ Error en la solicitud a Discord: {e}")

if __name__ == "__main__":
    main()

