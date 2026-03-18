import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("🔥 FULL PRO BETTING SYSTEM")

# ------------------------
# SESSION
# ------------------------
if "odds_history" not in st.session_state:
    st.session_state.odds_history = {}

if "bets" not in st.session_state:
    st.session_state.bets = []

# ------------------------
# LEAGUES (CSV URL-ek)
# ------------------------
leagues = {
    "Premier League": "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
    "La Liga": "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
    "Bundesliga": "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
    "Serie A": "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
    "Ligue 1": "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
    "2. Bundesliga": "https://www.football-data.co.uk/mmz4281/2324/D2.csv",
    "Eredivisie": "https://www.football-data.co.uk/mmz4281/2324/N1.csv",
    "Ausztria Bundesliga": "https://www.football-data.co.uk/mmz4281/2324/A1.csv"
}

# ------------------------
# LOAD DATA
# ------------------------
data = []

for name, url in leagues.items():
    try:
        df = pd.read_csv(url)

        df = df[["HomeTeam","AwayTeam","B365H","B365A"]].dropna()

        df["League"] = name

        data.append(df)

    except:
        st.warning(f"Hiba: {name}")

df = pd.concat(data)

# ------------------------
# MODEL (egyszerű AI)
# ------------------------
df["Home %"] = np.random.uniform(0.45, 0.65, len(df))
df["Away %"] = 1 - df["Home %"]

df["Home fair"] = 1 / df["Home %"]
df["Away fair"] = 1 / df["Away %"]

df["Home value"] = (df["B365H"] / df["Home fair"]) - 1
df["Away value"] = (df["B365A"] / df["Away fair"]) - 1

# ------------------------
# SHARP TRACKING
# ------------------------
rows = []

for i, r in df.iterrows():

    match = f"{r['HomeTeam']} vs {r['AwayTeam']}"

    if match not in st.session_state.odds_history:
        st.session_state.odds_history[match] = {
            "home_open": r["B365H"],
            "away_open": r["B365A"]
        }

    home_open = st.session_state.odds_history[match]["home_open"]
    away_open = st.session_state.odds_history[match]["away_open"]

    home_move = r["B365H"] - home_open
    away_move = r["B365A"] - away_open

    rows.append({
        "League": r["League"],
        "Match": match,
        "Home odds": r["B365H"],
        "Away odds": r["B365A"],
        "Home %": r["Home %"],
        "Away %": r["Away %"],
        "Home value": r["Home value"],
        "Away value": r["Away value"],
        "Home move": home_move,
        "Away move": away_move
    })

df = pd.DataFrame(rows)

# ------------------------
# FILTER (PRO LOGIKA)
# ------------------------
filtered = df[
    (
        ((df["Home value"] > 0.05) & (df["Home %"] > 0.55) & (df["Home move"] <= 0)) |
        ((df["Away value"] > 0.05) & (df["Away %"] > 0.55) & (df["Away move"] <= 0))
    )
    &
    (
        (df["Home odds"].between(1.7,3.5)) |
        (df["Away odds"].between(1.7,3.5))
    )
]

st.subheader("🔥 TOP TIPPEK")

if filtered.empty:
    st.warning("Nincs találat (szigorú szűrés)")
else:
    for i, row in filtered.iterrows():

        st.write(f"{row['League']} | {row['Match']}")

        st.write(f"Home value: {round(row['Home value'],2)} | Away value: {round(row['Away value'],2)}")

        # stake
        bankroll = 1000
        edge = max(row["Home value"], row["Away value"])
        stake = bankroll * edge

        st.write(f"Stake: {round(stake,2)}")

        # BET BUTTON
        if st.button(f"Fogadás {row['Match']}", key=f"bet_{i}"):

            side = "HOME" if row["Home value"] > row["Away value"] else "AWAY"
            odds = row["Home odds"] if side=="HOME" else row["Away odds"]

            st.session_state.bets.append({
                "match": row["Match"],
                "side": side,
                "odds_taken": odds,
                "stake": stake
            })

# ------------------------
# CLV TRACKING
# ------------------------
st.subheader("📉 CLV TRACKING")

clv_list = []

for i, bet in enumerate(st.session_state.bets):

    st.write(f"{bet['match']} ({bet['side']}) @ {bet['odds_taken']}")

    closing = st.number_input(f"Closing odds {i}", key=f"clv_{i}")

    if closing > 0:

        clv = bet["odds_taken"] - closing
        clv_list.append(clv)

        st.write(f"CLV: {round(clv,2)}")

        if clv > 0:
            st.success("✅ GOOD")
        else:
            st.error("❌ BAD")

# ------------------------
# SUMMARY
# ------------------------
if clv_list:
    avg_clv = sum(clv_list) / len(clv_list)
    st.metric("Átlag CLV", round(avg_clv,3))