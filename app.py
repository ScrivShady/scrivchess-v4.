import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import chess
import chess.pgn
import chess.svg
import io
import base64
import requests

# --- 1. UI CONFIG ---
st.set_page_config(page_title="ScrivChess v6.5", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #D4AF37; }
    .stSidebar { background-color: #1c1c1c !important; border-right: 1px solid #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FETCH ALL HISTORY LOGIC ---
def fetch_all_history(username):
    headers = {'User-Agent': 'ScrivChess-App'}
    all_games = []
    try:
        res = requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers)
        if res.status_code == 200:
            urls = res.json().get('archives', [])
            for url in urls: # This loops through every month in your history
                month_data = requests.get(url, headers=headers).json()
                for game in month_data.get('games', []):
                    if 'pgn' in game:
                        all_games.append(game['pgn'])
            return all_games[::-1] # Reverse so newest is first
    except: return []
    return []

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("♟️ ScrivChess Master")
    user = st.text_input("Chess.com User", "ScrivShady")
    
    if st.button("📥 FETCH FULL HISTORY"):
        with st.spinner("Retrieving your legacy..."):
            st.session_state.history = fetch_all_history(user)
    
    if 'history' in st.session_state:
        st.write(f"Games Found: {len(st.session_state.history)}")
        game_idx = st.selectbox("Select Game", range(len(st.session_state.history)), 
                                format_func=lambda x: f"Game {len(st.session_state.history)-x}")
        if st.button("🔌 LOAD TO FILM ROOM"):
            st.session_state.current_pgn = st.session_state.history[game_idx]
            st.session_state.analysis_text = ""

    st.markdown("---")
    mode = st.radio("Go to:", ["🎯 Film Room", "📊 Stats"])

# --- 4. PAGES ---
if mode == "🎯 Film Room":
    st.title("🎯 Film Room Coach")
    if 'current_pgn' in st.session_state:
        if st.button("🚀 RUN DEEP ANALYSIS"):
            with st.spinner("Analyzing..."):
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # FIXED MODEL NAME TO AVOID 404
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Analyze this chess game for ScrivShady: {st.session_state.current_pgn}")
                st.session_state.analysis_text = response.text
        
        if st.session_state.analysis_text:
            st.markdown(st.session_state.analysis_text)
            
        # Board rendering logic would follow here...
    else:
        st.info("Fetch history in the sidebar to start.")

elif mode == "📊 Stats":
    st.title("📊 Visual History")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
        st.line_chart(df)
    except:
        st.warning("Please finish the Google Cloud Service Account setup to see stats.")
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<center><img src="data:image/svg+xml;base64,{b64}" /></center>'

def fetch_latest_game():
    headers = {'User-Agent': 'ScrivChess-Coach-App (Contact: your-email-here)'}
    try:
        archives = requests.get("https://api.chess.com/pub/player/ScrivShady/games/archives", headers=headers).json()
        if 'archives' in archives:
            latest_month_url = archives['archives'][-1]
            games_data = requests.get(latest_month_url, headers=headers).json()
            if 'games' in games_data and games_data['games']:
                return games_data['games'][-1]['pgn']
    except Exception as e:
        st.error(f"Sync failed: {e}")
    return None

# --- 3. SESSION STATE ---
if 'move_index' not in st.session_state: st.session_state.move_index = 0
if 'current_pgn' not in st.session_state: st.session_state.current_pgn = ""
if 'analysis_text' not in st.session_state: st.session_state.analysis_text = ""

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("♟️ ScrivChess")
    st.subheader("Master Menu")
    page = st.radio("Navigate", ["🎯 Film Room", "💬 ScrivAssistant", "📊 Stats"])
    st.markdown("---")
    if st.button("🔄 SYNC CHESS.COM"):
        pgn = fetch_latest_game()
        if pgn:
            st.session_state.current_pgn = pgn
            st.session_state.move_index = 0
            st.success("Latest game fetched!")
        else:
            st.warning("No recent games found.")

# --- 5. MAIN PAGES ---
if page == "🎯 Film Room":
    st.title("🎯 Film Room Coach")
    
    pgn_input = st.text_area("Paste PGN here (if not synced)", height=100)
    
    if st.button("🚀 RUN DEEP ANALYSIS"):
        final_pgn = pgn_input if pgn_input else st.session_state.current_pgn
        if final_pgn:
            st.session_state.current_pgn = final_pgn
            if "GOOGLE_API_KEY" in st.secrets:
                genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                # FIXED: Using gemini-1.5-flash-latest to avoid 404 errors
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                with st.spinner("Coach is studying the tape..."):
                    prompt = """
                    You are the ScrivShady Coach. 
                    Tone: 80% direct/pattern coach, 20% Fischer/Morphy principles.
                    User: ScrivShady (Bottom player).
                    1. Creative Title (5 words max)
                    2. Accuracy Table (Open/Mid/End %)
                    3. Tactical Vision (Missed PINS, SKEWERS, MATES - Max 2 each)
                    4. Missed Opportunities (Max 2)
                    5. Legend Challenge
                    """
                    try:
                        response = model.generate_content(f"{prompt}\n\nGAME PGN:\n{final_pgn}")
                        st.session_state.analysis_text = response.text
                    except Exception as e:
                        st.error(f"AI Error: {e}")
            else:
                st.error("API Key missing in Secrets!")

    if st.session_state.analysis_text:
        st.markdown(st.session_state.analysis_text)

    if st.session_state.current_pgn:
        game = chess.pgn.read_game(io.StringIO(st.session_state.current_pgn))
        if game:
            moves = list(game.mainline_moves())
            board = game.board()
            for i in range(st.session_state.move_index): board.push(moves[i])
            
            st.markdown("---")
            st.subheader("🎬 Game Film")
            st.markdown(render_board(board), unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                if st.button("⬅️ BACK") and st.session_state.move_index > 0:
                    st.session_state.move_index -= 1
                    st.rerun()
            with c2: st.write(f"<center>Move {st.session_state.move_index} / {len(moves)}</center>", unsafe_allow_html=True)
            with c3:
                if st.button("FORWARD ➡️") and st.session_state.move_index < len(moves):
                    st.session_state.move_index += 1
                    st.rerun()

elif page == "💬 ScrivAssistant":
    st.header("💬 ScrivAssistant")
    if not st.session_state.current_pgn:
        st.info("Sync or paste a game in the Film Room first.")
    else:
        q = st.text_input("Ask a question about the current game:")
        if q:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            res = model.generate_content(f"Game: {st.session_state.current_pgn}. Question: {q}")
            st.write(res.text)

elif page == "📊 Stats":
    st.header("📊 Visual History")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1")
        if not df.empty:
            st.line_chart(df['Accuracy'], color="#D4AF37")
    except:
        st.info("Connect your Google Sheet in Secrets to see historical data.")
