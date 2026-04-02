import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import chess
import chess.pgn
import chess.svg
import io
import os
import re
import time
import base64
import requests
from datetime import datetime

# --- 1. BRANDING & UI ---
st.set_page_config(page_title="ScrivChess: Strategic Insights", page_icon="♟️", layout="wide")

st.markdown("""
    <style>
    /* Contrast: #D4AF37 on #121212 ≈ 7.7:1 — meets WCAG 2.1 AAA (7:1) for all text sizes */
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
    /* Keyboard-navigation focus ring (accessibility) */
    .stButton>button:focus-visible {
        outline: 3px solid #D4AF37;
        outline-offset: 2px;
    }
    .stTextArea textarea {
        background-color: #1c1c1c;
        color: #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY: RATE LIMITING (Gemini API) ---
_RATE_LIMIT_CALLS = 10    # max calls per window
_RATE_LIMIT_PERIOD = 60   # rolling window in seconds

def check_rate_limit() -> bool:
    """Token-bucket rate limiter for Gemini API calls. Returns False when limit is exceeded."""
    now = time.time()
    if 'api_call_times' not in st.session_state:
        st.session_state.api_call_times = []
    # Evict timestamps outside the rolling window
    st.session_state.api_call_times = [
        t for t in st.session_state.api_call_times if now - t < _RATE_LIMIT_PERIOD
    ]
    if len(st.session_state.api_call_times) >= _RATE_LIMIT_CALLS:
        wait = _RATE_LIMIT_PERIOD - (now - st.session_state.api_call_times[0])
        st.error(
            f"⏳ Rate limit reached ({_RATE_LIMIT_CALLS} calls/{_RATE_LIMIT_PERIOD}s). "
            f"Please wait {wait:.0f}s before making another request."
        )
        return False
    st.session_state.api_call_times.append(now)
    return True

# --- 3. SECURITY: INPUT SANITIZATION ---
_PGN_STRIP = re.compile(r'[^\x20-\x7E\n\r\t]')   # keep printable ASCII + whitespace
_FEN_STRIP = re.compile(r'[^a-zA-Z0-9/ \-]')       # valid FEN characters only

def sanitize_pgn(text: str) -> str:
    """Strip non-printable characters from PGN input and enforce a maximum length."""
    if not text:
        return ""
    return _PGN_STRIP.sub('', text)[:50_000]

def sanitize_fen(text: str) -> str:
    """Restrict FEN strings to valid characters only."""
    if not text:
        return ""
    return _FEN_STRIP.sub('', text)[:100]

# --- 4. PERFORMANCE: LAZY-LOADED MODULES ---
@st.cache_resource
def _load_stockfish_engine():
    """Lazily initialise Stockfish via chess.engine (no-op if not installed on host)."""
    try:
        import chess.engine
        return chess.engine.SimpleEngine.popen_uci("stockfish")
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_lichess_explorer(fen: str) -> dict | None:
    """Fetch Lichess opening-explorer data for *fen*. Cached for 1 hour."""
    safe_fen = sanitize_fen(fen)
    if not safe_fen:
        return None
    try:
        resp = requests.get(
            "https://explorer.lichess.ovh/lichess",
            params={"fen": safe_fen, "topGames": 0, "recentGames": 0},
            timeout=5,
            headers={"User-Agent": "ScrivChess-Coach-App"},
        )
        return resp.json() if resp.ok else None
    except Exception:
        return None

# --- 5. PERFORMANCE: CACHED DATABASE CONNECTION (zero-idle-CPU heartbeat) ---
@st.cache_resource
def _get_gsheets_conn():
    """Create the GSheets connection once and reuse it — no background polling."""
    return st.connection("gsheets", type=GSheetsConnection)

# --- 6. SEO: DYNAMIC META TAGS + UX: ARIA LABELS ---
def inject_meta_and_aria(title: str, description: str) -> None:
    """Inject Open Graph / Twitter meta tags and ARIA labels via an embedded script."""
    safe_title = title.replace("'", "\\'").replace('"', "&quot;")[:120]
    safe_desc = description.replace("'", "\\'").replace('"', "&quot;")[:160]
    components.html(
        f"""
        <script>
        (function() {{
          // --- dynamic meta tags ---
          const setMeta = (attr, key, val) => {{
            let el = document.querySelector('meta[' + attr + '="' + key + '"]');
            if (!el) {{ el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el); }}
            el.setAttribute('content', val);
          }};
          document.title = '{safe_title}';
          setMeta('name',     'description',    '{safe_desc}');
          setMeta('property', 'og:title',       '{safe_title}');
          setMeta('property', 'og:description', '{safe_desc}');
          setMeta('property', 'og:type',        'website');
          setMeta('name',     'twitter:card',   'summary');
          setMeta('name',     'twitter:title',  '{safe_title}');
          setMeta('name',     'twitter:description', '{safe_desc}');

          // --- ARIA labels on nav buttons (runs after Streamlit renders) ---
          const ARIA_MAP = {{
            'START':    'Go to start of game',
            '⏮':        'Go to start of game',
            'BACK':     'Go to previous move',
            '⬅':        'Go to previous move',
            'FORWARD':  'Go to next move',
            '➡':        'Go to next move',
            'END':      'Go to end of game',
            '⏭':        'Go to end of game',
            'SYNC':     'Sync latest game from Chess.com',
            'ANALYSIS': 'Run deep AI analysis on current game',
            'SHARE':    'Share current position as social post',
          }};
          const labelButtons = () => {{
            (window.parent || window).document.querySelectorAll('button').forEach(btn => {{
              const txt = btn.innerText.toUpperCase();
              for (const [kw, label] of Object.entries(ARIA_MAP)) {{
                if (txt.includes(kw)) {{ btn.setAttribute('aria-label', label); break; }}
              }}
            }});
            // Label the Precision Coaching tab
            (window.parent || window).document.querySelectorAll('[role="tab"]').forEach(tab => {{
              const t = tab.innerText;
              if (t.includes('Precision Coaching'))
                tab.setAttribute('aria-label', 'Precision Coaching — AI-powered game analysis');
              else if (t.includes('ScrivAssistant'))
                tab.setAttribute('aria-label', 'ScrivAssistant — Ask questions about your game');
              else if (t.includes('Stats'))
                tab.setAttribute('aria-label', 'Stats — View your performance history');
            }});
          }};
          setTimeout(labelButtons, 600);
          setTimeout(labelButtons, 2000);
        }})();
        </script>
        """,
        height=0,
    )

# --- 7. SEO: SHARE-MOVE FUNCTION ---
def generate_share_text(pgn: str, move_index: int, analysis: str = "") -> str:
    """Return a social-media-ready PGN summary for the current board position."""
    try:
        game = chess.pgn.read_game(io.StringIO(pgn))
        if not game:
            return ""
        white  = game.headers.get("White",  "White")
        black  = game.headers.get("Black",  "Black")
        result = game.headers.get("Result", "*")
        date   = game.headers.get("Date",   "")
        moves  = list(game.mainline_moves())
        cap    = min(move_index if move_index != 0 else len(moves), 20)  # 0 → full game preview, cap at 20
        temp   = game.board()
        san_moves: list[str] = []
        for i, m in enumerate(moves[:cap]):
            if i % 2 == 0:
                san_moves.append(f"{i // 2 + 1}.")
            san_moves.append(temp.san(m))
            temp.push(m)
        snippet = analysis[:240].replace("\n", " ") if analysis else ""
        ellipsis = "..." if len(moves) > 20 else ""
        return (
            f"♟️ ScrivChess Analysis\n"
            f"{white} vs {black} | {result} | {date}\n\n"
            f"{' '.join(san_moves)}{ellipsis}\n\n"
            f"{snippet}\n\n"
            f"#Chess #ChessAnalysis #ScrivChess"
        )
    except Exception:
        return ""

# --- 8. HELPERS ---
def render_board(board: chess.Board) -> str:
    """Return an HTML string with a base64-encoded SVG chessboard image.

    Highlights the last move when available.
    """
    last_move = board.peek() if board.move_stack else None
    svg = chess.svg.board(board, size=400, lastmove=last_move)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return (
        '<center><img src="data:image/svg+xml;base64,' + b64 + '" '
        'alt="Chess board showing current position" /></center>'
    )

def fetch_latest_game() -> str | None:
    """Fetch the PGN of ScrivShady's most recent Chess.com game.

    Returns the PGN string on success, or None if the request fails or
    no games are found.
    """
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

def generate_ai_content(prompt_text):
    """Generate content using Gemini with graceful fallback for 404/Model Not Found errors."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt_text)
    except Exception as e:
        error_msg = str(e).lower()
        if "404" in error_msg or "not found" in error_msg:
            st.warning("Primary model 'gemini-2.0-flash' not found. Falling back to 'gemini-1.5-flash'.")
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt_text)
        raise

