import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import concurrent.futures
import stocksense_engine as engine

# Cached data fetcher to reduce API calls
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_cached_data(ticker, period="1y"):
    """Wrapper for cached yfinance data."""
    ingest = engine.DataIngestion(ticker, period)
    return ingest.fetch_data()

# ============================================================================
# 1. PAGE CONFIG & CUSTOM CSS
# ============================================================================
st.set_page_config(
    page_title="StockSense Pro: Smart Money Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    'bg_main': '#0E1117',
    'bg_card': '#1E232F',
    'text_primary': '#FFFFFF',
    'text_secondary': '#9CA3AF',
    'accent_red': '#FF4B4B',
    'accent_green': '#00C853',
    'accent_warning': '#FFA000',
    'grid_color': '#2C3342'
}

# SECTOR MAPPING (Expanded Broad Universe: Big, Mid, Small Caps)
SECTOR_MAP = {
    "Financials": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "BBTN.JK", "PNBN.JK", "BTPS.JK", "ARTO.JK", "BNGA.JK", "NISP.JK", "BJBR.JK", "BJTM.JK", "BFIN.JK", "TUGU.JK", "ADMF.JK", "AMAR.JK", "BBYB.JK", "BCIC.JK", "BNLI.JK", "PNBS.JK", "AGRO.JK", "MAYA.JK"],
    "Energy": ["ADRO.JK", "PTBA.JK", "PGAS.JK", "MEDC.JK", "AKRA.JK", "ITMG.JK", "HRUM.JK", "BUMI.JK", "INDY.JK", "ELSA.JK", "DEWA.JK", "DOID.JK", "ENRG.JK", "ABMM.JK", "TOBA.JK", "RAJA.JK", "KKGI.JK", "MBSS.JK", "PSI.JK", "SGER.JK", "IATA.JK", "WINE.JK", "GTSI.JK"],
    "Basic Materials": ["MDKA.JK", "ANTM.JK", "INCO.JK", "TINS.JK", "MBMA.JK", "NCKL.JK", "INTP.JK", "SMGR.JK", "BRPT.JK", "TPIA.JK", "ESSA.JK", "MDKI.JK", "IFSH.JK", "KRAS.JK", "LTLS.JK", "ZINC.JK", "DKFT.JK", "NIKL.JK", "TYRE.JK", "BRMS.JK", "UNNU.JK", "NICL.JK"],
    "Consumer Non-Cyclicals": ["ICBP.JK", "INDF.JK", "MYOR.JK", "KLBF.JK", "UNVR.JK", "CPIN.JK", "JPFA.JK", "HMSP.JK", "GGRM.JK", "CMRY.JK", "SIDO.JK", "AMRT.JK", "MIDI.JK", "ROTI.JK", "STTP.JK", "CLEO.JK", "ULTJ.JK", "GOOD.JK", "WOOD.JK", "AISA.JK"],
    "Telecommunications": ["TLKM.JK", "ISAT.JK", "EXCL.JK", "MTEL.JK", "FREN.JK", "TBIG.JK", "TOWR.JK", "CENT.JK", "SUPR.JK", "LINK.JK", "GHON.JK"],
    "Technology": ["GOTO.JK", "EMTK.JK", "BUKA.JK", "BELI.JK", "WIRG.JK", "MTDL.JK", "MLPT.JK", "DMMX.JK", "GLVA.JK", "KIOS.JK", "UVCR.JK", "DIVA.JK", "NFCX.JK"],
    "Infrastructure": ["JSMR.JK", "WIKA.JK", "PTPP.JK", "ADHI.JK", "META.JK", "CMNP.JK", "IPCC.JK", "IPC.JK", "WEGE.JK", "TOTL.JK", "NRCA.JK", "ACST.JK", "IDPR.JK", "POWR.JK", "KEEN.JK"],
    "Healthcare": ["KLBF.JK", "MIKA.JK", "HEAL.JK", "SILO.JK", "SIDO.JK", "SAME.JK", "RDTX.JK", "PRDA.JK", "TSPC.JK", "KAEF.JK", "IRRA.JK", "PEHA.JK", "BMHS.JK"],
    "Properties": ["CTRA.JK", "BSDE.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "LPKR.JK", "DMAS.JK", "KIJA.JK", "BEST.JK", "APLN.JK", "PANI.JK", "DILD.JK", "MKPI.JK", "RALS.JK", "LPCK.JK", "GWSA.JK", "MTLA.JK"],
    "Automotive & Heavy": ["ASII.JK", "UNTR.JK", "HEXA.JK", "AUTO.JK", "DRMA.JK", "IMAS.JK", "SMSM.JK", "GJTL.JK", "MPMX.JK", "ALDO.JK"]
}

