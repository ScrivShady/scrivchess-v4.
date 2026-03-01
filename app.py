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
st.markdown("<style>.stApp {background-color: #121212; color: #D4AF37;} [data-testid='stMetricValue'] {color: #D4AF37 !important;} .stButton>button {border: 1px solid #D4AF37; background-color: #121212; color: #D4AF37; width: 100%;}</style>", unsafe_allow_stdio=True)

# --- 2. CONNECTIONS ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key in Secrets!")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. THE FILM ROOM LOGIC ---
if 'move_index' not in st.session_state:
    st.session_state.move_index = 0

def render_board(board):
    svg = chess.svg.board(board, size=400, lastmove=board.peek() if board.move_stack else None)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<center><img src="data:image/svg+xml;base64,{b64}" /></center>'

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Film Room Coach", "💬 ScrivAssistant", "📊 Stats"])

with tab1:
    st.title("ScrivChess v6.1")
    pgn_input = st.text_area("Paste PGN or use Sync", height=100)
    
    if st.button("🚀 ANALYZE GAME"):
        st.session_state.move_index = 0
        with st.spinner("Analyzing with ScrivShady 3.0 Logic..."):
            prompt = "You are the ScrivShady Coach. 80% direct patterns, 20% Fischer/Morphy. Analyze for: 1. Creative Title (5 words max), 2. Accuracy Table, 3. Tactical Vision (Pins/Skewers/Mates), 4. Missed Opportunities (Max 2), 5. Habit Match, 6. Legend Challenge."
            response = model.generate_content(prompt + pgn_input)
            st.markdown(response.text)
            st.session_state.current_pgn = pgn_input

    # THE FILM ROOM
    if 'current_pgn' in st.session_state:
        game = chess.pgn.read_game(io.StringIO(st.session_state.current_pgn))
        if game:
            moves = list(game.mainline_moves())
            board = game.board()
            for i in range(st.session_state.move_index): board.push(moves[i])
            
            st.markdown("---")
            st.subheader("🎬 Game Film")
            st.markdown(render_board(board), unsafe_allow_stdio=True)
            
            c1, c2, c3 = st.columns([1,2,1])
            with c1:
                if st.button("⬅️ BACK") and st.session_state.move_index > 0:
                    st.session_state.move_index -= 1
                    st.rerun()
            with c2: st.write(f"<center>Move {st.session_state.move_index} of {len(moves)}</center>", unsafe_allow_stdio=True)
            with c3:
                if st.button("FORWARD ➡️") and st.session_state.move_index < len(moves):
                    st.session_state.move_index += 1
                    st.rerun()

with tab2:
    st.header("ScrivAssistant")
    q = st.text_input("Ask about the game:")
    if q: st.write(model.generate_content(f"Context: {pgn_input}. Question: {q}").text)

with tab3:
    st.header("Visual History")
    # History logic pulls from Google Sheets
