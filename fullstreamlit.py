import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from highlight_text import fig_text
import plotly.graph_objects as go
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

#Mongodb atlas setup config
MONGO_URI = "mongodb+srv://UnderstatProject:UnderstatProject@understatprojectcluster.q03ptpx.mongodb.net/?retryWrites=true&w=majority&appName=UnderstatProjectCluster"
client = MongoClient(MONGO_URI)
db = client["understat_data"]

#Data Functions 
def get_league(team1):
    df = pd.read_excel('teams_leagues.xlsx')
    league = df[df['team'] == team1]['league'].iloc[0]
    return league

def get_team_key(team1, year1):
    re_team1 = re.sub(r"\s+", "_", team1)
    link = f"https://understat.com/team/{re_team1}/{year1}"
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    scripts = soup.find_all('script')
    strings = scripts[1].string
    ind_start = strings.index("('") + 2
    ind_end = strings.index("')")
    json_data = strings[ind_start:ind_end]
    json_data = json_data.encode('utf8').decode('unicode_escape')
    data = json.loads(json_data)
    df1 = pd.DataFrame(data)
    df_a = df1['a'].apply(pd.Series)
    df_h = df1['h'].apply(pd.Series)
    df_fx = pd.DataFrame(df_h)
    grouped = df_fx.groupby('title')
    if team1 in grouped.groups:
        group = grouped.get_group(team1)
    team1_key = group.iloc[0, 0]
    return team1_key

def get_fixtures(team, year):
    re_team = re.sub(r"\s+", "_", team)
    link = f"https://understat.com/team/{re_team}/{year}"
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'html.parser')
    scripts = soup.find_all('script')
    
    strings = scripts[1].string
    ind_start = strings.index("('") + 2
    ind_end = strings.index("')")
    json_data = strings[ind_start:ind_end]
    json_data = json_data.encode('utf8').decode('unicode_escape')
    data = json.loads(json_data)

    df1 = pd.DataFrame(data)
    df_a = df1['a'].apply(pd.Series)
    df_h = df1['h'].apply(pd.Series)

    opponents = []
    for i in range(len(df1)):
        home_team = df_h.loc[i, 'title']
        away_team = df_a.loc[i, 'title']
        if home_team == team:
            opponents.append(away_team)
        else:
            opponents.append(home_team)
    return opponents
    
@st.cache_data
def load_all_understat_data(team1, year1):
    if not team1 or not year1:
        return None

    try:
        re_team = re.sub(r"\s+", "_", team1)
        link = f"https://understat.com/team/{re_team}/{year1}"
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all('script')

        if len(scripts) < 3:
            st.warning(f"Not enough script tags found for {team1} {year1}.")
            return None

        strings = scripts[2].string
        ind_start = strings.index("('") + 2
        ind_end = strings.index("')")
        json_data = strings[ind_start:ind_end]
        json_data = json_data.encode('utf8').decode('unicode_escape')
        data = json.loads(json_data)
        return data

    except Exception as e:
        st.error(f"Failed to load data for {team1} ({year1}): {e}")
        return None

def clean_data(data_section, key):
    df = pd.DataFrame(data_section[key])
    df_against = df.loc['against']
    df = df.drop(['stat', 'time', 'against'], axis=0, errors='ignore')
    df_against_df = pd.DataFrame(df_against)
    df_against_expanded = df_against_df['against'].apply(pd.Series).T
    df_against_expanded.index = [str(idx) + 'A' for idx in df.index]
    df_main = df.astype('float64')
    cleaned = pd.concat([df_main, df_against_expanded], axis=0).T
    return cleaned

def save_to_mongo(df, collection_name, team, year):
    if df.empty:
        return
    records = df.reset_index().to_dict(orient='records')
    for r in records:
        r['team'] = team
        r['year'] = year
    try:
        db[collection_name].insert_many(records, ordered=False)
    except BulkWriteError as e:
        st.warning(f"Some records were not inserted due to duplicates.")

get_situation_data = lambda d: clean_data(d, 'situation')
get_formation_data = lambda d: clean_data(d, 'formation')
get_gamestate_data = lambda d: clean_data(d, 'gameState')
get_timing_data = lambda d: clean_data(d, 'timing')
get_shotzone_data = lambda d: clean_data(d, 'shotZone')
get_attackspeed_data = lambda d: clean_data(d, 'attackSpeed')
get_result_data = lambda d: clean_data(d, 'result')

#  Streamlit App 

st.set_page_config(layout="wide", page_title="Football Data Comparison")

st.sidebar.title("Team Comparison")
mode = st.sidebar.selectbox("Comparison Mode",
                            options= ["Compare Two Teams (Any Year)",
                                      "Compare One Team Across Years",
                                       "Single Team Stat Overview"])
