# 📊 Dota 2 Stats to Discord - OpenDota

This project fetches Dota 2 player stats from the [OpenDota API](https://www.opendota.com/) and posts a ranking in your Discord server using a webhook.  
It was made to track and have fun with the matches we play with friends in our Dota Discord.

## 🚀 Features

- Automatically fetches stats for your Dota squad.  
- Generates a ranking ordered by medal and winrate.  
- Highlights a **Top 3 leaderboard** with medals and stats.  
- Posts a **daily update** to your Discord channel (18:00 UTC).  
- Gives a **special mention** to the last place with funny phrases.  

## 📦 Requirements

- A repository on **GitHub**.  
- A **Discord Webhook** for the channel where you want to post the stats.  
- Your friends’ **Steam32 IDs** (you can find them at [SteamID.io](https://steamid.io/)).  

## ⚙️ Setup

### 1. Environment Variables

Go to your repository:

`Settings > Secrets and variables > Actions`

Add the following:

- **`DISCORD_WEBHOOK_URL`** → The Discord webhook URL.  
- **`PLAYERS`** → A JSON object with your friends’ Steam32 IDs mapped to their nicknames. Example:  

```json
{
  "123456754": "notail",
  "123456677": "miracle"
}
