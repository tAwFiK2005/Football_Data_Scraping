# ⚽ Football Data Scraper & Visualizer

A **Streamlit-based web application** for scraping and visualizing football data from [Understat](https://understat.com).  
Compare team performance across seasons and leagues — all in a simple, user-friendly interface.

🌐 **Live App**: [Click to Open](https://footballdatascrapingunderstat.streamlit.app/)

---

## 📂 Project Structure

| File/Folder               | Description                                                                |
|---------------------------|----------------------------------------------------------------------------|
| `fullstreamlit.py`        | Main Python app script (built with Streamlit)                              |
| `TeamsNameUnderstats.txt` | List of valid team names used for scraping                                 |
| `teams_leagues.xlsx`      | Editable list of teams and leagues (user input source)                     |
| `requirements.txt`        | Python dependencies for running the app                                    |

---

## ✨ Features

- ✅ **Live scraping** from [Understat](https://understat.com)
- ✅ Compare **same or different teams** across seasons
- ✅ Analyze data across **Top 5 European Leagues** + **Russian Premier League (RFPL)**
- ✅ Fast and reliable by using **cached `.txt` and `.xlsx` files**
- ✅ Clean, interactive interface with **Streamlit**

---

## 🚀 Getting Started (Local Setup)

> Requires: Python 3.7 or above

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/football-data-scraping.git
cd football-data-scraping
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run fullstreamlit.py
```

---

## 🛠️ How It Works

- Choose a team and season from the dropdowns.
- The app scrapes `TeamsNameUnderstats.txt`.
- Team and league options are loaded from `teams_leagues.xlsx`.
- Visuals and data insights are displayed in real-time using Streamlit.

---

## 📝 Customization Tips

- **Add more teams or leagues**:  
  Simply edit the `teams_leagues.xlsx` file — no code changes needed.

- **Optimize speed**:  
  Use `TeamsNameUnderstats.txt` to avoid needing to insert new teams in `teams_leagues.xlsx` .

---

## 📸 Preview

*(You can insert a screenshot here if you have one)*  
<!-- ![App Preview](https://footballdatascrapingunderstat.streamlit.app/_static/screenshot.png) -->
![image](https://github.com/user-attachments/assets/94aed5aa-e766-45fb-a19b-caa625af3604)
---

## 📄 License

This project is for educational and non-commercial purposes.  
Data sourced from [Understat](https://understat.com).
