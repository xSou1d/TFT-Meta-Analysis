import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")

HEADERS = {"X-Riot-Token": API_KEY}

def _get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
            elif response.status_code == 404:
                return None
            else:
                print(f"Error {response.status_code}: {response.url}")
                time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f"Connection error on attempt {attempt + 1}. Retrying in 10s...")
            time.sleep(10)
    return None

def get_challenger_players(region="na1"):
    """Fetch Challenger ladder for TFT."""
    url = f"https://{region}.api.riotgames.com/tft/league/v1/challenger"
    return _get(url)

def get_grandmaster_players(region="na1"):
    """Fetch Grandmaster ladder for TFT."""
    url = f"https://{region}.api.riotgames.com/tft/league/v1/grandmaster"
    return _get(url)

def get_puuid(summoner_id, region="na1"):
    """Get PUUID from summonerID."""
    url = f"https://{region}.api.riotgames.com/tft/summoner/v1/summoners/{summoner_id}"
    data = _get(url)
    return data["puuid"] if data else None

def get_match_ids(puuid, region="americas", count=20):
    """Get recent ranked TFT match IDs for a player."""
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
    params = {"count": count, "queue": 1100}
    return _get(url, params=params) or []

def get_match(match_id, region="americas"):
    """Fetch full match data by match ID."""
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/{match_id}"
    return _get(url)