
import streamlit as st

PRICE_BLUE = "#1D2E6E"
PRICE_BLUE_2 = "#2563EB"
PRICE_PINK = "#EC007C"
PRICE_DARK = "#15172F"
PRICE_GREEN = "#00B050"
PRICE_ORANGE = "#FF8C00"
PRICE_PURPLE = "#6D28D9"
PRICE_CYAN = "#06B6D4"
PRICE_RED = "#E11D48"
PRICE_GRAY = "#6B7280"


def apply_styles():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:#F3F6FA;
        }}

        .block-container {{
            max-width:100% !important;
            padding:0 1.6rem 2rem 1.6rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background:#FFFFFF;
            border-right:1px solid #DDE3EE;
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top:1rem;
        }}

        .top-header {{
            background:#FFFFFF;
            border-bottom:4px solid {PRICE_PINK};
            padding:18px 24px;
            display:grid;
            grid-template-columns:160px 1fr 430px;
            gap:24px;
            align-items:center;
            margin:0 -1.6rem 0 -1.6rem;
        }}

        .logo-fallback {{
            font-weight:950;
            color:{PRICE_BLUE};
            font-size:25px;
            line-height:.9;
            text-align:center;
        }}

        .header-title {{
            border-left:4px solid {PRICE_PINK};
            padding-left:22px;
        }}

        .header-title .small {{
            color:{PRICE_PINK};
            font-weight:900;
            letter-spacing:5px;
            font-size:13px;
            text-transform:uppercase;
        }}

        .header-title .big {{
            color:{PRICE_BLUE};
            font-weight:950;
            font-size:32px;
            line-height:1;
            letter-spacing:-.5px;
        }}

        .header-title .sub {{
            color:#596174;
            font-weight:650;
            font-size:14px;
            margin-top:4px;
        }}

        .header-controls {{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:14px;
        }}

        .header-card {{
            background:#F8FAFC;
            border:1px solid #DCE3EF;
            border-radius:14px;
            padding:12px 14px;
        }}

        .header-card label {{
            display:block;
            color:{PRICE_GRAY};
            font-size:11px;
            font-weight:800;
            text-transform:uppercase;
            letter-spacing:1.4px;
        }}

        .header-card div {{
            color:{PRICE_BLUE};
            font-size:17px;
            font-weight:950;
            margin-top:3px;
        }}

        .nav-bar {{
            background:{PRICE_BLUE};
            display:flex;
            gap:0;
            overflow-x:auto;
            margin:0 -1.6rem 22px -1.6rem;
            border-bottom:1px solid #0F1B47;
            box-shadow:0 10px 22px rgba(29,46,110,.18);
        }}

        .nav-item {{
            display:inline-block;
            padding:15px 23px;
            color:#DDE8FF !important;
            text-decoration:none !important;
            font-weight:900;
            font-size:15px;
            white-space:nowrap;
            border-bottom:4px solid transparent;
        }}

        .nav-item-active {{
            color:#FFFFFF !important;
            background:#233B86;
            border-bottom-color:{PRICE_PINK};
        }}

        .nav-help {{
            font-size:12px;
            color:#EEF5FF;
            padding:8px 14px 12px 14px;
            background:{PRICE_BLUE};
            margin:0 -1.6rem 0 -1.6rem;
        }}

        .section-title {{
            color:{PRICE_DARK};
            font-size:31px;
            line-height:1.05;
            font-weight:950;
            margin:10px 0 6px 0;
        }}

        .section-subtitle {{
            color:{PRICE_GRAY};
            font-size:15px;
            font-weight:550;
            margin-bottom:18px;
        }}

        .filter-card {{
            background:#FFFFFF;
            border:1px solid #E1E7F0;
            border-radius:18px;
            padding:16px;
            margin-bottom:20px;
            box-shadow:0 8px 18px rgba(17,24,39,.04);
        }}

        .hero-blue {{
            background:linear-gradient(135deg, {PRICE_BLUE} 0%, #2546A8 70%, {PRICE_PINK} 160%);
            border-radius:22px;
            padding:24px;
            color:#FFFFFF;
            margin-bottom:20px;
            box-shadow:0 18px 38px rgba(29,46,110,.25);
        }}

        .hero-blue h2 {{
            margin:0;
            font-size:28px;
            font-weight:950;
            color:#FFFFFF;
        }}

        .hero-blue p {{
            margin:6px 0 0 0;
            color:#E7ECFF;
            font-weight:650;
        }}

        .hero-grid {{
            display:grid;
            grid-template-columns:repeat(5, 1fr);
            gap:12px;
            margin-top:18px;
        }}

        .hero-mini {{
            background:rgba(255,255,255,.12);
            border:1px solid rgba(255,255,255,.20);
            border-radius:15px;
            padding:12px;
        }}

        .hero-mini-label {{
            opacity:.78;
            font-size:12px;
            font-weight:850;
        }}

        .hero-mini-value {{
            font-size:20px;
            font-weight:950;
            margin-top:3px;
        }}

        .kpi-grid {{
            display:grid;
            grid-template-columns:repeat(5, 1fr);
            gap:16px;
            margin-bottom:20px;
        }}

        .kpi-card {{
            background:#FFFFFF;
            border:1px solid #E1E7F0;
            border-radius:20px;
            padding:18px;
            box-shadow:0 10px 24px rgba(17,24,39,.06);
            min-height:165px;
            position:relative;
            overflow:hidden;
        }}

        .kpi-card:after {{
            content:"";
            position:absolute;
            right:-35px;
            top:-35px;
            width:100px;
            height:100px;
            border-radius:50%;
            background:var(--soft);
        }}

        .kpi-top {{
            display:flex;
            align-items:center;
            gap:12px;
            position:relative;
            z-index:1;
        }}

        .kpi-icon {{
            width:52px;
            height:52px;
            border-radius:16px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:var(--accent);
            color:#FFFFFF;
            font-size:23px;
            font-weight:950;
            box-shadow:0 10px 22px var(--shadow);
        }}

        .kpi-label {{
            color:var(--accent);
            font-size:14px;
            line-height:1.1;
            font-weight:950;
        }}

        .kpi-value {{
            color:{PRICE_DARK};
            font-size:28px;
            font-weight:950;
            margin-top:16px;
            letter-spacing:-.5px;
            position:relative;
            z-index:1;
        }}

        .kpi-note {{
            color:{PRICE_GRAY};
            font-size:13px;
            font-weight:650;
            margin-top:5px;
        }}

        .progress {{
            height:9px;
            background:#EDF2F7;
            border-radius:99px;
            margin-top:14px;
            overflow:hidden;
        }}

        .progress > div {{
            height:100%;
            background:var(--accent);
            width:var(--pct);
            border-radius:99px;
        }}

        .delta {{
            display:inline-block;
            margin-top:10px;
            padding:5px 9px;
            border-radius:10px;
            background:var(--soft);
            color:var(--accent);
            font-size:12px;
            font-weight:950;
        }}

        .panel {{
            background:#FFFFFF;
            border:1px solid #E1E7F0;
            border-radius:20px;
            padding:20px;
            box-shadow:0 10px 24px rgba(17,24,39,.05);
            margin-bottom:18px;
        }}

        .panel-title {{
            color:{PRICE_DARK};
            font-size:18px;
            font-weight:950;
            margin-bottom:14px;
        }}

        .week-grid {{
            display:grid;
            grid-template-columns:repeat(4, 1fr);
            gap:16px;
            margin-bottom:20px;
        }}

        .week-card {{
            background:#FFFFFF;
            border:1px solid #E1E7F0;
            border-radius:18px;
            overflow:hidden;
            box-shadow:0 10px 22px rgba(17,24,39,.06);
        }}

        .week-head {{
            background:#3F3F91;
            color:#FFFFFF;
            padding:13px 16px;
            text-align:center;
            font-weight:950;
        }}

        .week-line {{
            display:grid;
            grid-template-columns:1fr auto auto;
            gap:10px;
            align-items:center;
            padding:12px 16px;
            border-bottom:1px solid #EDF2F7;
        }}

        .week-label {{
            color:#666;
            font-size:12px;
            font-weight:900;
            text-transform:uppercase;
        }}

        .week-value {{
            color:#3F3F91;
            font-size:17px;
            font-weight:950;
        }}

        .week-delta {{
            font-size:11px;
            font-weight:950;
        }}

        .rank-row {{
            display:grid;
            grid-template-columns:150px 1fr 72px;
            gap:12px;
            align-items:center;
            padding:10px 0;
            border-bottom:1px solid #EDF2F7;
        }}

        .rank-name {{
            color:{PRICE_DARK};
            font-weight:850;
            font-size:13px;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }}

        .rankbar {{
            height:10px;
            background:#EDF2F7;
            border-radius:99px;
            overflow:hidden;
        }}

        .rankbar-fill {{
            height:100%;
            background:var(--accent);
            width:var(--w);
            border-radius:99px;
        }}

        .rank-value {{
            text-align:right;
            color:{PRICE_DARK};
            font-weight:950;
            font-size:13px;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius:14px;
            overflow:hidden;
        }}

        .user-card {{
            background:#FFF7ED;
            border:1px solid #FED7AA;
            border-radius:18px;
            padding:16px;
            margin:12px 0;
        }}

        @media (max-width:1200px) {{
            .top-header {{
                grid-template-columns:110px 1fr;
            }}
            .header-controls {{
                display:none;
            }}
            .kpi-grid {{
                grid-template-columns:repeat(2, 1fr);
            }}
            .hero-grid {{
                grid-template-columns:repeat(2, 1fr);
            }}
            .week-grid {{
                grid-template-columns:repeat(2, 1fr);
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
