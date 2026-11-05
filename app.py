# -*- coding: utf-8 -*-
"""
app.py
------
QUANTUM ALPHA TERMINAL // WORLD OF WARCRAFT & CYBERPUNK EPIC EDITION
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import feedparser
import urllib.parse
from screener_engine import QuantScreenerEngine

st.set_page_config(
    page_title="AZEROTH ALPHA TERMINAL // EPIC WARCRAFT EDITION",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    /* 核心背景：魔獸黑暗之門與深淵黑曜石風格 */
    .stApp {
        background-color: #050508;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(88, 28, 135, 0.25) 0%, transparent 70%),
            radial-gradient(circle at 10% 90%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
            linear-gradient(rgba(217, 119, 6, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(217, 119, 6, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        color: #E2E8F0;
        font-family: 'Cinzel', 'Segoe UI', 'Courier New', monospace, sans-serif;
    }

    /* 史詩標題：古金石與薩滿電弧藍漸層 */
    .cyber-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #F59E0B 0%, #38BDF8 35%, #A855F7 70%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.4), 0 0 60px rgba(168, 85, 247, 0.2);
        margin-bottom: 0.1rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* 副標題裝飾線 */
    .cyber-sub {
        font-size: 1.05rem;
        color: #38BDF8;
        font-weight: 700;
        margin-bottom: 2rem;
        border-left: 4px solid #F59E0B;
        padding-left: 0.85rem;
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, transparent 100%);
        padding-top: 0.4rem;
        padding-bottom: 0.4rem;
        letter-spacing: 0.12em;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
    }

    /* 側邊欄：暗黑符文法陣風格 */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 10, 18, 0.95);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(245, 158, 11, 0.35);
        box-shadow: 8px 0 35px rgba(0, 0, 0, 0.9);
    }

    /* 數據表格：黑曜石框體 */
    div.stDataFrame {
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 0.6rem;
        background-color: rgba(12, 14, 24, 0.9);
        backdrop-filter: blur(12px);
        padding: 0.6rem;
        box-shadow: 0 12px 35px -5px rgba(0, 0, 0, 0.95), 0 0 25px rgba(56, 189, 248, 0.15);
    }

    /* 分頁標籤：史詩能量條風格 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(12, 14, 24, 0.95);
        padding: 10px;
        border-radius: 0.6rem;
        border: 1px solid rgba(245, 158, 11, 0.3);
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px;
        background-color: transparent;
        border-radius: 4px;
        color: #94A3B8;
        font-weight: 700;
        border: none;
        letter-spacing: 0.06em;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #38BDF8;
        background-color: rgba(56, 189, 248, 0.12);
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.8);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #B45309 0%, #1E3A8A 50%, #6B21A8 100%);
        color: #F8FAFC !important;
        box-shadow: 0 0 30px rgba(245, 158, 11, 0.5), inset 0 0 10px rgba(56, 189, 248, 0.6);
        border: 1px solid rgba(245, 158, 11, 0.6);
    }

    /* 按鈕：史詩烈焰按鈕 */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #D97706 0%, #2563EB 50%, #7E22CE 100%);
        border: 1px solid rgba(245, 158, 11, 0.6);
        color: white;
        font-weight: 900;
        letter-spacing: 0.12em;
        border-radius: 0.4rem;
        box-shadow: 0 0 35px rgba(217, 119, 6, 0.6);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #F59E0B 0%, #3B82F6 50%, #9333EA 100%);
        box-shadow: 0 0 50px rgba(56, 189, 248, 0.8), 0 0 25px rgba(245, 158, 11, 0.9);
        transform: translateY(-2px) scale(1.02);
    }

    /* 展開面板與數據指標 */
    div.streamlit-expanderHeader {
        background-color: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 0.4rem;
        color: #F8FAFC;
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        background-color: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 15px;
        border-radius: 0.5rem;
        box-shadow: 0 0 25px rgba(0, 0, 0, 0.85);
    }
    [data-testid="stMetricValue"] {
        color: #F59E0B !important;
        text-shadow: 0 0 12px rgba(245, 158, 11, 0.6);
    }

    /* 🛡️ 分數變化彩色戰利品標籤 (Buff / Debuff Badge) */
    .buff-badge {
        color: #4ADE80;
        background-color: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 800;
        text-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
    }
    .debuff-badge {
        color: #F87171;
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 800;
        text-shadow: 0 0 8px rgba(248, 113, 113, 0.6);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="cyber-header">🛡️ AZEROTH ALPHA TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-sub">[EPIC_WARCRAFT_ACTIVE] // REAL-TIME MESH QUANTITATIVE SCREENING & MAGITECH ALLOCATION // v2026 MYTHIC EDITION</div>', unsafe_allow_html=True)

engine = QuantScreenerEngine()
default_watchlist = engine.watchlist

market_state = engine.get_current_market_state()
default_impulse = market_state["credit_impulse"]
default_m2 = market_state["m2_gap"]

st.sidebar.header("⚔️ 遠征軍戰情控制台")
st.sidebar.info(f"🌐 艾澤拉斯宏觀同步 ({market_state['sync_date']}): 10年美債 {market_state['benchmark_tnx']}%")

impulse_options = [
    "擴張期 (Expansion - 流動性充沛)", 
    "中性期 (Neutral)", 
    "收縮期 (Contraction - 防禦為主)"
]
default_impulse_idx = impulse_options.index(default_impulse) if default_impulse in impulse_options else 0

credit_impulse = st.sidebar.selectbox(
    "1. 遠征信貸脈衝 (Credit Impulse)", 
    impulse_options, 
    index=default_impulse_idx
)

m2_gap = st.sidebar.slider(
    "2. 超額 M2 剪刀差 (ΔM2 - ΔGDP %)", 
    -2.0, 6.0, float(default_m2), 0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 📁 戰利品清單與來源")

watchlist_source = st.sidebar.radio(
    "選擇股票池來源", 
    ["預設 Excel 檔案", "上傳自定義檔案 (Excel/CSV)", "手動輸入股票代碼"],
    label_visibility="collapsed"
)

active_watchlist = default_watchlist

if watchlist_source == "上傳自定義檔案 (Excel/CSV)":
    uploaded_file = st.sidebar.file_uploader("上傳 Excel 或 CSV 檔案", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            target_col = None
            for col in df_upload.columns:
                if any(k in str(col).lower() for k in ["name", "symbol", "ticker", "名稱", "代碼"]):
                    target_col = col
                    break
            if target_col is None:
                target_col = df_upload.columns[0]
            
            active_watchlist = df_upload[target_col].dropna().astype(str).str.strip().tolist()
            st.sidebar.success(f"✅ 成功載入上傳檔案，共 {len(active_watchlist)} 檔標的。")
        except Exception as e:
            st.sidebar.error(f"❌ 讀取檔案失敗: {e}")

elif watchlist_source == "手動輸入股票代碼":
    manual_input = st.sidebar.text_area(
        "輸入股票代碼 (支援逗號或換行分隔)", 
        value="NVDA, AAPL, TSLA, MSFT, BAS.DE, EON.DE",
        height=100
    )
    if manual_input:
        raw_items = manual_input.replace(";", ",").replace("\n", ",").split(",")
        active_watchlist = [item.strip() for item in raw_items if item.strip()]
        st.sidebar.success(f"✅ 已解析手動輸入的 {len(active_watchlist)} 檔標的。")

st.sidebar.markdown("---")
selection_mode = st.sidebar.radio(
    "選取過濾模式", 
    ["評估全部標的", "自選特定標的池子集"], 
    index=0
)

if selection_mode == "評估全部標的":
    selected_stocks = active_watchlist
    st.sidebar.info(f"📊 將全面評估當前來源的 {len(active_watchlist)} 檔股票。")
else:
    selected_stocks = st.sidebar.multiselect("從當前清單中勾選", active_watchlist, default=active_watchlist[:15] if len(active_watchlist)>=15 else active_watchlist)

st.sidebar.markdown("---")
kelly_mode = st.sidebar.selectbox(
    "3. 裝備頭寸與凱利模型", 
    ["四分之一凱利 (0.25 f* - 史詩推薦)", "半凱利 (0.5 f*)", "ATR 波動率目標化 (ATR Sizing)"], 
    index=0
)

total_capital = st.sidebar.number_input(
    "總冒險資金 (€ / $)", 
    value=100000, 
    step=10000
)

st.sidebar.markdown("---")
run_btn = st.sidebar.button("⚔️ 啟動史詩量化遠征與投組鍛造", type="primary", use_container_width=True)

@st.cache_data(ttl=1800)
def fetch_stock_rss_news(symbol_or_name):
    try:
        clean_query = str(symbol_or_name).split(".")[0].strip()
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_query + ' stock')}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        news_items = []
        for entry in feed.entries[:3]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '#')
            published = entry.get('published', 'Recent')
            news_items.append({"title": title, "link": link, "published": published})
        return news_items
    except Exception:
        return []

if run_btn:
    if not selected_stocks:
        st.warning("請至少選取或輸入一檔股票。")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("⚔️ [01/03] 正在與奧格瑪與暴風城伺服器建立法力連結、同步宏觀流動性...")
        progress_bar.progress(25)
        time.sleep(0.2)
        
        status_text.text("🚀 [02/03] 啟動多維度量化引擎、解析 RSS 戰報與威科夫神話結構...")
        progress_bar.progress(60)
        
        df_res, df_unqualified = engine.run_screening_with_unqualified(
            selected_stocks, 
            capital=total_capital, 
            credit_impulse_status=credit_impulse, 
            m2_gap=m2_gap, 
            method=kelly_mode
        )
        
        status_text.text("💎 [03/03] 計算神話 Sharpe、IC 分數與 100% 歸一化動態頭寸配置...")
        progress_bar.progress(90)
        time.sleep(0.2)
        
        if df_res.empty and df_unqualified.empty:
            progress_bar.empty()
            status_text.empty()
            st.error("篩選結果為空，請檢查網絡連線或標的代碼是否正確。")
        else:
            st.session_state['df_res'] = df_res
            st.session_state['df_unqualified'] = df_unqualified
            st.session_state['credit_impulse'] = credit_impulse
            st.session_state['m2_gap'] = m2_gap
            
            progress_bar.progress(100)
            status_text.text("✨ 史詩量化遠征與 Portfolio Top 投組鍛造完畢！")
            time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
            st.rerun()

if 'df_res' in st.session_state and ('df_unqualified' in st.session_state):
    df_res = st.session_state['df_res']
    df_unqualified = st.session_state['df_unqualified']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("遠征信貸脈衝 (實時)", st.session_state['credit_impulse'].split()[0], f"美債 {market_state['benchmark_tnx']}%")
    col2.metric("超額 M2 剪刀差", f"+{st.session_state['m2_gap']}%", "神話法力驅動")
    col3.metric("評估合格標的", f"{len(df_res)} 檔", "多因子量化試煉通過")
    col4.metric("未通過 / 遭剔除", f"{len(df_unqualified)} 檔", "流動性不足遭到擊殺")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 合格全景量化清單",
        "⚠️ 未通過檢驗 / 遭剔除清單",
        "🎯 Portfolio Top 15 核心投組", 
        "⚡ TOP 10 短線與中長線雙軌戰情室",
        "💰 投資建議與倉位配置總覽", 
        "🏆 依投資建議分類之 TOP 5 深度戰情解讀"
    ])
    
    with tab1:
        st.markdown("### 📊 通過多維度量化檢驗之合格股票池")
        excel_view_df = df_res.drop(columns=['raw_price', '貨幣', '建議倉位比例', '建議配置金額 (€)', '不合格原因'], errors='ignore')
        st.dataframe(excel_view_df, use_container_width=True, height=600)
        
    with tab2:
        st.markdown("### ⚠️ 未通過檢驗 / 遭剔除之標的清單與原因")
        if df_unqualified.empty:
            st.info("🎉 太棒了！目前選取的股票池中沒有被剔除的不合格標的。")
        else:
            unqualified_display = df_unqualified.drop(columns=['raw_price', '貨幣', '建議倉位比例', '建議配置金額 (€)'], errors='ignore')
            st.dataframe(unqualified_display, use_container_width=True, height=550)
        
    with tab3:
        st.markdown("### 🎯 Portfolio Top 15 核心投組推薦")
        top15_df = df_res.head(15).reset_index(drop=True)
        top15_display = top15_df.drop(columns=['raw_price', '貨幣', '不合格原因'], errors='ignore')
        
        col_t1, col_t2 = st.columns([3, 1])
        with col_t2:
            total_top15_amt = top15_df['建議配置金額 (€)'].sum() if '建議配置金額 (€)' in top15_df.columns else 0.0
            st.metric("Top 15 總配置金額", f"€ {total_top15_amt:,.2f}", f"佔總資金 {round(total_top15_amt/total_capital*100, 1)}%")
            
        st.dataframe(top15_display, use_container_width=True, height=550)
        
        if not top15_df.empty and '建議配置金額 (€)' in top15_df.columns:
            fig_top15 = px.bar(
                top15_df, 
                x='股票名稱', 
                y='建議配置金額 (€)', 
                color='綜合評分',
                title='Portfolio Top 15 核心標的之最佳資本配置與綜合評分分佈',
                template='plotly_dark'
            )
            fig_top15.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#F8FAFC',
                title_font_color='#F59E0B'
            )
            st.plotly_chart(fig_top15, use_container_width=True)

    with tab4:
        st.markdown("### ⚡ TOP 10 短線動能操作 vs TOP 10 中長線價值佈局雙軌戰情室")
        st.markdown("結合**量化價格要素**、**即時 RSS 財經戰報**與 **Gemini AI 智慧總結**，為您完整展開短線與中長線的精準操盤指引。")
        
        df_short_top10, df_long_top10 = engine.get_dual_track_top10(df_res, capital=total_capital)
        
        st.markdown("---")
        st.markdown("#### 🚀 TOP 10 短線動能操作精選標的")
        if df_short_top10.empty:
            st.info("目前合格股票池數量不足 10 檔。")
        else:
            st.dataframe(df_short_top10, use_container_width=True, height=450)
            
        st.markdown("---")
        st.markdown("#### 🏛️ TOP 10 中長線價值佈局精選標的")
        if df_long_top10.empty:
            st.info("目前合格股票池數量不足 10 檔。")
        else:
            st.dataframe(df_long_top10, use_container_width=True, height=450)
        
    with tab5:
        st.markdown("### 💰 投資建議與動態資金配置總覽")
        rec_summary = df_res.groupby('投資建議').agg(
            標的數量=('股票名稱', 'count'),
            平均綜合評分=('綜合評分', 'mean'),
            總配置金額=('建議配置金額 (€)', 'sum')
        ).reset_index()
        rec_summary['平均綜合評分'] = rec_summary['平均綜合評分'].round(1)
        
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            st.dataframe(rec_summary, use_container_width=True)
        with col_s2:
            fig_pie = px.pie(
                rec_summary, 
                names='投資建議', 
                values='總配置金額', 
                title='各投資建議類別之資本配置佔比',
                template='plotly_dark'
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#F8FAFC',
                title_font_color='#F59E0B'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab6:
        st.markdown("### 🏆 依華爾街投資建議分類之 TOP 5 深度技術、基本面與關鍵操盤解讀")
        
        @st.cache_data(ttl=3600)
        def cached_ai_analysis(stock_name, symbol, tech_str, fundamental_str):
            news_list = fetch_stock_rss_news(stock_name if stock_name else symbol)
            return engine.analyze_stock_with_ai_and_rss(
                stock_name=stock_name,
                symbol=symbol,
                rss_news_list=news_list,
                tech_str=tech_str,
                fundamental_str=fundamental_str
            ), news_list

        rec_types = df_res['投資建議'].unique()
        for rec in rec_types:
            sub_df = df_res[df_res['投資建議'] == rec].head(5)
            if not sub_df.empty:
                st.markdown(f"#### 🔥 【{rec}】TOP 5 精選標的 (共 {len(sub_df)} 檔)")
                for idx, row in sub_df.iterrows():
                    # 🛡️ 根據分數變化（Δ）動態渲染魔獸風格的 Buff（綠）與 Debuff（紅）徽章
                    diff_val_str = str(row['分數變化 (Δ)'])
                    is_positive = not diff_val_str.startswith("-")
                    badge_class = "buff-badge" if is_positive else "debuff-badge"
                    delta_html = f'<span class="{badge_class}">Δ {diff_val_str}</span>'

                    with st.expander(f"📌 {row['股票名稱']} ({row['股票代碼']}) — 現價: {row['最新現價']} | 綜合評分: {row['綜合評分']}分 ({delta_html}) | 建議: {row['投資建議']}", expanded=False):
                        ca, cb, cc, cd = st.columns(4)
                        ca.metric("評估結果", row['評估結果'])
                        cb.metric("夏普比率 (Sharpe)", row['Sharpe Ratio'])
                        cc.metric("技術面數據", row['技術面數據'])
                        cd.metric("消息面分數", row['消息面分數'])
                        
                        st.markdown(f"""
                        * **量化預測 IC**: `{row['量化預測 IC']}` | **上一版純量化分**: `{row['上一版純量化分']}`
                        * **建議倉位配置**: `{row['建議倉位比例']}` (約 `{row['建議配置金額 (€)']:,} €`)
                        * **📊 技術面分析 (威科夫結構與 ATR)**: `{row['技術面分析 (威科夫/ATR)']}`
                        """)
                        
                        st.markdown("---")
                        st.markdown("##### ⚡ 華爾街 AI 戰情情報 (新聞總結、預測與深度操盤指引)")
                        
                        with st.spinner(f"正在同步 {row['股票名稱']} 實時情報與操盤邏輯中..."):
                            ai_insight, rss_news = cached_ai_analysis(
                                stock_name=row['股票名稱'],
                                symbol=row['股票代碼'],
                                tech_str=row['技術面分析 (威科夫/ATR)'],
                                fundamental_str=row['消息面與基本面解讀']
                            )
                        
                        if rss_news:
                            with st.expander("查看參考的即時 RSS 財經頭條"):
                                for news in rss_news:
                                    st.markdown(f"- [{news['title']}]({news['link']}) `({news['published'][:16]})`")
                        
                        st.markdown(ai_insight)
                        
        st.markdown("---")
        st.markdown("### 🤖 Gemini AI 全局戰情室總結報告")
        if st.button("✨ 啟動 Gemini AI 巨集戰情室診斷", type="primary"):
            with st.spinner("正在生成全局總結報告..."):
                ai_report = engine.analyze_with_gemini(
                    df_res, 
                    st.session_state['credit_impulse'],
                    st.session_state['m2_gap']
                )
                st.markdown(ai_report)
else:
    st.info("👈 請在左側側邊欄點擊「⚔️ 啟動史詩量化遠征與投組鍛造」按鈕，展開專業的魔獸風格量化決策終端。")