st.markdown(f"""
<style>
    /* GLOBAL FONTS & THEME */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background-color: #0E1117;
        background-image: radial-gradient(circle at 50% 0%, #1c2333 0%, #0E1117 70%);
        background-attachment: fixed;
    }}
    
    /* REMOVE STREAMLIT PADDING */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 5rem;
    }}

    /* CUSTOM CARDS */
    .dashboard-card {{
        background-color: #161B22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }}
    
    /* GRADIENT TITLES */
    .gradient-text {{
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }}
    .sub-gradient-text {{
        background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
        font-size: 1.2rem;
    }}

    /* CUSTOM METRICS GRID */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 2rem;
    }}
    
    .metric-box {{
        background: linear-gradient(145deg, #1E232F, #161B22);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        text-align: left;
        transition: transform 0.2s;
    }}
    
    .metric-box:hover {{
        transform: translateY(-2px);
        border-color: #58a6ff;
    }}

    .metric-label {{
        color: #8b949e;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }}
    
    .metric-value {{
        color: #f0f6fc;
        font-size: 1.8rem;
        font-weight: 700;
    }}
    
    .metric-delta {{
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 5px;
    }}
    
    .delta-pos {{ color: #3fb950; }}
    .delta-neg {{ color: #f85149; }}
    .delta-neu {{ color: #8b949e; }}

    /* SIDEBAR POLISH */
    section[data-testid="stSidebar"] {{
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }}
    
    /* BUTTONS */
    .stButton button {{
        background: linear-gradient(45deg, #238636, #2ea043);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        background: linear-gradient(45deg, #2ea043, #3fb950);
        box-shadow: 0 0 15px rgba(46, 160, 67, 0.4);
        transform: scale(1.02);
    }}

</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. HELPER FUNCTIONS & CHARTING
# ============================================================================

def plot_advanced_charts(df, ticker):
    """Generates the 4-panel Smart Money chart."""
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=("", "", "", "")
    )
    
    # 1. Price + VWAP + BB
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Price', increasing_line_color=COLORS['accent_green'], decreasing_line_color=COLORS['accent_red']
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['vwap'], mode='lines', name='VWAP (20)',
        line=dict(color=COLORS['accent_warning'], width=1.5)
    ), row=1, col=1)

    # SMA 200 (Long Term Trend)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['sma_200'], mode='lines', name='SMA 200',
        line=dict(color='white', width=2)
    ), row=1, col=1)
    
    # BB
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(119,136,153,0.1)', showlegend=False), row=1, col=1)

    # 2. RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#58a6ff', width=1.5), name='RSI'), row=2, col=1)
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=70, y1=70, line=dict(color="white", dash="dot", width=1), row=2, col=1)
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=30, y1=30, line=dict(color="white", dash="dot", width=1), row=2, col=1)

    # 3. CMF (Smart Money Accumulation/Distribution)
    # Area Chart Logic: Green if > 0, Red if < 0.
    cmf_colors = [COLORS['accent_green'] if val >= 0 else COLORS['accent_red'] for val in df['cmf']]
    
    # We use Bar for area-like effect or filled Scatter. Bar is clearer for zero-line crossover.
    fig.add_trace(go.Bar(
        x=df.index, y=df['cmf'],
        name='CMF',
        marker_color=cmf_colors
    ), row=3, col=1)
    
    # Zero Line for CMF
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=0, y1=0, line=dict(color="white", width=1), row=3, col=1)
    
    # MFI is now secondary or just used in logic, Panel 3 is CMF as requested.

    # 4. RVOL
    colors = [COLORS['accent_warning'] if v >= 1.5 else '#4b5563' for v in df['rvol']]
    fig.add_trace(go.Bar(x=df.index, y=df['rvol'], name='RVOL', marker_color=colors), row=4, col=1)
    fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1], y0=1.0, y1=1.0, line=dict(color="white", width=1), row=4, col=1)

    fig.update_layout(template='plotly_dark', height=800, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, paper_bgcolor=COLORS['bg_main'], plot_bgcolor=COLORS['bg_main'])
    fig.update_xaxes(showgrid=False, rangeslider_visible=False)
    fig.update_yaxes(showgrid=True, gridcolor='#2C3342')
    
    return fig

# ============================================================================
# 3. MAIN APP LOGIC
# ============================================================================

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'screener'
    if 'selected_ticker' not in st.session_state:
        st.session_state['selected_ticker'] = None

    # Sidebar Navigation
    with st.sidebar:
        st.title("🛡️ StockSense Pro")
        st.caption("Institutional Smart Money Tracker")
        
        mode = st.radio("Navigation", ["🔍 Smart Screener", "📈 Chart Deep Dive"], 
                        index=0 if st.session_state['page'] == 'screener' else 1)
        
        if mode == "🔍 Smart Screener":
            st.session_state['page'] = 'screener'
        else:
            st.session_state['page'] = 'deep_dive'
            
        st.divider()
        st.info("System Status: ONLINE\nEngine: v2.1.0 (Alpha)")

    # ------------------------------------------------------------------
    # PAGE 1: SMART SCREENER
    # ------------------------------------------------------------------
    if st.session_state['page'] == 'screener':
        # Header
        st.markdown('<div class="gradient-text">StockSense Pro</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-gradient-text">Institutional Smart Money Flow Screener</div>', unsafe_allow_html=True)
        st.write("")
        
        # --- INPUT SECTION (CARD) ---
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            # 1. Sector Selection
            sector_options = ["Manual Input / None"] + list(SECTOR_MAP.keys())
            selected_sector = st.selectbox("📌 Select Sector (or use Manual Input)", sector_options)
            
            # 2. Manual Input
            user_tickers = st.text_area(
                "📝 Or Input Tickers Manually (Comma separated, overrides Sector)", 
                height=70,
                placeholder="e.g. BBCA.JK, BBRI.JK (Leave empty to use Sector Scan)"
            )
        
        with col2:
            st.write("")
            st.write("")
            st.write("") # Spacing
            scan_btn = st.button("🚀 SCAN MARKET", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if scan_btn:
             scan_mode = "MANUAL"
             final_ticker_list = []
             
             # --- DECISION ENGINE ---
             if user_tickers.strip():
                 # Priority 1: User Manual Input
                 scan_mode = "MANUAL"
                 raw_list = user_tickers.upper().replace(" ", "").split(',')
                 final_ticker_list = [t for t in raw_list if t]
                
            elif selected_sector != "Manual Input / None":
                # Priority 2: Sector Selection
                scan_mode = "SECTOR_TOP10"
                final_ticker_list = SECTOR_MAP[selected_sector]
                
            else:
                st.warning("⚠️ Please select a Sector OR input tickers manually.")
                st.stop()
            
            # --- EXECUTION ---
            st.markdown("### 🔄 Scanning Market...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            valid_results = []
            cleaned_tickers = list(set(final_ticker_list)) # Remove duplicates
            total_tickers = len(cleaned_tickers)
            
            import concurrent.futures
            
            # Using ThreadPool in the App to control Progress Bar
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                ingest = engine.DataIngestion() 
                analyzer = engine.SmartMoneyAnalyzer()
                
                # Submit all tasks
                future_to_ticker = {executor.submit(ingest.fetch_data, t): t for t in cleaned_tickers}
                
                completed_count = 0
                
                for future in concurrent.futures.as_completed(future_to_ticker):
                    t = future_to_ticker[future]
                    completed_count += 1
                    
                    # Update Progress
                    progress = int((completed_count / total_tickers) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Scanning {t} ({completed_count}/{total_tickers})")
                    
                    try:
                        df = future.result()
                        
                        # 1. PRE-SCREENING GATE (Safety Filter)
                        is_safe, reason = ingest.check_safety_criteria(df)
                        
                        if is_safe:
                            # 2. RUN HEAVY CALCULATIONS
                            df = ingest.calculate_indicators(df)
                            
                            # 3. GET LAST ROW & ANALYZE
                            latest = df.iloc[-1].to_dict()
                            recent_14d = df.iloc[-14:]
                            latest['max_rvol_14d'] = recent_14d['rvol'].max() if not recent_14d.empty else 0
                            
                            analysis = analyzer.analyze_single_row(pd.Series(latest))
                            
                            # 4. APPEND TO LIST
                            valid_results.append({
                                "Ticker": t,
                                "Close": f"{latest['close']:,.0f}",
                                "RVOL (Today)": round(latest['rvol'], 2),
                                "Max RVOL (14D)": round(recent_14d['rvol'].max(), 2),
                                "MFI": round(latest['mfi'], 1),
                                "CMF": round(latest['cmf'], 2),
                                "Status": analysis['status'],
                                "Signal Score": analysis['score']
                            })
                            
                    except Exception as e:
                        # Fail silently for individual stocks to keep loop running
                        continue

            progress_bar.empty()
            status_text.empty()
            
            if not valid_results:
                st.warning("No stocks passed the Safety Filters (Price > 60, Liquidity > 2B). Try another sector.")
            else:
                df_res = pd.DataFrame(valid_results)
                
                 # --- RANKING ALGORITHM (Top 10) ---
                if scan_mode == "SECTOR_TOP10":
                    # Sort by Score (Desc) then RVOL (Desc)
                    df_res = df_res.sort_values(by=["Signal Score", "RVOL (Today)"], ascending=[False, False])
                    # Slice Top 10
                    df_res = df_res.head(10)
                    st.success(f"✅ Displaying Top 10 High-Momentum Stocks in {selected_sector}")
                else:
                    # Manual Mode: Sort by likely interesting ones
                    df_res = df_res.sort_values(by="Max RVOL (14D)", ascending=False)
                    
                st.session_state['scan_results'] = df_res
        
        # Display Results
        if 'scan_results' in st.session_state:
            res_df = st.session_state['scan_results']
            
            # Interactive Dataframe
            st.markdown("### 📊 Scanning Results")
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            event = st.dataframe(
                res_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn(
                        "AI Status",
                        help="Smart Money Interpretation",
                        validate="^(ACCUMULATION|DISTRIBUTION|MARKUP|NEUTRAL)$"
                    ),
                    "RVOL (Today)": st.column_config.NumberColumn(
                        "RVOL (Today)",
                        format="%.2f"
                    ),
                    "Max RVOL (14D)": st.column_config.ProgressColumn(
                        "Max RVOL (14D)",
                        help="Highest Relative Volume in last 2 weeks",
                        format="%.2f",
                        min_value=0,
                        max_value=5,
                    ),
                     "Signal Score": st.column_config.NumberColumn(
                        "Score",
                        format="%d ⭐"
                    )
                },
                selection_mode="single-row",
                on_select="rerun"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Handling Selection
            if len(event.selection['rows']) > 0:
                idx = event.selection['rows'][0]
                selected_ticker = res_df.iloc[idx]['Ticker']
                st.session_state['selected_ticker'] = selected_ticker
                st.session_state['page'] = 'deep_dive'
                st.rerun()

            st.caption("💡 Tip: Select a row to open the Deep Dive Chart Analysis.")

    # ------------------------------------------------------------------
    # PAGE 2: TECHNICAL DEEP DIVE
    # ------------------------------------------------------------------
    elif st.session_state['page'] == 'deep_dive':
        ticker = st.session_state['selected_ticker']
        if not ticker:
            st.warning("No ticker selected. Please go back to Screener.")
            if st.button("⬅️ Back to Screener"):
                st.session_state['page'] = 'screener'
                st.rerun()
            return

        # Header
        col_back, col_title = st.columns([1, 6])
        with col_back:
            if st.button("⬅️ Back"):
                st.session_state['page'] = 'screener'
                st.rerun()
        with col_title:
            st.title(f"⚡ {ticker} • Institutional Deep Dive")

        # Fetch Full History for Charting
        ingest = engine.DataIngestion(ticker, period="1y")
        df = ingest.fetch_data()
        
        if df.empty:
            st.error(f"Failed to load data for {ticker}")
            return
            
        df = ingest.calculate_indicators(df)
        
        # AI Analysis
        last_row = df.iloc[-1]
        analyzer = engine.SmartMoneyAnalyzer()
        analysis = analyzer.analyze_single_row(last_row)
        
        # Top Metrics Row (Custom HTML)
        price_change = last_row['close'] - df.iloc[-2]['close']
        price_delta_class = "delta-pos" if price_change >= 0 else "delta-neg"
        
        rvol_val = last_row['rvol']
        rvol_delta_class = "delta-pos" if rvol_val > 1.5 else "delta-neu"
        
        mfi_val = last_row['mfi']
        mfi_status = "OVERSOLD" if mfi_val < 20 else ("OVERBOUGHT" if mfi_val > 80 else "NEUTRAL")
        mfi_class = "delta-pos" if mfi_val < 20 else "delta-neu"
        
        trend_status = "BULLISH" if last_row['close'] > last_row['vwap'] else "BEARISH"
        trend_class = "delta-pos" if trend_status == "BULLISH" else "delta-neg"

        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">Current Price</div>
                <div class="metric-value">{last_row['close']:,.0f}</div>
                <div class="metric-delta {price_delta_class}">{price_change:+,.0f} IDR</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Relative Volume</div>
                <div class="metric-value">{rvol_val:.2f}x</div>
                <div class="metric-delta {rvol_delta_class}">{'🔥 SPIKE' if rvol_val > 1.5 else 'NORMAL'}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Money Flow Index</div>
                <div class="metric-value">{mfi_val:.1f}</div>
                <div class="metric-delta {mfi_class}">{mfi_status}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Trend vs VWAP</div>
                <div class="metric-value" style="font-size: 1.5rem;">{trend_status}</div>
                <div class="metric-delta {trend_class}">{last_row['close']:,.0f} vs {last_row['vwap']:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Main Chart
        st.markdown("### 📉 Smart Money Structure")
        st.plotly_chart(plot_advanced_charts(df, ticker), use_container_width=True)
        
        # Narrative Box
        st.markdown(f"""
        <div style="background-color: #1E232F; padding: 20px; border-radius: 10px; border-left: 5px solid {COLORS['accent_green'] if analysis['score'] > 0 else COLORS['accent_red']};">
            <h4 style="margin:0; color: white;">🤖 AI Interpretative Logic</h4>
            <p style="color: #E6EDF3; font-size: 1.1rem; margin-top: 10px;">
                <strong>Detected Status: {analysis['status']}</strong><br>
                {analysis['details']}
            </p>
            <hr style="border-color: #30363d;">
            <p style="font-size: 0.9rem; color: #9CA3AF;">
                <em>Logic: RVOL > 1.5 indicates institutional interest. MFI Divergence checks for hidden accumulation. Price > VWAP confirms trend direction.</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Disclaimer Footer
        st.divider()
        st.caption("""
        ⚠️ **Disclaimer**: This tool is for educational and research purposes only. 
        It does not constitute financial advice. Past performance does not guarantee future results. 
        Always do your own research before making investment decisions.
        """)

if __name__ == "__main__":
    main()