def handle_ai_error(e):
    """Display a user-friendly error message for AI-related errors."""
    error_msg = str(e).lower()
    if "404" in error_msg or "not found" in error_msg:
        st.error("AI Model not found. The model name may have been updated. Please check the configuration.")
    else:
        st.error(f"AI Error: {e}")

# --- 9. SESSION STATE ---
if 'move_index' not in st.session_state:    st.session_state.move_index = 0
if 'current_pgn' not in st.session_state:   st.session_state.current_pgn = ""
if 'analysis_text' not in st.session_state: st.session_state.analysis_text = ""
if 'api_call_times' not in st.session_state: st.session_state.api_call_times = []

# --- 10. INJECT META TAGS & ARIA (runs every render, updates dynamically) ---
_meta_desc = "AI-powered chess coaching and game analysis for ScrivShady."
if st.session_state.current_pgn:
    try:
        _g = chess.pgn.read_game(io.StringIO(st.session_state.current_pgn))
        if _g:
            _w = _g.headers.get("White", "")
            _b = _g.headers.get("Black", "")
            if _w and _b:
                _meta_desc = f"Analysing {_w} vs {_b} — ScrivChess Strategic Insights."
    except Exception:
        pass
inject_meta_and_aria(title="ScrivChess: Strategic Insights", description=_meta_desc)