if mode == "Compare Two Teams (Any Year)":  
    team1 = st.sidebar.text_input("Enter Team 1" , "Barcelona")
    year1 = st.sidebar.selectbox("Select Year for Team 1", list(range(2014, 2025))[::-1])

    team2 = st.sidebar.text_input("Enter Team 2" , "Real Madrid")
    year2 = st.sidebar.selectbox("Select Year for Team 2", list(range(2014, 2025))[::-1])
    
    # Load data
    data_team1 = load_all_understat_data(team1, year1)
    data_team2 = load_all_understat_data(team2, year2)        
    data_type = st.sidebar.selectbox("Select Data Type", [
        "Situation", "Formation", "AttackSpeed", "GameState", "Timing", "ShotZone", "Result"
            ])

    data_funcs = {
        "Situation": get_situation_data,
        "Formation": get_formation_data,
        "AttackSpeed": get_attackspeed_data,
        "GameState": get_gamestate_data,
        "Timing": get_timing_data,
        "ShotZone": get_shotzone_data,
        "Result": get_result_data,
            }
    
    df1 = data_funcs[data_type](data_team1)
    df2 = data_funcs[data_type](data_team2)
    save_to_mongo(df1, data_type, team1, year1)
    save_to_mongo(df2, data_type, team2, year2)
    # Sort index descending
    df1 = df1.sort_index(ascending=False)
    df2 = df2.sort_index(ascending=False)
    if data_team1 and data_team2:
        tab1, tab2 = st.tabs(["Data  Tables", "Plots"])
        #  Tab 1:
        with tab1:

            st.markdown(f"### {team1} {year1} - {data_type.title()} Data")
            st.dataframe(df1)

            st.markdown(f"### {team2} {year2} - {data_type.title()} Data")
            st.dataframe(df2)
        save_to_mongo(df1, data_type, team1, year1)
        save_to_mongo(df2, data_type, team2, year2)
        # Tab 2
        with tab2:
            st.markdown(f"### {data_type.title()} Comparison Plot")

            metric = st.selectbox("Select Metric to Compare", df1.columns)

            # Create bar chart
            comparison_df = pd.DataFrame({
                f"{team1} ({year1})": df1[metric],
                f"{team2} ({year2})": df2[metric]
            })

            comparison_df.plot(kind='bar', figsize=(10, 6))
            plt.title(f"{data_type.title()} - {metric} Comparison")
            plt.xlabel("Category")
            plt.ylabel(metric)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(plt)
    else:
        st.warning("Please enter valid teams and years to compare data.")
elif mode =="Compare One Team Across Years":
     
    team1 = st.sidebar.text_input("Enter Team " , "Barcelona")
    year1 = st.sidebar.selectbox("Select year to compare", list(range(2014, 2025))[::-1])
    year2 = st.sidebar.selectbox("Select another year", list(range(2014, 2024))[::-1])

    # Load data
    data_team1 = load_all_understat_data(team1, year1)
    data_team2 = load_all_understat_data(team1, year2)

    data_type = st.sidebar.selectbox("Select Data Type", [
                "Situation", "Formation", "AttackSpeed", "GameState", "Timing", "ShotZone", "Result"
            ])
    data_funcs = {
            "Situation": get_situation_data,
            "Formation": get_formation_data,
            "AttackSpeed": get_attackspeed_data,
            "GameState": get_gamestate_data,
            "Timing": get_timing_data,
            "ShotZone": get_shotzone_data,
            "Result": get_result_data,
                }
    df1 = data_funcs[data_type](data_team1)
    df2 = data_funcs[data_type](data_team2)
    save_to_mongo(df1, data_type, team1, year1)
    save_to_mongo(df2, data_type, team1, year2)
    # Sort index descending
    df1 = df1.sort_index(ascending=False)
    df2 = df2.sort_index(ascending=False)
    if data_team1 and data_team2:
        tab1, tab2 = st.tabs(["Data  Tables", "Plots"])
       
        # ---------- Tab 1: Data Tables ----------
        with tab1:

            st.markdown(f"### {team1} {year1} - {data_type.title()} Data")
            st.dataframe(df1)

            st.markdown(f"### {team1} {year2} - {data_type.title()} Data")
            st.dataframe(df2)
        # ---------- Tab 2: Plots ----------
        with tab2:
            st.markdown(f"### {data_type.title()} Comparison Plot")

            metric = st.selectbox("Select Metric to Compare", df1.columns)

            # Create bar chart
            comparison_df = pd.DataFrame({
                f"{team1} ({year1})": df1[metric],
                f"{team1} ({year2})": df2[metric]
            })

            comparison_df.plot(kind='bar', figsize=(10, 6))
            plt.title(f"{data_type.title()} - {metric} Comparison")
            plt.xlabel("Category")
            plt.ylabel(metric)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(plt)
    else:
        st.warning("Please enter valid team and years to compare data.")
