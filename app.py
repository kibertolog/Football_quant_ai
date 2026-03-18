import streamlit as st
import pandas as pd
import requests

st.title("🔥 BETTING SYSTEM (LIVE AI)")

FOOTBALL_API_KEY = "87d5fc28e1e84206b1e48312563372b7"
ODDS_API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

# ======================
# LOAD TRAIN DATA
# ======================
@st.cache_data
def load_data():
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
    return pd.read_csv(url)

# ======================
# TRAIN MODEL
# ======================
def train_model(df):
    teams = {}
    for _, row in df.iterrows():
        home = row["HomeTeam"]
        away = row["AwayTeam"]

        if home not in teams:
            teams[home] = {"g": 0, "ga": 0, "n": 0}
        if away not in teams:
            teams[away] = {"g": 0, "ga": 0, "n": 0}

        teams[home]["g"] += row["FTHG"]
        teams[home]["ga"] += row["FTAG"]
        teams[home]["n"] += 1

        teams[away]["g"] += row["FTAG"]
        teams[away]["ga"] += row["FTHG"]
        teams[away]["n"] += 1

    return teams

# ======================
# FIXTURES
# ======================
def get_fixtures():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    params = {"status": "SCHEDULED"}

    r = requests.get(url, headers=headers, params=params)

    if r.status_code != 200:
        st.error(f"Football API hiba: {r.status_code}")
        return []

    data = r.json()
    matches = []

    for m in data.get("matches", []):
        matches.append({
            "home": m["homeTeam"]["name"],
            "away": m["awayTeam"]["name"]
        })

    return matches

# ======================
# ODDS
# ======================
def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    r = requests.get(url, params=params)

    if r.status_code != 200:
        st.error(f"Odds API hiba: {r.status_code}")
        return {}

    data = r.json()

    odds = {}

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        try:
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            odds[(home, away)] = {o["name"]: o["price"] for o in outcomes}
        except:
            continue

    return odds

# ======================
# PREDICT
# ======================
def predict(home, away, teams):
    if home not in teams or away not in teams:
        return None

    h = teams[home]
    a = teams[away]

    hp = h["g"] / h["n"]
    ap = a["g"] / a["n"]

    total = hp + ap

    return hp/total, ap/total

# ======================
# RUN
# ======================
df = load_data()
teams = train_model(df)

fixtures = get_fixtures()
odds = get_odds()

st.write(f"📊 Meccsek száma: {len(fixtures)}")
st.write(f"💰 Odds találatok: {len(odds)}")

if not fixtures:
    st.warning("Nincs fixture adat")
if not odds:
    st.warning("Nincs odds adat")

for match in fixtures:
    home = match["home"]
    away = match["away"]

    st.write(f"➡️ {home} vs {away}")

    probs = predict(home, away, teams)
    if not probs:
        st.write("❌ nincs modell adat")
        continue

    home_prob, away_prob = probs

    # LAZA MATCH (nem tuple egyezés!)
    found = None
    for (h, a), o in odds.items():
        if home.lower() in h.lower() and away.lower() in a.lower():
            found = o
            break

    if not found:
        st.write("❌ nincs odds match")
        continue

    home_odds = list(found.values())[0]
    away_odds = list(found.values())[1]

    home_value = home_prob * home_odds - 1
    away_value = away_prob * away_odds - 1

    st.write(f"Home value: {round(home_value,2)} | Away value: {round(away_value,2)}")

    if home_value > away_value:
        st.success(f"TIPP: {home}")
    else:
        st.success(f"TIPP: {away}")