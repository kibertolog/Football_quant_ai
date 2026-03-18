import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ==============================
# API KEYS
# ==============================
FOOTBALL_API_KEY = "87d5fc28e1e84206b1e48312563372b7"
ODDS_API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

# ==============================
# LOAD HISTORICAL DATA (TRAIN)
# ==============================
@st.cache_data
def load_data():
    urls = [
        "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
        "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
        "https://www.football-data.co.uk/mmz4281/2324/I1.csv"
    ]
    df_list = [pd.read_csv(url) for url in urls]
    df = pd.concat(df_list)
    return df

# ==============================
# TRAIN MODEL (VERY SIMPLE)
# ==============================
def train_model(df):
    df = df.dropna(subset=["FTHG", "FTAG"])

    teams = {}

    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]

        if home not in teams:
            teams[home] = {"scored": 0, "conceded": 0, "games": 0}
        if away not in teams:
            teams[away] = {"scored": 0, "conceded": 0, "games": 0}

        teams[home]["scored"] += row["FTHG"]
        teams[home]["conceded"] += row["FTAG"]
        teams[home]["games"] += 1

        teams[away]["scored"] += row["FTAG"]
        teams[away]["conceded"] += row["FTHG"]
        teams[away]["games"] += 1

    return teams

# ==============================
# GET FIXTURES (UPCOMING MATCHES)
# ==============================
def get_fixtures():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    params = {
        "status": "SCHEDULED"
    }

    res = requests.get(url, headers=headers, params=params)
    data = res.json()

    matches = []

    for m in data["matches"]:
        matches.append({
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"],
            "date": m["utcDate"]
        })

    return matches

# ==============================
# GET ODDS
# ==============================
def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    res = requests.get(url, params=params)
    data = res.json()

    odds_dict = {}

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        try:
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            odds_dict[(home, away)] = {
                outcomes[0]["name"]: outcomes[0]["price"],
                outcomes[1]["name"]: outcomes[1]["price"]
            }
        except:
            continue

    return odds_dict

# ==============================
# PREDICT
# ==============================
def predict(home, away, teams):
    if home not in teams or away not in teams:
        return None

    h = teams[home]
    a = teams[away]

    home_strength = h["scored"] / h["games"]
    away_strength = a["scored"] / a["games"]

    total = home_strength + away_strength

    home_prob = home_strength / total
    away_prob = away_strength / total

    return home_prob, away_prob

# ==============================
# STREAMLIT UI
# ==============================
st.title("🔥 BETTING SYSTEM (LIVE AI)")

df = load_data()
teams = train_model(df)

fixtures = get_fixtures()
odds = get_odds()

for match in fixtures:
    home = match["home"]
    away = match["away"]

    if (home, away) not in odds:
        continue

    probs = predict(home, away, teams)
    if not probs:
        continue

    home_prob, away_prob = probs

    home_odds = odds[(home, away)].get(home)
    away_odds = odds[(home, away)].get(away)

    if not home_odds or not away_odds:
        continue

    home_value = home_prob * home_odds - 1
    away_value = away_prob * away_odds - 1

    if home_value > 0.07 or away_value > 0.07:
        st.subheader(f"{home} vs {away}")
        st.write(f"Home %: {round(home_prob,2)} | Away %: {round(away_prob,2)}")
        st.write(f"Home value: {round(home_value,2)} | Away value: {round(away_value,2)}")

        if home_value > away_value:
            st.success(f"👉 TIPP: {home}")
        else:
            st.success(f"👉 TIPP: {away}")