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
from PIL import Image
from datetime import datetime

# --- 1. BRANDING & UI ---
st.set_page_config(page_title="ScrivChess v6.2", page_icon="♟️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #D4AF37; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; }
    .stButton>button { 
        border: 1px solid #D4AF37; 
        background-color: #121212; 
        color: #D4AF37; 
        width: 100%;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #D4AF37;
        color: #121212;
    }
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPERS ---
def render_board(board):
    last_move = board.peek() if board.move_stack else None
    svg = chess.svg.board(board, size=400, lastmove=last_move)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<center><img src="data:image/svg+xml;base64,{b64}" /></center>'

def fetch_latest_game():
    headers = {'User-Agent': 'ScrivChess-Coach-App (Contact: your-email-here)'}
    try:
        archives = requests.get("https://api.chess.com/pub/player/ScrivShady/games/archives", headers=headers).json()
        if 'archives' in archives:
            latest_month_url = archives['archives'][-1]
            games_data = requests.get(latest_month_url, headers=headers).json()
            if 'games' in games_data and games_data['games']:p
                return games_data['games'][-1]['pgn']
    except Exception as e:
        st.error(f"Sync failed: {e}")
    return None

# --- 3. SESSION STATE ---
if 'move_index' not in st.session_state: st.session_state.move_index = 0
if 'current_pgn' not in st.session_state: st.session_state.current_pgn = ""
if 'analysis_text' not in st.session_state: st.session_state.analysis_text = ""

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Film Room Coach", "💬 ScrivAssistant", "📊 Stats"])

with tab1:
    st.title("ScrivChess v6.2")
    
    pgn_input = st.text_area("Paste PGN here or use Sync", height=100)
    
    col_sync, col_analyze = st.columns(2)
    
    with col_sync:
        if st.button("🔄 SYNC CHESS.COM"):
            pgn = fetch_latest_game()
            if pgn:
                st.session_state.current_pgn = pgn
                st.success("Fetched latest game!")
            else:
                st.warning("No recent games found.")

    with col_analyze:
        if st.button("🚀 RUN DEEP ANALYSIS"):
            final_pgn = pgn_input if pgn_input else st.session_state.current_pgn
            if final_pgn:
                st.session_state.current_pgn = final_pgn
                st.session_state.move_index = 0
                
                if "GOOGLE_API_KEY" in st.secrets:
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    
                    # UPDATED: Using Gemini 3 Flash for 2026 production stability
                    try:
                        model = genai.GenerativeModel('gemini-3-flash')
                        
                        with st.spinner("Studying the tape..."):
                            prompt = """
                            You are the ScrivShady Coach. 
                            Tone: 80% direct/pattern coach, 20% Fischer/Morphy principles.
                            User: ScrivShady (Bottom player).
                            
                            1. Creative Title (5 words max)
                            2. Accuracy Table (Open/Mid/End %)
                            3. Tactical Vision (Missed PINS, SKEWERS, MATES - Max 2 each)
                            4. Missed Opportunities (Max 2)
                            5. Habit Match (Refer G1-G28 IDs)
                            6. Legend Challenge
                            """
                            response = model.generate_content(prompt + final_pgn)
                            st.session_state.analysis_text = response.text
                    except Exception as e:
                        st.error(f"AI Error: {e}. If this is a 404, the model name may have updated again.")
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

with tab2:
    st.header("ScrivAssistant")
    q = st.text_input("Ask a question about the game:")
    if q and st.session_state.current_pgn:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # UPDATED: Consistent model name for Gemini 3
        model = genai.GenerativeModel('gemini-3-flash')
        res = model.generate_content(f"Game: {st.session_state.current_pgn}. Question: {q}")
        st.write(res.text)

with tab3:
    st.header("Visual History")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1")
        if not df.empty:
            st.line_chart(df['Accuracy'], color="#D4AF37")
    except:
        st.info("Play and analyze games to populate stats.")

    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPERS ---
def render_board(board):
    last_move = board.peek() if board.move_stack else None
    svg = chess.svg.board(board, size=400, lastmove=last_move)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<center><img src="data:image/svg+xml;base64,{b64}" /></center>'

def fetch_latest_game():
    headers = {'User-Agent': 'ScrivChess-Coach-App (Contact: your-email-here)'}
    try:
        # Fetches the list of monthly archives
        archives = requests.get("https://api.chess.com/pub/player/ScrivShady/games/archives", headers=headers).json()
        if 'archives' in archives:
            # Gets the latest month's URL
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

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Film Room Coach", "💬 ScrivAssistant", "📊 Stats"])

with tab1:
    st.title("ScrivChess v6.2")
    
    pgn_input = st.text_area("Paste PGN here or use Sync", height=100)
    
    col_sync, col_analyze = st.columns(2)
    
    with col_sync:
        if st.button("🔄 SYNC CHESS.COM"):
            pgn = fetch_latest_game()
            if pgn:
                st.session_state.current_pgn = pgn
                st.success("Fetched latest game!")
            else:
                st.warning("No recent games found.")

    with col_analyze:
        if st.button("🚀 RUN DEEP ANALYSIS"):
            final_pgn = pgn_input if pgn_input else st.session_state.current_pgn
            if final_pgn:
                st.session_state.current_pgn = final_pgn
                st.session_state.move_index = 0
                
                if "GOOGLE_API_KEY" in st.secrets:
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    # Use exact model name to avoid NotFound error
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    with st.spinner("Studying the tape..."):
                        prompt = """
                        You are the ScrivShady Coach. 
                        Tone: 80% direct/pattern coach, 20% Fischer/Morphy principles.
                        User: ScrivShady (Bottom player).
                        
                        1. Creative Title (5 words max)
                        2. Accuracy Table (Open/Mid/End %)
                        3. Tactical Vision (Missed PINS, SKEWERS, MATES - Max 2 each)
                        4. Missed Opportunities (Max 2)
                        5. Habit Match (Refer G1-G28 IDs)
                        6. Legend Challenge
                        """
                        try:
                            response = model.generate_content(prompt + final_pgn)
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

with tab2:
    st.header("ScrivAssistant")
    q = st.text_input("Ask a question about the game:")
    if q and st.session_state.current_pgn:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Game: {st.session_state.current_pgn}. Question: {q}")
        st.write(res.text)

with tab3:
    st.header("Visual History")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1")
        if not df.empty:
            st.line_chart(df['Accuracy'], color="#D4AF37")
    except:
        st.info("Play and analyze games to populate stats.")
