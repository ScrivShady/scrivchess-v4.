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
st.set_page_config(page_title="ScrivChess v6.1", page_icon="♟️", layout="wide")

# This is where the typo was fixed: unsafe_allow_html=True
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
    /* Mobile optimization for text area */
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTIONS ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key! Please check Advanced Settings > Secrets.")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. THE FILM ROOM LOGIC ---
if 'move_index' not in st.session_state:
    st.session_state.move_index = 0

def render_board(board):
    # Highlight the last move made
    last_move = board.peek() if board.move_stack else None
    svg = chess.svg.board(board, size=400, lastmove=last_move)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<center><img src="data:image/svg+xml;base64,{b64}" /></center>'

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Film Room Coach", "💬 ScrivAssistant", "📊 Stats"])

with tab1:
    st.title("ScrivChess v6.1")
    
    # Input Area
    pgn_input = st.text_area("Paste PGN or use Sync button below", height=100)
    
    col_sync, col_analyze = st.columns(2)
    with col_sync:
        if st.button("🔄 SYNC CHESS.COM"):
            try:
                res = requests.get("https://api.chess.com/pub/player/ScrivShady/games/latest")
                pgn_data = res.json()['games'][-1]['pgn']
                st.session_state.current_pgn = pgn_data
                st.success("Latest game pulled!")
            except:
                st.error("Could not find game. Check username.")

    with col_analyze:
        if st.button("🚀 RUN DEEP ANALYSIS"):
            if pgn_input:
                st.session_state.current_pgn = pgn_input
            
            if 'current_pgn' in st.session_state:
                st.session_state.move_index = 0
                with st.spinner("Studying the tape with ScrivShady 3.0 Logic..."):
                    prompt = """
                    You are the ScrivShady Coach. 
                    Tone: 80% direct/pattern-focused coach, 20% Fischer/Morphy principles.
                    User: ScrivShady (Always BOTTOM player).
                    
                    Required Output Format:
                    1. Theme Name: Creative title (play on words/tactical pun, max 5 words).
                    2. Accuracy Table: Opening, Middlegame, Endgame %.
                    3. Tactical Vision: Explicitly identify PINS, SKEWERS, and MATES (Max 2 each).
                    4. Missed Opportunities: Identify MAX 2 critical moments.
                    5. Habit Match: Reference G1-G28 IDs (f-pawn, c2 forks, corner blindness).
                    6. The Legend Challenge: One high-level 'Legendary' goal.
                    """
                    response = model.generate_content(prompt + st.session_state.current_pgn)
                    st.session_state.analysis_text = response.text

    # Display Analysis
    if 'analysis_text' in st.session_state:
        st.markdown(st.session_state.analysis_text)

    # --- THE FILM ROOM (Replay Section) ---
    if 'current_pgn' in st.session_state:
        game = chess.pgn.read_game(io.StringIO(st.session_state.current_pgn))
        if game:
            moves = list(game.mainline_moves())
            board = game.board()
            # Advance board to the current move index
            for i in range(st.session_state.move_index):
                board.push(moves[i])
            
            st.markdown("---")
            st.subheader("🎬 Game Film: Move-by-Move")
            st.markdown(render_board(board), unsafe_allow_html=True)
            
            # Nav Buttons
            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                if st.button("⬅️ BACK") and st.session_state.move_index > 0:
                    st.session_state.move_index -= 1
                    st.rerun()
            with c2:
                st.write(f"<center>Move {st.session_state.move_index} / {len(moves)}</center>", unsafe_allow_html=True)
            with c3:
                if st.button("FORWARD ➡️") and st.session_state.move_index < len(moves):
                    st.session_state.move_index += 1
                    st.rerun()

with tab2:
    st.header("ScrivAssistant")
    q = st.text_input("Ask a question about your history or current game:")
    if q and 'current_pgn' in st.session_state:
        res = model.generate_content(f"Context: {st.session_state.current_pgn}. Question: {q}")
        st.write(res.text)

with tab3:
    st.header("Visual History")
    # This will load from Google Sheets automatically
    try:
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1")
        if not df.empty:
            st.line_chart(df['Accuracy'], color="#D4AF37")
            st.dataframe(df)
    except:
        st.info("Play and save your first game to see stats here!")
