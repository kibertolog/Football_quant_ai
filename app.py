import streamlit as st
import pandas as pd
import requests
from rapidfuzz import process, fuzz

st.title("🔥 BETTING SYSTEM (REAL EDGE)")

# ======================
# SETTINGS
# ======================
MIN_EDGE = 0.03
MIN_VALUE = 0.05

# ======================
# API KEYS
# ======================
FOOTBALL_API_KEY = "87d5fc28e1e84206b1e48312563372b7"
ODDS_API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

# ======================
# NORMALIZE
# ======================
def normalize(name):
    name = name.lower()
    for r in ["fc", "cf", "club", "sc", "ac"]:
        name = name.replace(r, "")
    return name.strip()

# ======================
# FUZZY MATCH
# ======================
def fuzzy_match(team, team_list):
    match, score, _ = process.extractOne(
        normalize(team),
        team_list,
        scorer=fuzz.token_sort_ratio
    )
    return match if score > 70 else None

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
    return pd.read_csv(url)

df = load_data()

# ======================
# MODEL
# ======================
teams = {}

for _, row in df.iterrows():
    home = normalize(row["HomeTeam"])
    away = normalize(row["AwayTeam"])

    if home not in teams:
        teams[home] = {"g": 0, "n": 0}
    if away not in teams:
        teams[away] = {"g": 0, "n": 0}

    teams[home]["g"] += row["FTHG"]
    teams[home]["n"] += 1

    teams[away]["g"] += row["FTAG"]
    teams[away]["n"] += 1

team_list = list(teams.keys())

# ======================
# PREDICT
# ======================
def predict(h, a):
    if h not in teams or a not in teams:
        return None

    hp = teams[h]["g"] / teams[h]["n"]
    ap = teams[a]["g"] / teams[a]["n"]

    total = hp + ap
    return hp / total, ap / total

# ======================
# LIVE DATA
# ======================
def get_matches():
    try:
        url = "https://api.football-data.org/v4/matches"
        headers = {"X-Auth-Token": FOOTBALL_API_KEY}
        params = {"status": "SCHEDULED"}

        r = requests.get(url, headers=headers, params=params, timeout=5)
        if r.status_code != 200:
            return None

        return [
            {
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"]
            }
            for m in r.json()["matches"][:20]
        ]
    except:
        return None

def get_odds():
    try:
        url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h"
        }

        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            return None

        return r.json()
    except:
        return None

# ======================
# RUN
# ======================
matches = get_matches()
odds_data = get_odds()

if not matches or not odds_data:
    st.error("❌ NINCS LIVE ADAT → ellenőrizd az API kulcsokat")
    st.stop()

st.success("🟢 LIVE EDGE MODE")

found_bets = 0

for m in matches:
    home = m["home"]
    away = m["away"]

    h_map = fuzzy_match(home, team_list)
    a_map = fuzzy_match(away, team_list)

    if not h_map or not a_map:
        continue

    probs = predict(h_map, a_map)
    if not probs:
        continue

    home_p, away_p = probs

    # ODDS MATCH
    odds_match = None
    for o in odds_data:
        if home.lower() in o["home_team"].lower():
            odds_match = o
            break

    if not odds_match:
        continue

    try:
        outcomes = odds_match["bookmakers"][0]["markets"][0]["outcomes"]
        home_odds = outcomes[0]["price"]
        away_odds = outcomes[1]["price"]
    except:
        continue

    # IMPLIED PROB
    imp_home = 1 / home_odds
    imp_away = 1 / away_odds

    # EDGE
    edge_home = home_p - imp_home
    edge_away = away_p - imp_away

    # VALUE
    val_home = home_p * home_odds - 1
    val_away = away_p * away_odds - 1

    # FILTER
    if val_home > MIN_VALUE and edge_home > MIN_EDGE:
        found_bets += 1

        st.subheader(f"{home} vs {away}")
        st.write(f"📊 EDGE: {round(edge_home,3)} | VALUE: {round(val_home,3)}")
        st.success(f"👉 BET: {home}")

    elif val_away > MIN_VALUE and edge_away > MIN_EDGE:
        found_bets += 1

        st.subheader(f"{home} vs {away}")
        st.write(f"📊 EDGE: {round(edge_away,3)} | VALUE: {round(val_away,3)}")
        st.success(f"👉 BET: {away}")

if found_bets == 0:
    st.warning("⚠️ NINCS VALUE BET JELENLEG (EZ JÓ!)")