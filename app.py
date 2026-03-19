import requests
import time
from datetime import datetime
from rapidfuzz import process, fuzz
import pandas as pd

# ======================
# CONFIG
# ======================
ODDS_API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

TELEGRAM_TOKEN = "8627872429:AAFkw3t7lhO2oOEubgPcekVrnMp5S8bd4SA"
CHAT_ID = "215380178"

SPORT = "soccer_epl"

MIN_EDGE = 0.03
MIN_VALUE = 0.05

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ======================
# LOAD MODEL DATA
# ======================
def load_data():
    url = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
    return pd.read_csv(url)

df = load_data()

teams = {}

for _, row in df.iterrows():
    h = row["HomeTeam"]
    a = row["AwayTeam"]

    if h not in teams:
        teams[h] = {"g":0,"n":0}
    if a not in teams:
        teams[a] = {"g":0,"n":0}

    teams[h]["g"] += row["FTHG"]
    teams[h]["n"] += 1

    teams[a]["g"] += row["FTAG"]
    teams[a]["n"] += 1

team_list = list(teams.keys())

# ======================
# FUZZY
# ======================
def fuzzy_match(name):
    match, score, _ = process.extractOne(name, team_list)
    return match if score > 70 else None

# ======================
# PREDICT
# ======================
def predict(h,a):
    if h not in teams or a not in teams:
        return None

    hp = teams[h]["g"]/teams[h]["n"]
    ap = teams[a]["g"]/teams[a]["n"]

    t = hp + ap
    return hp/t, ap/t

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
        return None

    return r.json()

# ======================
# MAIN LOOP
# ======================
sent = set()

while True:
    data = get_odds()

    if not data:
        print("API error...")
        time.sleep(60)
        continue

    print("Checking market...", datetime.now())

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        h_map = fuzzy_match(home)
        a_map = fuzzy_match(away)

        if not h_map or not a_map:
            continue

        probs = predict(h_map, a_map)
        if not probs:
            continue

        try:
            outcomes = game["bookmakers"][0]["markets"][0]["outcomes"]
            home_odds = outcomes[0]["price"]
            away_odds = outcomes[1]["price"]
        except:
            continue

        home_p, away_p = probs

        imp_home = 1/home_odds
        imp_away = 1/away_odds

        edge_home = home_p - imp_home
        edge_away = away_p - imp_away

        val_home = home_p * home_odds - 1
        val_away = away_p * away_odds - 1

        key = f"{home}-{away}"

        # ======================
        # ALERT LOGIC
        # ======================
        if val_home > MIN_VALUE and edge_home > MIN_EDGE:
            if key not in sent:
                msg = f"🔥 VALUE BET\n{home} vs {away}\nBET: {home}\nODDS: {home_odds}\nEDGE: {round(edge_home,3)}"
                send_telegram(msg)
                sent.add(key)

        elif val_away > MIN_VALUE and edge_away > MIN_EDGE:
            if key not in sent:
                msg = f"🔥 VALUE BET\n{home} vs {away}\nBET: {away}\nODDS: {away_odds}\nEDGE: {round(edge_away,3)}"
                send_telegram(msg)
                sent.add(key)

    time.sleep(120)  # 2 percenként check