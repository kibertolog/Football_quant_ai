import streamlit as st
import requests
import pandas as pd

st.title("⚽ Football Value Finder")

API_KEY = "62f668f1e4a69303cf9b75e0f3cf3452"

leagues = {
"Premier League":"soccer_epl",
"La Liga":"soccer_spain_la_liga",
"Bundesliga":"soccer_germany_bundesliga",
"Bundesliga 2":"soccer_germany_bundesliga2",
"Serie A":"soccer_italy_serie_a",
"Ligue 1":"soccer_france_ligue_one",
"Austria":"soccer_austria_bundesliga"
}

data = []

for name, code in leagues.items():

    url = f"https://api.the-odds-api.com/v4/sports/{code}/odds"

    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    try:
        res = requests.get(url, params=params)
        games = res.json()

        for g in games:

            try:
                home = g["home_team"]
                away = g["away_team"]

                odds = g["bookmakers"][0]["markets"][0]["outcomes"]

                data.append({
                    "Liga": name,
                    "Meccs": f"{home} vs {away}",
                    "Hazai odds": odds[0]["price"],
                    "Vendég odds": odds[1]["price"]
                })

            except:
                pass

    except:
        st.error(f"Hiba: {name}")

df = pd.DataFrame(data)

st.success(f"Talált meccsek: {len(df)}")

st.dataframe(df, use_container_width=True)
