# ScrivChess v6.2 ♟️

An AI-powered chess coaching web app built with Streamlit. Fetch your latest Chess.com games, get deep analysis from Google Gemini, and step through every move on an interactive board.

## Features

- **🎯 Film Room Coach** – Paste or sync a PGN, run AI analysis, and replay the game move-by-move.
- **💬 ScrivAssistant** – Ask natural-language questions about any loaded game.
- **📊 Stats** – View accuracy history pulled from a linked Google Sheet.

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and add:

| Key | Value |
|---|---|
| `GOOGLE_API_KEY` | Your [Google Gemini API key](https://aistudio.google.com/app/apikey) |
| `GSHEET_URL` | Full URL of your Google Sheet |

### 3. Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set the main file path to `app.py`.
4. In **Advanced settings → Secrets**, paste the contents of your `secrets.toml`:

```toml
GOOGLE_API_KEY = "your-google-gemini-api-key"
GSHEET_URL = "https://docs.google.com/spreadsheets/d/..."
```

5. Click **Deploy** – Streamlit Cloud handles the rest.

## Required Secrets

| Secret | Description |
|---|---|
| `GOOGLE_API_KEY` | Google Gemini API key (enables AI analysis) |
| `GSHEET_URL` | Google Sheets URL for storing game stats |
