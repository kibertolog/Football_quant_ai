import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

st.set_page_config(layout="wide")

st.title("🔥 REAL AI BETTING SYSTEM")

# ------------------------
# SESSION
# ------------------------
if "bets" not in st.session_state:
    st.session_state.bets = []

# ------------------------
# DATA (VALÓDI)
# ------------------------
url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"

df = pd.read_csv(url)

df = df.dropna(subset=["FTHG","FTAG","HomeTeam","AwayTeam","B365H","B365D","B365A"])

# ------------------------
# ÁTLAG GÓLOK
# ------------------------
avg_home_goals = df["FTHG"].mean()
avg_away_goals = df["FTAG"].mean()

# ------------------------
# CSAPAT STATOK
# ------------------------
teams = pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique()

attack_strength = {}
defense_strength = {}

for team in teams:

    home = df[df["HomeTeam"] == team]
    away = df[df["AwayTeam"] == team]

    attack = (home["FTHG"].mean() + away["FTAG"].mean()) / 2
    defense = (home["FTAG"].mean() + away["FTHG"].mean()) / 2

    attack_strength[team] = attack / avg_home_goals
    defense_strength[team] = defense / avg_away_goals

# ------------------------
# ELŐREJELZÉS
# ------------------------
def predict(home, away):

    home_xg = attack_strength[home] * defense_strength[away] * avg_home_goals
    away_xg = attack_strength[away] * defense_strength[home] * avg_away_goals

    max_goals = 5

    home_win = 0
    draw = 0
    away_win = 0

    for i in range(max_goals):
        for j in range(max_goals):

            prob = poisson.pmf(i, home_xg) * poisson.pmf(j, away_xg)

            if i > j:
                home_win += prob
            elif i == j:
                draw += prob
            else:
                away_win += prob

    return home_win, draw, away_win

# ------------------------
# MAI MECCSEK (szimulált = utolsó sorok)
# ------------------------
matches = df.tail(20)

results = []

for i, r in matches.iterrows():

    home = r["HomeTeam"]
    away = r["AwayTeam"]

    home_p, draw_p, away_p = predict(home, away)

    home_odds = r["B365H"]
    draw_odds = r["B365D"]
    away_odds = r["B365A"]

    home_value = (home_p * home_odds) - 1
    away_value = (away_p * away_odds) - 1

    results.append({
        "Match": f"{home} vs {away}",
        "Home %": home_p,
        "Draw %": draw_p,
        "Away %": away_p,
        "Home odds": home_odds,
        "Away odds": away_odds,
        "Home value": home_value,
        "Away value": away_value
    })

df_pred = pd.DataFrame(results)

# ------------------------
# FILTER
# ------------------------
filtered = df_pred[
    (df_pred["Home value"] > 0.05) |
    (df_pred["Away value"] > 0.05)
]

st.subheader("🔥 VALUE TIPPEK (REAL AI)")

if filtered.empty:
    st.warning("Nincs value")
else:
    for i, row in filtered.iterrows():

        st.write(row["Match"])

        st.write(f"Home %: {round(row['Home %'],2)} | Away %: {round(row['Away %'],2)}")

        st.write(f"Home value: {round(row['Home value'],2)} | Away value: {round(row['Away value'],2)}")

        stake = 1000 * max(row["Home value"], row["Away value"])

        st.write(f"Stake: {round(stake,2)}")

        if st.button(f"Fogadás {row['Match']}", key=f"bet_{i}"):

            side = "HOME" if row["Home value"] > row["Away value"] else "AWAY"
            odds = row["Home odds"] if side=="HOME" else row["Away odds"]

            st.session_state.bets.append({
                "match": row["Match"],
                "side": side,
                "odds": odds,
                "stake": stake
            })

# ------------------------
# CLV TRACKING
# ------------------------
st.subheader("📉 CLV")

for i, bet in enumerate(st.session_state.bets):

    st.write(f"{bet['match']} @ {bet['odds']}")

    closing = st.number_input(f"Closing odds {i}", key=f"clv_{i}")

    if closing > 0:

        clv = bet["odds"] - closing

        st.write(f"CLV: {round(clv,2)}")

        if clv > 0:
            st.success("✅ GOOD")
        else:
            st.error("❌ BAD")