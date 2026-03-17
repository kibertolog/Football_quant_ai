import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("⚽ FINAL + PROFIT Football AI")

# --- INPUTOK ---
API_KEY = st.text_input("62f668f1e4a69303cf9b75e0f3cf3452")
bankroll = st.number_input("Bankroll (€)", value=1000)
mode = st.selectbox("Staking mód", ["SAFE", "SMART"])

# --- LIGÁK ---
leagues = {
    "Premier League":"soccer_epl",
    "La Liga":"soccer_spain_la_liga",
    "Bundesliga":"soccer_germany_bundesliga",
    "Serie A":"soccer_italy_serie_a",
    "Ligue 1":"soccer_france_ligue_one"
}

# --- ELO ---
elo_ratings = {}

def get_elo(team):
    if team not in elo_ratings:
        elo_ratings[team] = 1500
    return elo_ratings[team]

def expected_score(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

# --- MONTE CARLO ---
def monte_carlo(home_xg, away_xg, sims=3000):

    hw = aw = dr = ov = 0

    for _ in range(sims):
        hg = np.random.poisson(home_xg)
        ag = np.random.poisson(away_xg)

        if hg > ag:
            hw += 1
        elif ag > hg:
            aw += 1
        else:
            dr += 1

        if hg + ag > 2:
            ov += 1

    return hw/sims, dr/sims, aw/sims, ov/sims

def implied(odds):
    return 1 / odds

# --- MAIN ---
if API_KEY:

    rows = []

    for name, code in leagues.items():

        url = f"https://api.the-odds-api.com/v4/sports/{code}/odds"

        params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h,totals"
        }

        res = requests.get(url, params=params)

        if res.status_code != 200:
            st.error(f"Hiba: {name}")
            continue

        games = res.json()

        for g in games:

            try:
                home = g["home_team"]
                away = g["away_team"]

                markets = g["bookmakers"][0]["markets"]

                h2h = [m for m in markets if m["key"]=="h2h"][0]["outcomes"]

                home_odds = h2h[0]["price"]
                away_odds = h2h[1]["price"]

                if home_odds < 1.56 and away_odds < 1.56:
                    continue

                # --- ELO ---
                home_elo = get_elo(home)
                away_elo = get_elo(away)

                elo_prob = expected_score(home_elo, away_elo)

                # --- xG becslés ---
                home_xg = 1.2 + (elo_prob * 1.2)
                away_xg = 1.2 + ((1 - elo_prob) * 1.2)

                # --- MONTE CARLO ---
                p_home, p_draw, p_away, p_over = monte_carlo(home_xg, away_xg)

                # --- VALUE ---
                home_val = p_home - implied(home_odds)
                away_val = p_away - implied(away_odds)

                # --- STAKE ---
                edge = max(home_val, away_val)

                if mode == "SAFE":
                    stake = bankroll * 0.02
                else:
                    stake = bankroll * (edge * 0.5)

                tip = "HOME" if home_val > away_val else "AWAY"

                row = {
                    "Liga": name,
                    "Meccs": f"{home} vs {away}",
                    "Home odds": home_odds,
                    "Away odds": away_odds,
                    "Home %": round(p_home,2),
                    "Away %": round(p_away,2),
                    "Over 2.5 %": round(p_over,2),
                    "Home value": round(home_val,3),
                    "Away value": round(away_val,3),
                    "Stake (€)": round(stake,2),
                    "🔥 Tipp": tip
                }

                rows.append(row)

            except:
                pass

    df = pd.DataFrame(rows)

    st.write("Összes meccs:", len(df))

    # --- PROFIT FILTER ---
    filtered_df = df[
        (
            ((df["Home value"] > 0.05) & (df["Home %"] > 0.55)) |
            ((df["Away value"] > 0.05) & (df["Away %"] > 0.55))
        )
        &
        (
            (df["Home odds"].between(1.7,3.5)) |
            (df["Away odds"].between(1.7,3.5))
        )
    ]

    # --- TOP 5 ---
    final_df = filtered_df.sort_values(
        by=["Home value","Away value"],
        ascending=False
    ).head(5)

    st.subheader("💰 NAPI TOP TIPPEK")
    st.dataframe(final_df, use_container_width=True)

    st.subheader("📊 ÖSSZES MECCS")
    st.dataframe(df, use_container_width=True)
