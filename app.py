import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

st.title("📊 ODDS MOVEMENT TRACKER")

# ======================
# API KEY
# ======================
ODDS_API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

# ======================
# SETTINGS
# ======================
FILE = "odds_history.csv"

SPORT = "soccer_epl"  # ide később jöhet több liga

# ======================
# GET ODDS
# ======================
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    r = requests.get(url, params=params)

    if r.status_code != 200:
        st.error("❌ Odds API hiba")
        return None

    return r.json()

# ======================
# SAVE SNAPSHOT
# ======================
def save_snapshot(data):
    rows = []

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        try:
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]

            home_odds = outcomes[0]["price"]
            away_odds = outcomes[1]["price"]

            rows.append({
                "time": datetime.now(),
                "match": f"{home} vs {away}",
                "home": home,
                "away": away,
                "home_odds": home_odds,
                "away_odds": away_odds
            })
        except:
            continue

    df_new = pd.DataFrame(rows)

    if os.path.exists(FILE):
        df_old = pd.read_csv(FILE)
        df = pd.concat([df_old, df_new])
    else:
        df = df_new

    df.to_csv(FILE, index=False)

# ======================
# LOAD HISTORY
# ======================
def load_history():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    return pd.DataFrame()

# ======================
# ANALYZE MOVEMENT
# ======================
def analyze_movement(df):
    results = []

    matches = df["match"].unique()

    for match in matches:
        m = df[df["match"] == match]

        if len(m) < 2:
            continue

        first = m.iloc[0]
        last = m.iloc[-1]

        home_move = last["home_odds"] - first["home_odds"]
        away_move = last["away_odds"] - first["away_odds"]

        results.append({
            "match": match,
            "home_start": first["home_odds"],
            "home_now": last["home_odds"],
            "home_move": round(home_move, 3),

            "away_start": first["away_odds"],
            "away_now": last["away_odds"],
            "away_move": round(away_move, 3)
        })

    return pd.DataFrame(results)

# ======================
# RUN
# ======================
data = get_odds()

if data:
    save_snapshot(data)
    st.success("📥 Odds snapshot mentve")

history = load_history()

if not history.empty:
    movement = analyze_movement(history)

    st.subheader("📊 ODDS MOVEMENT")

    for _, row in movement.iterrows():
        st.write(f"➡️ {row['match']}")

        # HOME
        if row["home_move"] < 0:
            st.success(f"HOME ↓ {row['home_start']} → {row['home_now']} (SHARP)")
        elif row["home_move"] > 0:
            st.error(f"HOME ↑ {row['home_start']} → {row['home_now']}")
        else:
            st.write("HOME → nincs változás")

        # AWAY
        if row["away_move"] < 0:
            st.success(f"AWAY ↓ {row['away_start']} → {row['away_now']} (SHARP)")
        elif row["away_move"] > 0:
            st.error(f"AWAY ↑ {row['away_start']} → {row['away_now']}")
        else:
            st.write("AWAY → nincs változás")

        st.write("---")

else:
    st.warning("Nincs még elég adat (legalább 2 snapshot kell)")