# --- 11. TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Precision Coaching", "💬 ScrivAssistant", "📊 Stats"])

with tab1:
    st.title("ScrivChess: Strategic Insights")
    
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
            final_pgn = sanitize_pgn(pgn_input if pgn_input else st.session_state.current_pgn)
            if final_pgn:
                st.session_state.current_pgn = final_pgn
                st.session_state.move_index = 0

                api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
                if api_key and api_key.strip():
                    if check_rate_limit():
                        genai.configure(api_key=api_key)
                        try:
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
                                response = generate_ai_content(prompt + final_pgn)
                                st.session_state.analysis_text = response.text
                        except Exception as e:
                            handle_ai_error(e)
                else:
                    st.error("API Key missing! Set the GOOGLE_GENERATIVE_AI_API_KEY environment variable.")

    if st.session_state.analysis_text:
        st.markdown(st.session_state.analysis_text)

    if st.session_state.current_pgn:
        game = chess.pgn.read_game(io.StringIO(st.session_state.current_pgn))
        if game:
            moves = list(game.mainline_moves())
            board = game.board()
            for i in range(st.session_state.move_index):
                board.push(moves[i])

            st.markdown("---")
            st.subheader("🎬 Game Film")
            st.markdown(render_board(board), unsafe_allow_html=True)

            # Lichess Opening Explorer for the current position (lazy-loaded & cached)
            with st.expander("📖 Lichess Opening Explorer", expanded=False):
                with st.spinner("Loading opening data..."):
                    explorer = get_lichess_explorer(board.fen())
                if explorer and explorer.get('moves'):
                    rows = []
                    for m in explorer['moves'][:5]:
                        total = m.get('white', 0) + m.get('draws', 0) + m.get('black', 0)
                        if total:
                            rows.append({
                                "Move":    m.get('san', ''),
                                "White %": round(m['white'] / total * 100, 1),
                                "Draw %":  round(m['draws'] / total * 100, 1),
                                "Black %": round(m['black'] / total * 100, 1),
                                "Games":   total,
                            })
                    if rows:
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("No opening explorer data for this position.")
                else:
                    st.info("No opening explorer data for this position.")

            # Navigation buttons: [<<] [<] counter [>] [>>]
            c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
            with c1:
                if st.button("⏮ START", help="Go to start of game"):
                    st.session_state.move_index = 0
                    st.rerun()
            with c2:
                if st.button("⬅️ BACK", help="Previous move") and st.session_state.move_index > 0:
                    st.session_state.move_index -= 1
                    st.rerun()
            with c3:
                st.write(
                    f"<center>Move {st.session_state.move_index} / {len(moves)}</center>",
                    unsafe_allow_html=True,
                )
            with c4:
                if st.button("FORWARD ➡️", help="Next move") and st.session_state.move_index < len(moves):
                    st.session_state.move_index += 1
                    st.rerun()
            with c5:
                if st.button("END ⏭", help="Go to end of game"):
                    st.session_state.move_index = len(moves)
                    st.rerun()

            # Share Move
            st.markdown("---")
            if st.button("📤 SHARE MOVE", help="Generate a social-media-ready PGN summary"):
                share_text = generate_share_text(
                    st.session_state.current_pgn,
                    st.session_state.move_index,
                    st.session_state.analysis_text,
                )
                if share_text:
                    st.text_area("📋 Copy and share:", value=share_text, height=180)
                else:
                    st.warning("Could not generate share text.")

with tab2:
    st.header("ScrivAssistant")
    q = st.text_input("Ask a question about the game:")
    if q and st.session_state.current_pgn:
        api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
        if api_key and api_key.strip():
            if check_rate_limit():
                genai.configure(api_key=api_key)
                try:
                    res = generate_ai_content(
                        f"Game: {sanitize_pgn(st.session_state.current_pgn)}. Question: {q}"
                    )
                    st.write(res.text)
                except Exception as e:
                    handle_ai_error(e)
        else:
            st.error("API Key missing! Set the GOOGLE_GENERATIVE_AI_API_KEY environment variable.")

with tab3:
    st.header("Visual History")
    try:
        conn = _get_gsheets_conn()
        df = conn.read(spreadsheet=st.secrets["GSHEET_URL"], worksheet="Sheet1")
        if not df.empty:
            st.line_chart(df['Accuracy'], color="#D4AF37")
    except Exception:
        st.info("Play and analyze games to populate stats.")