else:
    team1 = st.sidebar.text_input("Enter Team " , "Barcelona")
    year1 = st.sidebar.selectbox("Select Year for Team ", list(range(2014, 2025))[::-1])
    stat_types = st.multiselect("Select stat(s) to compare", [
        "xG", "xGA", "npxG", "npxGA", "xpts", "npxGD"
    ], default=["xG"])

    # 1) Load team page JSON for your custom xG plot
    team_data = load_all_understat_data(team1, year1)
    # Get fixtures for labeling
    teams_played = get_fixtures(team1, year1)
    test = len(teams_played) + 1
    league = get_league(team1)
    link = f"https://understat.com/league/{league}/{year1}"
    res = requests.get(link)
    soup = BeautifulSoup(res.content, 'html.parser')
    scripts = soup.find_all('script')

    strings = scripts[2].string
    ind_start = strings.index("('") + 2
    ind_end = strings.index("')")
    json_data = strings[ind_start:ind_end]
    json_data = json_data.encode('utf8').decode('unicode_escape')
    data = json.loads(json_data)
    league_data = json.loads(json_data)
    history_df = pd.DataFrame(
        league_data[get_team_key(team1, year1)]['history']
    )
    # Only the columns we know are available:
    history_df['Match'] = np.arange(1, len(history_df) + 1)
    df = pd.DataFrame(data[get_team_key(team1, year1)]['history'])
    df['xGdif'] = df['xG'] - df['xGA']
    df['Match'] = np.arange(1, len(df) + 1)  # 👈 this goes before filtering

    df['xGdif'] = np.round(df['xGdif'], 2)   # Round before filtering

    df_pos = df[df['xGdif'] > 0]
    df_neg = df[df['xGdif'] < 0]
    if stat_types == ["xG"]:
    # Plot
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots(figsize=(15, 12))

        plt.hlines(y=df_pos['Match'], xmin=0, xmax=df_pos['xGdif'], color='cyan', alpha=0.4, linewidth=8)
        plt.hlines(y=df_neg['Match'], xmin=0, xmax=df_neg['xGdif'], color='red', alpha=0.4, linewidth=8)

        ax.tick_params(axis='x', colors='gray')
        ax.tick_params(axis='y', colors='gray')
        plt.xticks(np.arange(-3, 4, 0.5))
        plt.yticks(np.arange(1, test), teams_played, rotation='horizontal', fontsize=10)
        plt.gca().xaxis.grid(False)
        plt.gca().yaxis.grid(False)

        fig_text(0.08, 1.03, s=f"{team1} {year1} Season xG Differential\n", fontsize=25, fontweight="light")
        fig_text(0.08, 0.97, s=" <Positive xG> vs <Negative xG>", highlight_textprops=[{"color": 'cyan'}, {'color': "red"}], fontsize=20, fontweight="light")
        fig_text(0.45, 0.01, s="xG Differential\n", fontsize=20, fontweight="bold", color="black")
        fig_text(0.0001, 0.6, s="Teams\n", fontsize=20, fontweight="bold", color="black", rotation=90)

        for i in range(len(df_pos['Match'])):
            plt.annotate(df_pos['xGdif'].iloc[i],
                         (df_pos['xGdif'].iloc[i] + 0.2, df_pos['Match'].iloc[i]),
                         c='black', size=10, ha='center', va='center')

        for i in range(len(df_neg['Match'])):
            plt.annotate(df_neg['xGdif'].iloc[i],
                         (df_neg['xGdif'].iloc[i] - 0.2, df_neg['Match'].iloc[i]),
                         c='black', size=10, ha='center', va='center')

        st.pyplot(fig)
        # CASE B) exactly one non-xG stat
    elif len(stat_types) in [1, 2]:
        fig = go.Figure()

        for stat in stat_types:
            fig.add_trace(go.Scatter(
                x=history_df['Match'],
                y=history_df[stat],
                mode='lines+markers',
                name=stat,
                line=dict(width=3)
            ))

        fig.update_layout(
            title=f"{team1} {year1} - {' & '.join(stat_types)} Over Matches",
            template="plotly_white",
            xaxis_title="Matchday",
            yaxis_title="Value",
            xaxis=dict(tickmode='linear'),
            yaxis=dict(showgrid=True, gridcolor="lightgrey"),
            plot_bgcolor='white'
        )

        st.plotly_chart(fig, use_container_width=True)
    # CASE C) multiple stats → radar
    else:
        valid_stats = [s for s in stat_types if s in history_df.columns]
        if not valid_stats:
            st.warning("None of the selected stats are available in the data.")
        else:
            vals = history_df[valid_stats].sum().tolist()

            # Normalize the values so that the radar looks readable
            max_val = max(vals)
            normalized_vals = [v / max_val for v in vals]
            normalized_vals.append(normalized_vals[0])  # close the radar

            angles = valid_stats + [valid_stats[0]]

            radar_fig = go.Figure(go.Scatterpolar(
                r=normalized_vals,
                theta=angles,
                fill='toself',
                line=dict(color='royalblue'),
                marker=dict(size=8)
            ))

            radar_fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        tickfont=dict(size=12)
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=14),
                        rotation=90,
                        direction="clockwise"
                    )
                ),
                showlegend=False,
                title={
                    'text': f"{team1} ({year1}) – Normalized Stats Radar",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                margin=dict(l=40, r=40, t=80, b=40)
            )
            st.plotly_chart(radar_fig, use_container_width=True)
