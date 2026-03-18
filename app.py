import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

st.set_page_config(layout="wide")
st.title("🔥 ELITE AI BETTING SYSTEM")

# ------------------------
# SESSION
# ------------------------
if "bets" not in st.session_state:
    st.session_state.bets = []

# ------------------------
# DATA (több liga)
# ------------------------
urls = [
    "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
    "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
    "https://www.football-data.co.uk/mmz4281/2324/I1.csv"
]

dfs = []
for url in urls:
    try:
        d = pd.read_csv(url)
        dfs.append(d)
    except:
        pass

df = pd.concat(dfs)

df = df.dropna(subset=["FTHG","FTAG","HomeTeam","AwayTeam","B365H","B365D","B365A"])

# ------------------------
# ALAP ÁTLAGOK
# ------------------------
avg_home_goals = df["FTHG"].mean()
avg_away_goals = df["FTAG"].mean()

# ------------------------
# FORMA (last 5)
# ------------------------
def get_form(team, df):

    matches = df[(df["HomeTeam"]==team) | (df["AwayTeam"]==team)].tail(5)

    goals_for = 0
    goals_against = 0

    for _, m in matches.iterrows():
        if m["HomeTeam"] == team:
            goals_for += m["FTHG"]
            goals_against += m["FTAG"]
        else:
            goals_for += m["FTAG"]
            goals_against += m["FTHG"]

    if len(matches) == 0:
        return 1,1

    return goals_for/len(matches), goals_against/len(matches)

# ------------------------
# CSAPAT ERŐSSÉG
# ------------------------
teams = pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique()

attack = {}
defense = {}

for team in teams:

    home = df[df["HomeTeam"]==team]
    away = df[df["AwayTeam"]==team]

    att = (home["FTHG"].mean() + away["FTAG"].mean()) / 2
    deff = (home["FTAG"].mean() + away["FTHG"].mean()) / 2

    form_att, form_def = get_form(team, df)

    # ELITE: kombinált erő
    attack[team] = (att * 0.7 + form_att * 0.3) / avg_home_goals
    defense[team] = (deff * 0.7 + form_def * 0.3) / avg_away_goals

# ------------------------
# PREDIKCIÓ
# ------------------------
def predict(home, away):

    home_xg = attack[home] * defense[away] * avg_home_goals
    away_xg = attack[away] * defense[home] * avg_away_goals

    max_goals = 6

    home_win = 0
    draw = 0
    away_win = 0

    for i in range(max_goals):
        for j in range(max_goals):

            p = poisson.pmf(i, home_xg) * poisson.pmf(j, away_xg)

            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p

    return home_win, draw, away_win

# ------------------------
# MECCSEK (utolsó 20)
# ------------------------
matches = df.tail(20)

rows = []

for _, r in matches.iterrows():

    home = r["HomeTeam"]
    away = r["AwayTeam"]

    hp, dp, ap = predict(home, away)

    odds_h = r["B365H"]
    odds_a = r["B365A"]

    value_h = hp * odds_h - 1
    value_a = ap * odds_a - 1

    rows.append({
        "Match": f"{home} vs {away}",
        "Home %": hp,
        "Away %": ap,
        "Home odds": odds_h,
        "Away odds": odds_a,
        "Home value": value_h,
        "Away value": value_a
    })

df_pred = pd.DataFrame(rows)

# ------------------------
# FILTER (ELITE)
# ------------------------
filtered = df_pred[
    (
        (df_pred["Home value"] > 0.07) |
        (df_pred["Away value"] > 0.07)
    )
]

st.subheader("🔥 ELITE TIPPEK")

if filtered.empty:
    st.warning("Nincs találat")
else:
    for i, row in filtered.iterrows():

        st.write(row["Match"])

        st.write(f"Home%: {round(row['Home %'],2)} | Away%: {round(row['Away %'],2)}")

        st.write(f"Value: H {round(row['Home value'],2)} | A {round(row['Away value'],2)}")

        stake = 1000 * max(row["Home value"], row["Away value"])

        st.write(f"Stake: {round(stake,2)}")

        if st.button(f"Fogadás {row['Match']}", key=f"b{i}"):

            side = "HOME" if row["Home value"] > row["Away value"] else "AWAY"
            odds = row["Home odds"] if side=="HOME" else row["Away odds"]

            st.session_state.bets.append({
                "match": row["Match"],
                "side": side,
                "odds": odds,
                "stake": stake
            })

# ------------------------
# CLV
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