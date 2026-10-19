import os
import time
from collections import deque

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")

HEADERS = {"X-Riot-Token": API_KEY}

# Development key limits: 20 requests / 1s and 100 requests / 120s.
# Override via env vars if you get a personal/production key.
RATE_LIMITS = [
    (int(os.getenv("RIOT_LIMIT_SHORT", 20)), 1.0),
    (int(os.getenv("RIOT_LIMIT_LONG", 100)), 120.0),
]


class RateLimiter:
    """Sliding-window limiter that waits *before* a request instead of after a 429."""

    def __init__(self, limits):
        self.limits = limits
        self.history = deque()
        self.max_window = max(w for _, w in limits)

    def wait(self):
        while True:
            now = time.monotonic()
            while self.history and now - self.history[0] > self.max_window:
                self.history.popleft()
            sleep_for = 0.0
            for max_calls, window in self.limits:
                recent = [t for t in self.history if now - t < window]
                if len(recent) >= max_calls:
                    sleep_for = max(sleep_for, window - (now - recent[0]) + 0.05)
            if sleep_for <= 0:
                self.history.append(now)
                return
            time.sleep(sleep_for)


_limiter = RateLimiter(RATE_LIMITS)


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        _limiter.wait()
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                print(f"Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
            elif response.status_code == 404:
                return None
            elif response.status_code in (401, 403):
                raise RuntimeError(
                    f"Riot API returned {response.status_code}. Your RIOT_API_KEY is "
                    "missing or expired (dev keys expire every 24h)."
                )
            else:
                print(f"Error {response.status_code}: {response.url}")
                time.sleep(2)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
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


def get_match_ids(puuid, region="americas", count=20, start=0,
                  start_time=None, end_time=None):
    """Get ranked TFT match IDs for a player, optionally within an epoch-seconds window."""
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
    params = {"count": count, "start": start, "queue": 1100}
    if start_time is not None:
        params["startTime"] = int(start_time)
    if end_time is not None:
        params["endTime"] = int(end_time)
    return _get(url, params=params) or []


def get_match(match_id, region="americas"):
    """Fetch full match data by match ID."""
    url = f"https://{region}.api.riotgames.com/tft/match/v1/matches/{match_id}"
    return _get(url)
