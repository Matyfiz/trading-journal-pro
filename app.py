import streamlit as st
import pandas as pd
import calendar
import time
import os
import re
from datetime import datetime, date, timedelta
import altair as alt

# --- NOWE BIBLIOTEKI DLA GOOGLE SHEETS ---
import gspread
from google.oauth2.service_account import Credentials

# --- 1. KONFIGURACJA I CSS (CYBERPUNK DARK) ---
st.set_page_config(page_title="Trader PRO", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        :root {
            --bg-dark: #0d1117; --bg-card: #161b22; --border: #30363d; --text-main: #e6edf3; --text-sub: #8b949e; 
            --neon-green: #2ea043; --neon-red: #da3633; --accent: #1f6feb;
            --badge-long-bg: rgba(46, 160, 67, 0.2); --badge-long-text: #3fb950;
            --badge-short-bg: rgba(218, 54, 51, 0.2); --badge-short-text: #f85149;
            --badge-time-bg: rgba(56, 139, 253, 0.15); --badge-time-text: #58a6ff;
        }
        .stApp { background-color: var(--bg-dark); color: var(--text-main); }
        
        /* Sidebar fix */
        section[data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid var(--border); }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label {
            background-color: transparent; border: 1px solid transparent; padding: 12px 20px;
            border-radius: 4px; margin-bottom: 6px; transition: all 0.3s; cursor: pointer;
            color: var(--text-sub); font-weight: 500; display: flex; align-items: center;
            filter: grayscale(100%) opacity(0.7); 
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
            background: linear-gradient(90deg, rgba(31, 111, 235, 0.15) 0%, transparent 100%);
            border-left: 3px solid rgba(31, 111, 235, 0.5); color: var(--text-main); filter: grayscale(0%) opacity(1);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
            background: linear-gradient(90deg, rgba(31, 111, 235, 0.25) 0%, rgba(31, 111, 235, 0.0) 90%);
            border-left: 3px solid var(--accent); color: white; font-weight: 600; filter: grayscale(0%) opacity(1);
        }

        /* Karty */
        .custom-card { background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 15px; text-align: center; height: 100%; transition: transform 0.2s; }
        .custom-card:hover { transform: translateY(-3px); border-color: var(--accent); }
        .card-title { color: var(--text-sub); font-size: 0.7rem; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; }
        .card-val { font-size: 1.5rem; font-weight: 800; font-family: 'Courier New', monospace; margin-bottom: 4px; }
        .val-up { color: var(--neon-green); } .val-down { color: var(--neon-red); }
        
        /* Tabela transakcji */
        .trade-table-container { background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; font-size: 0.85rem; margin-top: 10px; }
        .trade-table-header { display: grid; grid-template-columns: 0.9fr 0.9fr 0.7fr 0.8fr 0.8fr 1fr 1fr 0.9fr 1fr 0.7fr; padding: 12px 10px; background-color: rgba(48, 54, 61, 0.3); color: var(--text-sub); font-weight: 700; text-transform: uppercase; font-size: 0.7rem; border-bottom: 1px solid var(--border); }
        .trade-table-row { display: grid; grid-template-columns: 0.9fr 0.9fr 0.7fr 0.8fr 0.8fr 1fr 1fr 0.9fr 1fr 0.7fr; padding: 10px 10px; border-bottom: 1px solid var(--border); align-items: center; transition: background-color 0.1s; }
        .trade-table-row:hover { background-color: rgba(48, 54, 61, 0.2); }
        
        /* Badges (Poprawione) */
        .badge { display: inline-block; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem; text-align: center; min-width: 60px; }
        .badge-long { background-color: var(--badge-long-bg); color: var(--badge-long-text); border: 1px solid rgba(46, 160, 67, 0.3); }
        .badge-short { background-color: var(--badge-short-bg); color: var(--badge-short-text); border: 1px solid rgba(218, 54, 51, 0.3); }
        .badge-time { background-color: var(--badge-time-bg); color: var(--badge-time-text); border: 1px solid rgba(88, 166, 255, 0.3); padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-align: center; display: inline-block; min-width: 60px; }
        
        .col-pnl { font-family: 'Courier New', monospace; font-weight: 800; display: flex; align-items: center; gap: 4px; }
        .pnl-green { color: var(--neon-green); } .pnl-red { color: var(--neon-red); }
        
        /* Kalendarz (NAPRAWIONY GRID) */
        .calendar-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; margin-top: 10px; }
        .tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; margin-top: 10px; }
        .grid-header { text-align: center; font-size: 0.7rem; color: var(--text-sub); padding-bottom: 5px; font-weight: bold; text-transform: uppercase; }
        .day-card { background-color: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 8px; min-height: 80px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s; }
        .day-card:hover { border-color: var(--accent); }
        .day-num { font-size: 0.8rem; font-weight: bold; color: var(--text-sub); }
        .day-val { font-size: 0.9rem; font-weight: 800; font-family: 'Courier New', monospace; text-align: right; }
        .week-summary { background-color: rgba(31, 111, 235, 0.1); border: 1px solid rgba(31, 111, 235, 0.3); border-radius: 6px; padding: 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; }

        /* Wizualizacja pozycji */
        .visual-bar-container { height: 300px; width: 60px; background-color: #0d1117; border: 1px solid var(--border); border-radius: 4px; position: relative; display: flex; flex-direction: column; margin: 0 auto; }
        .visual-segment { width: 100%; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; position: relative; }
        .visual-profit { background-color: var(--neon-green); opacity: 0.2; border: 1px solid var(--neon-green); }
        .visual-loss { background-color: var(--neon-red); opacity: 0.2; border: 1px solid var(--neon-red); }
        .price-label { position: absolute; left: 70px; font-size: 12px; white-space: nowrap; font-family: 'Courier New', monospace; font-weight: bold; }
        .entry-line { height: 2px; background-color: #fff; width: 80px; position: absolute; left: -10px; z-index: 10; }
        
        canvas { filter: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIKA I BAZA DANYCH (INTEGRACJA GOOGLE SHEETS) ---
POLISH_MONTHS = {1: 'Styczeń', 2: 'Luty', 3: 'Marzec', 4: 'Kwiecień', 5: 'Maj', 6: 'Czerwiec', 7: 'Lipiec', 8: 'Sierpień', 9: 'Wrzesień', 10: 'Październik', 11: 'Listopad', 12: 'Grudzień'}

# --- FUNKCJA DO POŁĄCZENIA Z GOOGLE SHEETS (POPRAWIONA) ---
@st.cache_resource(ttl=3600) 
def get_sheets_client():
    try:
        # Pobieramy sekrety jako słownik
        creds_json = dict(st.secrets["gcp_service_account"])
        
        # 1. FIX: Naprawa znaków nowej linii (najczęstsza przyczyna błędu w Streamlit)
        if "private_key" in creds_json:
            creds_json["private_key"] = creds_json["private_key"].replace("\\n", "\n")

        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_info(creds_json, scopes=scopes)
        return gspread.authorize(credentials)
        
    except Exception as e:
        # 2. FIX: Wyświetlamy PRAWDZIWY błąd zamiast ogólnego komunikatu
        st.error(f"❌ Szczegóły błędu technicznego: {e}")
        return None

# --- FUNKCJA ODCZYTU DANYCH (ZAMIAST get_trades) ---
@st.cache_data(ttl=30) 
def get_trades_from_gsheet():
    client = get_sheets_client()
    if client is None: return pd.DataFrame()
    
    try:
        spreadsheet_id = st.secrets["spreadsheet"]["id"]
        sheet = client.open_by_key(spreadsheet_id).worksheet('Arkusz1') 
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty or 'id' not in df.columns:
            # Zapewnia, że pusta tabela ma właściwe kolumny
            empty_cols = ['id', 'date', 'entry_date', 'symbol', 'direction', 'setup', 'entry_price', 'exit_price', 'stop_loss', 'position_size', 'fees', 'notes', 'pnl', 'r_multiple']
            return pd.DataFrame(columns=empty_cols)
            
        # Konwersja dat i dodanie kolumn analitycznych
        df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
        df['entry_dt'] = pd.to_datetime(df['entry_date'], errors='coerce')
        df = df.dropna(subset=['date_dt'])
        
        df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        df['year_int'] = df['date_dt'].dt.year.astype(int)
        df['month_int'] = df['date_dt'].dt.month.astype(int)
        df['date_only'] = df['date_dt'].dt.date
        df['hold_hours'] = df.apply(lambda x: (x['date_dt'] - x['entry_dt']).total_seconds()/3600 if pd.notnull(x['entry_dt']) else 0, axis=1)
        
        df = df.sort_values('date_dt', ascending=False)
        return df

    except Exception as e:
        st.error(f"Błąd odczytu Arkusza Google: {e}")
        return pd.DataFrame()

# --- FUNKCJA ZAPISU DO GOOGLE SHEETS ---
def add_trade_to_gsheet(data, current_df):
    client = get_sheets_client()
    if client is None: return False
    
    try:
        spreadsheet_id = st.secrets["spreadsheet"]["id"]
        sheet = client.open_by_key(spreadsheet_id).worksheet('Arkusz1')
    
        # 1. Anty-Duplikat
        is_duplicate = current_df[
            (current_df['date'] == data['date']) &
            (current_df['symbol'] == data['symbol']) &
            (current_df['direction'] == data['direction']) &
            (abs(current_df['pnl'] - data['pnl']) < 0.01)
        ].shape[0] > 0
        
        if is_duplicate: return False

        # 2. Ustalenie nowego ID
        max_id = current_df['id'].max() if not current_df.empty and 'id' in current_df.columns else 0
        data['id'] = max_id + 1
        
        # 3. Przygotowanie wiersza
        cols_to_keep = ['id', 'date', 'entry_date', 'symbol', 'direction', 'setup', 'entry_price', 'exit_price', 'stop_loss', 'position_size', 'fees', 'notes', 'pnl', 'r_multiple']
        new_row = [data.get(col, '') for col in cols_to_keep]

        # 4. Zapis
        sheet.append_row(new_row, value_input_option='USER_ENTERED')
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Błąd zapisu do Google Sheets: {e}")
        return False
    
# Zastąpienie starych funkcji nowymi
get_trades = get_trades_from_gsheet
add_trade_to_db = add_trade_to_gsheet

# --- POZOSTAŁA LOGIKA ---
def calculate_streaks(df):
    if df.empty: return 0, 0
    df = df.sort_values('date_dt')
    pnl = df['pnl'].values
    cw, mw, cl, ml = 0, 0, 0, 0
    for val in pnl:
        if val > 0: cw += 1; cl = 0; mw = max(mw, cw)
        elif val < 0: cl += 1; cw = 0; ml = max(ml, cl)
    return mw, ml

def format_duration(hours):
    if pd.isna(hours) or hours == 0: return "-"
    if hours < 1: return f"{int(hours*60)}m"
    if hours > 24: return f"{hours/24:.1f}d"
    return f"{hours:.1f}h"

def get_date_range(preset):
    today = date.today()
    if preset == "Dzisiaj": return today, today
    elif preset == "Wczoraj": return today - timedelta(days=1), today - timedelta(days=1)
    elif preset == "Obecny Tydzień": return today - timedelta(days=today.weekday()), today
    elif preset == "Obecny Miesiąc": return today.replace(day=1), today
    elif preset == "Obecny Rok": return today.replace(month=1, day=1), today
    return None, None

# --- 3. RENDERERY HTML ---
def render_card(title, value, sub="", is_curr=True):
    val_num = float(value) if isinstance(value, (int, float)) else 0
    if isinstance(value, str):
        try: val_num = float(value.replace('$','').replace('%',''))
        except: val_num = 0
    cls = "val-neutral"
    if "Win Rate" in title or "Profit Factor" in title:
        if val_num >= 1.5 or ("Win" in title and val_num > 50): cls = "val-up"
        elif val_num < 1.0 or ("Win" in title and val_num < 40): cls = "val-down"
    elif is_curr:
        if val_num > 0: cls = "val-up"
        elif val_num < 0: cls = "val-down"
    val_str = f"{val_num:+.2f}$" if is_curr and isinstance(value, (int, float)) else str(value)
    return f'<div class="custom-card"><div class="card-title">{title}</div><div class="card-val {cls}">{val_str}</div><div class="card-sub">{sub}</div></div>'

def render_day_tile(day, pnl, count):
    if day == 0: return '<div class="day-card" style="border:none; background:transparent"></div>'
    cls = "val-up" if pnl > 0 else "val-down" if pnl < 0 else "val-neutral"
    pnl_s = f"{pnl:+.0f}" if count > 0 else "-"
    cnt_s = f"{int(count)}" if count > 0 else ""
    return f'<div class="day-card"><div class="day-num">{day}</div><div class="day-val {cls}">{pnl_s}</div><div style="font-size:0.7rem; color:#666; text-align:center;">{cnt_s}</div></div>'

def render_calendar_grid(df, year, month):
    cal = calendar.monthcalendar(year, month)
    stats = df.groupby('date_only')['pnl'].agg(['sum', 'count']).to_dict('index')
    html = '<div class="calendar-grid">'
    for d in ['PN','WT','ŚR','CZ','PT','SB','ND','SUMA']: html += f'<div class="grid-header">{d}</div>'
    for week in cal:
        w_sum = 0
        for day in week:
            curr = date(year, month, day) if day != 0 else None
            if curr and curr in stats:
                s = stats[curr]['sum']; c = stats[curr]['count']; w_sum += s
                html += render_day_tile(day, s, c)
            else: html += render_day_tile(day, 0, 0)
        w_cls = "val-up" if w_sum > 0 else "val-down" if w_sum < 0 else "val-neutral"
        html += f'<div class="week-summary"><div style="font-size:0.6rem; color:#888;">TYDZIEŃ</div><div class="{w_cls}" style="font-weight:bold; font-family:monospace;">{w_sum:+.0f}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_tiles_grid(df, mode, year=None):
    html = '<div class="tile-grid">'
    if mode == "Lata":
        stats = df.groupby('year_int').agg({'pnl': 'sum', 'id': 'count'}).sort_index(ascending=False)
        for y, r in stats.iterrows(): html += render_card(f"Rok {y}", r['pnl'], f"{r['id']} trd")
    elif mode == "Rok":
        df_y = df[df['year_int'] == year]
        stats = df_y.groupby('month_int').agg({'pnl': 'sum', 'id': 'count'}) if not df_y.empty else pd.DataFrame()
        for m in range(1, 13):
            name = POLISH_MONTHS[m]
            if not stats.empty and m in stats.index: html += render_card(name, stats.loc[m]['pnl'], f"{stats.loc[m]['id']} trd")
            else: html += render_card(name, 0, "-", True)
    elif mode == "Tygodnie":
        df_y = df[df['year_int'] == year]
        last_w = date(year, 12, 28).isocalendar().week
        stats = df_y.groupby(df_y['date_dt'].dt.isocalendar().week).agg({'pnl': 'sum', 'id': 'count'}) if not df_y.empty else pd.DataFrame()
        for w in range(1, last_w + 1):
            if not stats.empty and w in stats.index: html += render_card(f"Tydz {w}", stats.loc[w]['pnl'], f"{stats.loc[w]['id']} trd")
            else: html += render_card(f"Tydz {w}", 0, "-", True)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_html_table(df):
    html = '<div class="trade-table-container"><div class="trade-table-header"><div>Data</div><div>Symbol</div><div>Kier.</div><div>Cena Wej.</div><div>Cena Wyj.</div><div>Wart. Wej.</div><div>Wart. Wyj.</div><div>Czas</div><div>Wynik (PnL)</div><div>Zwrot %</div></div>'
    for index, row in df.iterrows():
        pnl = row['pnl']; size = row['position_size']
        entry_val = row['entry_price'] * size; exit_val = row['exit_price'] * size
        pnl_class = "pnl-green" if pnl > 0 else "pnl-red" if pnl < 0 else ""
        icon = "▲" if pnl > 0 else "▼" if pnl < 0 else ""
        roi = (pnl / entry_val * 100) if entry_val > 0 else 0
        roi_class = "pnl-green" if roi > 0 else "pnl-red" if roi < 0 else ""
        direction = row['direction']
        
        # FIX: Zastosowanie klasy .badge wewnątrz kontenera
        badge_class = "badge-long" if direction == "Long" else "badge-short"
        
        hours = row['hold_hours']
        if pd.isna(hours) or hours == 0: time_str = "-"
        elif hours < 1: time_str = f"{int(hours*60)}m"
        else: h = int(hours); m = int((hours - h) * 60); time_str = f"{h}h {m}m"
        date_str = row['date_dt'].strftime('%d.%m.%Y')
        
        # HTML z poprawionymi klasami
        html += f'<div class="trade-table-row"><div class="col-date">{date_str}</div><div class="col-symbol">{row["symbol"]}</div><div><span class="badge {badge_class}">{direction}</span></div><div class="col-num">{row["entry_price"]:.4f}</div><div class="col-num">{row["exit_price"]:.4f}</div><div class="col-val">${entry_val:,.0f}</div><div class="col-val">${exit_val:,.0f}</div><div><span class="badge-time">{time_str}</span></div><div class="col-pnl {pnl_class}"><span>{icon}</span>{pnl:+.2f}$</div><div class="{roi_class}" style="font-weight:700; font-family:monospace;">{roi:+.2f}%</div></div>'
    html += '</div>'
    return html

def render_position_visualizer(entry, sl, tp, direction):
    dist_top = abs(max(tp, sl) - entry)
    dist_bottom = abs(entry - min(tp, sl))
    total_dist = dist_top + dist_bottom
    if total_dist == 0: total_dist = 1
    pct_top = (dist_top / total_dist) * 100; pct_bottom = (dist_bottom / total_dist) * 100
    if pct_top < 15: pct_top = 15
    if pct_bottom < 15: pct_bottom = 15
    sum_pct = pct_top + pct_bottom; pct_top = (pct_top / sum_pct) * 100; pct_bottom = (pct_bottom / sum_pct) * 100
    
    if direction == "Long":
        class_top = "visual-profit"; class_bottom = "visual-loss"
        label_top = f"TP: {tp}"; label_bottom = f"SL: {sl}"
        color_top = "var(--neon-green)"; color_bottom = "var(--neon-red)"
    else:
        class_top = "visual-loss"; class_bottom = "visual-profit"
        label_top = f"SL: {sl}"; label_bottom = f"TP: {tp}"
        color_top = "var(--neon-red)"; color_bottom = "var(--neon-green)"

    html = f"""<div style="display:flex; justify-content:center; align-items:center; height:100%;"><div class="visual-bar-container"><div class="visual-segment {class_top}" style="height: {pct_top}%;"><div class="price-label" style="color: {color_top};">{label_top}</div></div><div class="entry-line" style="top: {pct_top}%;"><div class="price-label" style="color: white; top:-8px;">Entry: {entry}</div></div><div class="visual-segment {class_bottom}" style="height: {pct_bottom}%;"><div class="price-label" style="color: {color_bottom};">{label_bottom}</div></div></div></div>"""
    return html

# --- NOWA FUNKCJA IMPORTU (REGEX + SIEROTY) ---
def parse_exchange_csv_final(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        
        # 1. Robust Number Cleaner (Regex)
        def clean_num(x):
            if pd.isna(x): return 0.0
            s = str(x)
            s = s.replace(',', '.')
            s = re.sub(r'[^\d.-]', '', s)
            try: return float(s)
            except: return 0.0

        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if 'czas' in cl or 'time' in cl: col_map['date'] = col
            elif 'kontrakt' in cl or 'symbol' in cl: col_map['symbol'] = col
            elif 'kierunek' in cl or 'side' in cl: col_map['direction'] = col
            elif 'kwota' in cl or 'qty' in cl or 'size' in cl: col_map['size'] = col
            elif 'cena' in cl or 'price' in cl: col_map['price'] = col
            elif 'opłata' in cl or 'fee' in cl: col_map['fee'] = col
            elif 'pnl' in cl: col_map['pnl'] = col

        required = ['date', 'symbol', 'direction', 'size', 'price', 'pnl']
        if not all(k in col_map for k in required):
            st.error("Nie rozpoznano struktury pliku CSV. Sprawdź nagłówki.")
            return pd.DataFrame()

        df['size_c'] = df[col_map['size']].apply(clean_num)
        df['price_c'] = df[col_map['price']].apply(clean_num)
        df['fee_c'] = df[col_map['fee']].apply(clean_num)
        df['pnl_c'] = df[col_map['pnl']].apply(clean_num)
        df['dt'] = pd.to_datetime(df[col_map['date']])

        df_grouped = df.groupby(['dt', col_map['symbol'], col_map['direction']]).agg({
            'size_c': 'sum', 'fee_c': 'sum', 'pnl_c': 'sum', 'price_c': 'mean'
        }).reset_index().sort_values(by='dt', ascending=True)

        trades_to_import = []
        open_positions = {}

        for _, row in df_grouped.iterrows():
            sym = row[col_map['symbol']]
            dir_str = str(row[col_map['direction']])
            size = row['size_c']; price = row['price_c']; fee = row['fee_c']; pnl = row['pnl_c']
            d_str = row['dt'].strftime('%Y-%m-%d %H:%M:%S')

            is_open = 'Otw' in dir_str or 'Open' in dir_str
            is_close = 'Zamk' in dir_str or 'Close' in dir_str
            is_long = 'Dług' in dir_str or 'Long' in dir_str
            
            if is_open:
                if sym not in open_positions: open_positions[sym] = []
                open_positions[sym].append({'size': size, 'price': price, 'fee': fee, 'date': d_str})
            
            elif is_close:
                direction = 'Long' if is_long else 'Short'
                remaining_qty = size
                entry_cost = 0; entry_fee = 0; exec_qty = 0; entry_times = []

                if sym in open_positions:
                    while remaining_qty > 0.0000001 and open_positions[sym]:
                        op = open_positions[sym][0]; avail = op['size']
                        chunk = min(remaining_qty, avail)
                        chunk_fee = op['fee'] * (chunk / avail) if avail > 0 else 0
                        entry_fee += chunk_fee; entry_cost += chunk * op['price']
                        exec_qty += chunk; remaining_qty -= chunk; entry_times.append(op['date'])
                        open_positions[sym][0]['size'] -= chunk; open_positions[sym][0]['fee'] -= chunk_fee
                        if open_positions[sym][0]['size'] <= 0.0000001: open_positions[sym].pop(0)

                if remaining_qty > 0.0000001:
                    ratio = remaining_qty / size; orphan_pnl = pnl * ratio 
                    calc_entry_price = 0
                    if direction == 'Long': calc_entry_price = price - (orphan_pnl / remaining_qty)
                    else: calc_entry_price = (orphan_pnl / remaining_qty) + price
                    entry_cost += remaining_qty * calc_entry_price; exec_qty += remaining_qty; entry_times.append(d_str) 
                
                avg_entry_price = entry_cost / exec_qty if exec_qty > 0 else 0
                total_trade_fee = fee + entry_fee
                net_pnl = pnl - total_trade_fee
                final_entry_date = min(entry_times) if entry_times else d_str

                trades_to_import.append({
                    'date': d_str, 'entry_date': final_entry_date, 'symbol': sym, 'direction': direction,
                    'setup': 'Import CSV', 'entry_price': avg_entry_price, 'exit_price': price,
                    'stop_loss': 0.0, 'position_size': exec_qty, 'fees': total_trade_fee,
                    'notes': 'Auto-Import', 'pnl': net_pnl, 'r_multiple': 0.0
                })

        return pd.DataFrame(trades_to_import)
    except Exception as e:
        st.error(f"Błąd parsowania CSV: {e}")
        return pd.DataFrame()

# --- 5. APLIKACJA GŁÓWNA ---
def main():
    df = get_trades()
    
    with st.sidebar:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.markdown("### ⚡ TRADER PRO")
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        menu_options = ["📊 Dashboard", "📈 Statystyki", "🧮 Kalkulator", "📅 Kalendarz", "📂 Dane"]
        menu = st.radio("", menu_options, label_visibility="collapsed", key="nav_menu_final_v3")
        

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("DASHBOARD")
        if not df.empty:
            c1, c2 = st.columns([1, 4])
            preset = c1.selectbox("Zakres", ["Własny", "Dzisiaj", "Wczoraj", "Obecny Tydzień", "Obecny Miesiąc", "Obecny Rok", "Całość"], index=6)
            s_d, e_d = get_date_range(preset)
            df_f = df.copy()
            if preset == "Własny":
                with c2:
                    d_input = st.date_input("Wybierz zakres dat", [])
                    if len(d_input) == 2: df_f = df[(df['date_dt'].dt.date >= d_input[0]) & (df['date_dt'].dt.date <= d_input[1])]
            elif preset != "Całość" and s_d: df_f = df[(df['date_dt'].dt.date >= s_d) & (df['date_dt'].dt.date <= e_d)]
            
            wins = df_f[df_f['pnl'] > 0]; losses = df_f[df_f['pnl'] < 0]
            net = df_f['pnl'].sum(); fees = df_f['fees'].sum()
            pf = wins['pnl'].sum() / abs(losses['pnl'].sum()) if not losses.empty else 0
            cnt = len(df_f); wr = len(wins)/cnt*100 if cnt>0 else 0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(render_card("Net PnL", net, "Po opłatach"), unsafe_allow_html=True)
            c2.markdown(render_card("Profit Factor", f"{pf:.2f}", "Target > 1.5", False), unsafe_allow_html=True)
            c3.markdown(render_card("Win Rate", f"{wr:.1f}%", f"{len(wins)}W / {len(losses)}L", False), unsafe_allow_html=True)
            c4.markdown(render_card("Prowizje", fees, "Opłacone"), unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### KRZYWA KAPITAŁU")
            df_s = df_f.sort_values('date_dt'); df_s['cum'] = df_s['pnl'].cumsum()
            min_y = df_s['cum'].min(); max_y = df_s['cum'].max()
            area_stops = []; line_stops = []
            
            if min_y >= 0:
                area_stops = [alt.GradientStop(color='rgba(46, 160, 67, 0.1)', offset=0), alt.GradientStop(color='rgba(46, 160, 67, 0.5)', offset=1)]
                line_stops = [alt.GradientStop(color='#2ea043', offset=0), alt.GradientStop(color='#2ea043', offset=1)]
            elif max_y <= 0:
                area_stops = [alt.GradientStop(color='rgba(218, 54, 51, 0.5)', offset=0), alt.GradientStop(color='rgba(218, 54, 51, 0.1)', offset=1)]
                line_stops = [alt.GradientStop(color='#da3633', offset=0), alt.GradientStop(color='#da3633', offset=1)]
            else:
                zero_r = abs(min_y) / (max_y - min_y)
                area_stops = [alt.GradientStop(color='rgba(218, 54, 51, 0.5)', offset=0), alt.GradientStop(color='rgba(218, 54, 51, 0.1)', offset=zero_r), alt.GradientStop(color='rgba(46, 160, 67, 0.1)', offset=zero_r), alt.GradientStop(color='rgba(46, 160, 67, 0.5)', offset=1)]
                line_stops = [alt.GradientStop(color='#da3633', offset=0), alt.GradientStop(color='#da3633', offset=zero_r), alt.GradientStop(color='#2ea043', offset=zero_r), alt.GradientStop(color='#2ea043', offset=1)]

            base = alt.Chart(df_s).encode(x=alt.X('date_dt', title=''), y=alt.Y('cum', title='Equity ($)'), tooltip=['date','cum'])
            area = base.mark_area(color=alt.Gradient(gradient='linear', stops=area_stops, x1=1, x2=1, y1=1, y2=0))
            line = base.mark_line(color=alt.Gradient(gradient='linear', stops=line_stops, x1=1, x2=1, y1=1, y2=0))
            st.altair_chart((area + line).properties(height=350), use_container_width=True)

            st.markdown("#### OSTATNIE TRANSAKCJE")
            st.markdown(render_html_table(df_f.head(20)), unsafe_allow_html=True)
        else: st.info("Brak danych.")

    # --- STATYSTYKI ---
    elif menu == "📈 Statystyki":
        st.title("STATYSTYKI")
        if not df.empty:
            c1, c2 = st.columns([1, 4])
            preset = c1.selectbox("Zakres", ["Własny", "Dzisiaj", "Wczoraj", "Obecny Tydzień", "Obecny Miesiąc", "Obecny Rok", "Całość"], index=6, key="stats_range")
            s_d, e_d = get_date_range(preset); df_f = df.copy()
            if preset == "Własny":
                with c2:
                    d_input = st.date_input("Wybierz zakres dat", [], key="stats_date_input")
                    if len(d_input) == 2: df_f = df[(df['date_dt'].dt.date >= d_input[0]) & (df['date_dt'].dt.date <= d_input[1])]
            elif preset != "Całość" and s_d: df_f = df[(df['date_dt'].dt.date >= s_d) & (df['date_dt'].dt.date <= e_d)]
            
            wins = df_f[df_f['pnl']>0]; losses = df_f[df_f['pnl']<0]
            ws, ls = calculate_streaks(df_f)
            awh = wins['hold_hours'].mean() if not wins.empty else 0
            alh = losses['hold_hours'].mean() if not losses.empty else 0
            pf = wins['pnl'].sum() / abs(losses['pnl'].sum()) if not losses.empty else 0
            
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            r1c1.markdown(render_card("Net PnL", df_f['pnl'].sum()), unsafe_allow_html=True)
            r1c2.markdown(render_card("Profit Factor", f"{pf:.2f}", "", False), unsafe_allow_html=True)
            r1c3.markdown(render_card("Win Rate", f"{(len(wins)/len(df_f)*100):.1f}%" if len(df_f)>0 else "0%", "", False), unsafe_allow_html=True)
            r1c4.markdown(render_card("Prowizje", df_f['fees'].sum()), unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            r2c1, r2c2, r2c3, r2c4 = st.columns(4)
            r2c1.markdown(render_card("Max Zysk", df_f['pnl'].max() if not df_f.empty else 0), unsafe_allow_html=True)
            r2c2.markdown(render_card("Max Strata", df_f['pnl'].min() if not df_f.empty else 0), unsafe_allow_html=True)
            r2c3.markdown(render_card("Śr. Zysk", wins['pnl'].mean() if not wins.empty else 0), unsafe_allow_html=True)
            r2c4.markdown(render_card("Śr. Strata", losses['pnl'].mean() if not losses.empty else 0), unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            r3c1, r3c2, r3c3, r3c4 = st.columns(4)
            r3c1.markdown(render_card("Win Streak", ws, "Seria", False), unsafe_allow_html=True)
            r3c2.markdown(render_card("Loss Streak", ls, "Seria", False), unsafe_allow_html=True)
            r3c3.markdown(render_card("Śr. Czas Win", format_duration(awh), "", False), unsafe_allow_html=True)
            r3c4.markdown(render_card("Śr. Czas Loss", format_duration(alh), "", False), unsafe_allow_html=True)
            
            st.markdown("---")
            c_sel, c_ch = st.columns([1, 4])
            with c_sel: metric_type = st.radio("Wybierz Wykres", ["Krzywa Kapitału", "Drawdown", "PnL Dzienny", "PnL Miesięczny", "Rolling Win Rate"])
            with c_ch:
                df_s = df_f.sort_values('date_dt')
                if metric_type == "Krzywa Kapitału":
                    df_s['cum'] = df_s['pnl'].cumsum()
                    ch = alt.Chart(df_s).mark_area(color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color='#2ea043', offset=0), alt.GradientStop(color='rgba(46, 160, 67, 0)', offset=1)], x1=1, x2=1, y1=1, y2=0), line={'color':'#2ea043'}).encode(x='date_dt', y='cum').properties(height=350)
                    st.altair_chart(ch, use_container_width=True)
                elif metric_type == "Drawdown":
                    df_s['cum'] = df_s['pnl'].cumsum(); df_s['peak'] = df_s['cum'].cummax(); df_s['dd'] = df_s['cum'] - df_s['peak']
                    ch = alt.Chart(df_s).mark_area(color='#da3633', opacity=0.6).encode(x='date_dt', y='dd').properties(height=350)
                    st.altair_chart(ch, use_container_width=True)
                elif metric_type == "Rolling Win Rate":
                    df_s['is_win'] = df_s['pnl'] > 0; df_s['roll_wr'] = df_s['is_win'].rolling(20, min_periods=1).mean() * 100
                    ch = alt.Chart(df_s).mark_line(color='#1f6feb').encode(x='date_dt', y=alt.Y('roll_wr', title='Win Rate % (20 tradów)')).properties(height=350)
                    st.altair_chart(ch, use_container_width=True)
                elif metric_type == "PnL Dzienny":
                    d = df_f.groupby('date_only')['pnl'].sum().reset_index(); d['col'] = d['pnl'].apply(lambda x: '#2ea043' if x>0 else '#da3633')
                    ch = alt.Chart(d).mark_bar().encode(x='date_only', y='pnl', color=alt.Color('col', scale=None)).properties(height=350)
                    st.altair_chart(ch, use_container_width=True)
                elif metric_type == "PnL Miesięczny":
                    df_f['ym'] = df_f['date_dt'].dt.strftime('%Y-%m'); m = df_f.groupby('ym')['pnl'].sum().reset_index(); m['col'] = m['pnl'].apply(lambda x: '#2ea043' if x>0 else '#da3633')
                    ch = alt.Chart(m).mark_bar().encode(x='ym', y='pnl', color=alt.Color('col', scale=None)).properties(height=350)
                    st.altair_chart(ch, use_container_width=True)

    # --- KALKULATOR ---
    elif menu == "🧮 Kalkulator":
        st.title("KALKULATOR POZYCJI")
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("##### USTAWIENIA KONTA")
            balance = st.number_input("Kapitał ($)", value=10000.0, step=100.0, key="calc_balance")
            
            cr1, cr2 = st.columns(2)
            risk_type = cr1.selectbox("Typ Ryzyka", ["Procent (%)", "Kwota ($)"], key="calc_risk_type")
            risk_val = cr2.number_input("Wartość Ryzyka", value=1.0, step=0.1, key="calc_risk_val")
            
            st.markdown("##### PROWIZJE")
            cf1, cf2, cf3 = st.columns([1, 1, 1])
            entry_order_type = cf1.selectbox("Typ Zlecenia", ["Taker", "Maker"], key="calc_order_type")
            
            default_open = 0.01 if entry_order_type == "Taker" else 0.0
            
            fee_open = cf2.number_input("Otwarcie (%)", value=default_open, step=0.001, format="%.3f", key=f"f_op_{entry_order_type}")
            fee_close = cf3.number_input("Zamknięcie (%)", value=0.010, step=0.001, format="%.3f", key="f_cl")
            
            incl_fees = st.checkbox("Wlicz prowizję w ryzyko?", value=True, key="calc_incl_fees")
            
            st.markdown("##### PARAMETRY POZYCJI")
            direction = st.selectbox("Kierunek", ["Long", "Short"], key="calc_direction")
            
            cp1, cp2, cp3 = st.columns(3)
            entry = cp1.number_input("Cena Wejścia", value=50000.0, step=10.0, key="calc_entry")
            sl = cp2.number_input("Stop Loss", value=49000.0, step=10.0, key="calc_sl")
            tp = cp3.number_input("Take Profit", value=52000.0, step=10.0, key="calc_tp")
            
        with c2:
            st.markdown("##### WYNIKI")
            # LOGIKA OBLICZEŃ
            if entry > 0 and sl > 0:
                price_diff = entry - sl if direction == "Long" else sl - entry
                reward_diff = tp - entry if direction == "Long" else entry - tp
                
                if price_diff <= 0: price_diff = 0.000001
                
                risk_amt = balance * (risk_val/100) if risk_type == "Procent (%)" else risk_val
                
                comm_open_dec = fee_open / 100
                comm_close_dec = fee_close / 100
                
                size = 0
                if incl_fees:
                    fee_per_unit = (entry * comm_open_dec) + (sl * comm_close_dec)
                    denom = price_diff + fee_per_unit
                    if denom > 0: size = risk_amt / denom
                else:
                    size = risk_amt / price_diff
                
                position_val = size * entry
                est_fee_open = position_val * comm_open_dec
                est_fee_close_sl = (size * sl) * comm_close_dec
                est_fee_close_tp = (size * tp) * comm_close_dec
                
                total_loss = (size * price_diff) + est_fee_open + est_fee_close_sl
                total_profit = (size * reward_diff) - (est_fee_open + est_fee_close_tp)
                
                rr = total_profit / total_loss if total_loss > 0 else 0
                
                st.markdown(render_card("Wielkość Pozycji", size, f"Wartość: ${position_val:,.2f}", False), unsafe_allow_html=True)
                
                r1, r2 = st.columns(2)
                r1.markdown(render_card("Ryzyko (Strata)", -total_loss), unsafe_allow_html=True)
                r2.markdown(render_card("Potencjalny Zysk", total_profit), unsafe_allow_html=True)
                
                r3, r4 = st.columns(2)
                r3.markdown(render_card("Risk : Reward", f"1 : {rr:.2f}", "", False), unsafe_allow_html=True)
                r4.markdown(render_card("Prowizje (Szac.)", -(est_fee_open + est_fee_close_sl)), unsafe_allow_html=True)
                
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                st.markdown(render_position_visualizer(entry, sl, tp, direction), unsafe_allow_html=True)

    # --- KALENDARZ ---
    elif menu == "📅 Kalendarz":
        st.title("KALENDARZ")
        if not df.empty:
            c1, c2 = st.columns([2,1])
            mode = c1.radio("Tryb", ["Miesiąc (Dni)", "Tygodnie", "Rok", "Lata"], horizontal=True)
            years = sorted(df['year_int'].unique(), reverse=True)
            sel_yr = c2.selectbox("Rok", years if years else [2025])
            st.markdown("---")
            if mode == "Miesiąc (Dni)":
                now = datetime.now()
                c_m, _ = st.columns([1,3])
                # FIX: Użyj datetime.now().month jako default, chyba że brak danych
                sel_m = c_m.selectbox("Miesiąc", range(1,13), index=now.month-1, format_func=lambda x: POLISH_MONTHS[x])
                render_calendar_grid(df, sel_yr, sel_m)
            else:
                render_tiles_grid(df, mode, sel_yr)

    # --- DANE ---
    elif menu == "📂 Dane":
        st.title("DANE")
        t1, t2, t3 = st.tabs(["✍️ Dodaj Ręcznie", "📂 Import CSV", "🗑️ Zarządzanie"])
        with t1:
            current_df = get_trades() # Pobierz dla anty-duplikatu
            with st.form("manual"):
                c1, c2 = st.columns(2)
                dt = c1.date_input("Data Zamknięcia")
                ent_dt = c2.date_input("Data Otwarcia", value=dt)
                c_sym, c_dir, c_set = st.columns(3)
                sym = c_sym.text_input("Symbol").upper(); dire = c_dir.selectbox("Kierunek", ["Long", "Short"]); setup = c_set.text_input("Setup", "Manual")
                st.markdown("---")
                c3, c4, c5 = st.columns(3)
                ep = c3.number_input("Wejście", step=0.0001, format="%.4f"); xp = c4.number_input("Wyjście", step=0.0001, format="%.4f"); sl = c5.number_input("SL", step=0.0001, format="%.4f")
                c6, c7 = st.columns(2)
                sz = c6.number_input("Ilość", step=0.001); fee = c7.number_input("Fee", step=0.01)
                note = st.text_area("Notatki")
                if st.form_submit_button("Zapisz"):
                    pnl = ((xp - ep) * sz) - fee if dire == "Long" else ((ep - xp) * sz) - fee
                    risk = abs(ep - sl); r = abs(xp - ep) / risk if risk > 0 else 0
                    
                    data_to_add = {'date': dt.strftime('%Y-%m-%d %H:%M:%S'), 'entry_date': ent_dt.strftime('%Y-%m-%d %H:%M:%S'), 'symbol': sym, 'direction': dire, 'setup': setup, 'entry_price': ep, 'exit_price': xp, 'stop_loss': sl, 'position_size': sz, 'fees': fee, 'notes': note, 'pnl': pnl, 'r_multiple': r}
                    
                    if add_trade_to_gsheet(data_to_add, current_df):
                        st.success("Transakcja dodana pomyślnie do Google Sheets!"); st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else: st.error("Błąd: Duplikat transakcji lub błąd zapisu.")
        with t2:
            current_df = get_trades()
            up = st.file_uploader("CSV", type=['csv'])
            if up:
                imp = parse_exchange_csv_final(up)
                if not imp.empty:
                    if st.button(f"Import {len(imp)}"):
                        n=0
                        for _,r in imp.iterrows(): 
                            data_to_add = r.to_dict()
                            if add_trade_to_gsheet(data_to_add, current_df): n+=1
                        
                        if n>0: 
                            st.toast(f"Dodano {n}", icon='✅'); st.success(f"Dodano {n} unikalnych pozycji do Sheets."); 
                            time.sleep(2); st.rerun()
                        else: st.warning("Brak nowych transakcji (wszystkie to duplikaty).")
        with t3:
            st.warning("Funkcje usuwania pozycji i czyszczenia bazy są wyłączone w trybie Google Sheets. Aby usunąć pozycję, musisz zrobić to ręcznie w Arkuszu Google.")

if __name__ == "__main__":
    main()
