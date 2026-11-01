# -*- coding: utf-8 -*-
"""
app.py
------
QUANTUM ALPHA TERMINAL — 現代多維度量化股票篩選與決策系統 (深度新聞要點與操盤點版)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import feedparser
import urllib.parse
from screener_engine import QuantScreenerEngine

st.set_page_config(
    page_title="QUANTUM ALPHA TERMINAL // CYBERNETIC v2026",
    page_icon="⚡",
    layout="wide"
)

# ⚡ 注入極致賽博龐克、霓虹發光與戰情室風格 CSS
st.markdown("""
<style>
    .stApp {
        background-color: #030712;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(6, 182, 212, 0.15) 0%, transparent 60%),
            linear-gradient(rgba(6, 182, 212, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.04) 1px, transparent 1px);
        background-size: 100% 100%, 30px 30px, 30px 30px;
        color: #F3F4F6;
        font-family: 'Share Tech Mono', 'Courier New', monospace, sans-serif;
    }
    .cyber-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #22D3EE 0%, #818CF8 40%, #E879F9 80%, #34D399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 35px rgba(34, 211, 238, 0.6), 0 0 70px rgba(232, 121, 249, 0.3);
        margin-bottom: 0.1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .cyber-sub {
        font-size: 1rem;
        color: #06B6D4;
        font-weight: 600;
        margin-bottom: 2rem;
        border-left: 4px solid #22D3EE;
        padding-left: 0.75rem;
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, transparent 100%);
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
        letter-spacing: 0.1em;
        text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
    }
    [data-testid="stSidebar"] {
        background-color: rgba(3, 7, 18, 0.92);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(34, 211, 238, 0.3);
        box-shadow: 5px 0 30px rgba(0, 0, 0, 0.8);
    }
    div.stDataFrame {
        border: 1px solid rgba(34, 211, 238, 0.35);
        border-radius: 0.5rem;
        background-color: rgba(10, 15, 30, 0.85);
        backdrop-filter: blur(12px);
        padding: 0.5rem;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.9), 0 0 25px rgba(34, 211, 238, 0.12);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(10, 15, 30, 0.95);
        padding: 8px;
        border-radius: 0.5rem;
        border: 1px solid rgba(34, 211, 238, 0.3);
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: transparent;
        border-radius: 4px;
        color: #9CA3AF;
        font-weight: 700;
        border: none;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #22D3EE;
        background-color: rgba(34, 211, 238, 0.1);
        text-shadow: 0 0 10px rgba(34, 211, 238, 0.7);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0891B2 0%, #4F46E5 50%, #9333EA 100%);
        color: #FFFFFF !important;
        box-shadow: 0 0 25px rgba(34, 211, 238, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #06B6D4 0%, #6366F1 50%, #D946EF 100%);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        font-weight: 800;
        letter-spacing: 0.1em;
        border-radius: 0.4rem;
        box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0891B2 0%, #4F46E5 50%, #C026D3 100%);
        box-shadow: 0 0 45px rgba(217, 70, 239, 0.8), 0 0 20px rgba(6, 182, 212, 0.8);
        transform: translateY(-2px) scale(1.02);
    }
    div.streamlit-expanderHeader {
        background-color: rgba(10, 15, 30, 0.9);
        border: 1px solid rgba(34, 211, 238, 0.3);
        border-radius: 0.4rem;
        color: #F3F4F6;
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        background-color: rgba(10, 15, 30, 0.85);
        border: 1px solid rgba(34, 211, 238, 0.25);
        padding: 15px;
        border-radius: 0.5rem;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.8);
    }
    [data-testid="stMetricValue"] {
        color: #22D3EE !important;
        text-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="cyber-header">⚡ QUANTUM ALPHA TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-sub">[SYSTEM_ACTIVE] // GLOBAL QUANTITATIVE SCREENING & DYNAMIC ASSET ALLOCATION // 2026 CYBERNETIC WARFARE EDITION</div>', unsafe_allow_html=True)

engine = QuantScreenerEngine()
watchlist = engine.watchlist

market_state = engine.get_current_market_state()
default_impulse = market_state["credit_impulse"]
default_m2 = market_state["m2_gap"]

st.sidebar.header("🎛️ 戰情室控制台")
st.sidebar.info(f"🌐 實時宏觀同步 ({market_state['sync_date']}): 10年美債 {market_state['benchmark_tnx']}%")

impulse_options = [
    "擴張期 (Expansion - 流動性充沛)", 
    "中性期 (Neutral)", 
    "收縮期 (Contraction - 防禦為主)"
]
default_impulse_idx = impulse_options.index(default_impulse) if default_impulse in impulse_options else 0

credit_impulse = st.sidebar.selectbox(
    "1. 信貸脈衝狀態 (Credit Impulse)", 
    impulse_options, 
    index=default_impulse_idx
)

m2_gap = st.sidebar.slider(
    "2. 超額 M2 剪刀差 (ΔM2 - ΔGDP %)", 
    -2.0, 6.0, float(default_m2), 0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 股票池選取模式")
selection_mode = st.sidebar.radio(
    "選擇模式", 
    ["評估 Excel 中的全部股票", "自選特定標的池"], 
    index=0, 
    label_visibility="collapsed"
)

if selection_mode == "評估 Excel 中的全部股票":
    selected_stocks = watchlist
    st.sidebar.success(f"✅ 已自動載入 Excel 中的全部 {len(watchlist)} 檔股票進行全景評估。")
else:
    selected_stocks = st.sidebar.multiselect("選取目標標的池", watchlist, default=watchlist[:15] if len(watchlist)>=15 else watchlist)

st.sidebar.markdown("---")
kelly_mode = st.sidebar.selectbox(
    "3. 資金控管與頭寸模型", 
    ["四分之一凱利 (0.25 f* - 機構推薦)", "半凱利 (0.5 f*)", "ATR 波動率目標化 (ATR Sizing)"], 
    index=0
)

total_capital = st.sidebar.number_input(
    "總投資資本 (€ / $)", 
    value=100000, 
    step=10000
)

st.sidebar.markdown("---")
run_btn = st.sidebar.button("⚡ 啟動量子量化篩選與投組構建", type="primary", use_container_width=True)

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
        st.warning("請至少選取或載入一檔股票。")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("⚡ [01/03] 建立量子安全連線、同步全球宏觀與實時流動性狀態...")
        progress_bar.progress(25)
        time.sleep(0.2)
        
        status_text.text("🚀 [02/03] 執行多維度量化引擎、威科夫微觀結構與華爾街評分運算...")
        progress_bar.progress(60)
        
        df_res, df_unqualified = engine.run_screening_with_unqualified(
            selected_stocks, 
            capital=total_capital, 
            credit_impulse_status=credit_impulse, 
            m2_gap=m2_gap, 
            method=kelly_mode
        )
        
        status_text.text("💎 [03/03] 計算 Sharpe、IC 分數與 100% 歸一化動態頭寸配置...")
        progress_bar.progress(90)
        time.sleep(0.2)
        
        if df_res.empty and df_unqualified.empty:
            progress_bar.empty()
            status_text.empty()
            st.error("篩選結果為空，請檢查網絡連線或標的流動性狀態。")
        else:
            st.session_state['df_res'] = df_res
            st.session_state['df_unqualified'] = df_unqualified
            st.session_state['credit_impulse'] = credit_impulse
            st.session_state['m2_gap'] = m2_gap
            
            progress_bar.progress(100)
            status_text.text("✨ 量子量化全景篩選與 Portfolio Top 投組建構完畢！")
            time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
            st.rerun()

if 'df_res' in st.session_state and ('df_unqualified' in st.session_state):
    df_res = st.session_state['df_res']
    df_unqualified = st.session_state['df_unqualified']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("宏觀信貸脈衝 (實時)", st.session_state['credit_impulse'].split()[0], f"美債 {market_state['benchmark_tnx']}%")
    col2.metric("超額 M2 剪刀差", f"+{st.session_state['m2_gap']}%", "動態估值驅動")
    col3.metric("評估合格標的", f"{len(df_res)} 檔", "多因子量化評分通過")
    col4.metric("未通過 / 遭剔除", f"{len(df_unqualified)} 檔", "流動性或體質未達標")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 合格全景量化清單",
        "⚠️ 未通過檢驗 / 遭剔除清單",
        "🎯 Portfolio Top 15 核心投組", 
        "💰 投資建議與倉位配置總覽", 
        "🏆 專業投研技術與基本面解讀"
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
            st.metric("Top 15 總配置金額", f"€ {total_top15_amt:,.2f}", f"佔總資本 {round(total_top15_amt/total_capital*100, 1)}%")
            
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
                font_color='#F3F4F6',
                title_font_color='#22D3EE'
            )
            st.plotly_chart(fig_top15, use_container_width=True)
        
    with tab4:
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
                font_color='#F3F4F6',
                title_font_color='#22D3EE'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab5:
        st.markdown("### 🏆 依華爾街投資建議分類之深度技術、基本面與關鍵操盤解讀")
        
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
            sub_df = df_res[df_res['投資建議'] == rec].head(10)
            if not sub_df.empty:
                st.markdown(f"#### 🔥 【{rec}】精選標的 (共 {len(sub_df)} 檔)")
                for idx, row in sub_df.iterrows():
                    with st.expander(f"📌 {row['股票名稱']} ({row['股票代碼']}) — 現價: {row['最新現價']} | 綜合評分: {row['綜合評分']}分 | 建議: {row['投資建議']}"):
                        ca, cb, cc, cd = st.columns(4)
                        ca.metric("評估結果", row['評估結果'])
                        cb.metric("夏普比率 (Sharpe)", row['Sharpe Ratio'])
                        cc.metric("財務體質 (F-Score)", row['Piotroski F'])
                        cd.metric("ATR 停損位", row['ATR 停損位'])
                        
                        st.markdown(f"""
                        * **量化預測 IC**: `{row['量化預測 IC']}` | **破產預警 (Altman Z)**: `{row['Altman Z']}`
                        * **建議倉位配置**: `{row['建議倉位比例']}` (約 `{row['建議配置金額 (€)']:,} €`)
                        * **📊 技術面分析 (威科夫結構與 ATR)**: `{row['技術面分析 (威科夫/ATR)']}`
                        """)
                        
                        st.markdown("---")
                        st.markdown("##### ⚡ 華爾街 AI 戰情情報 (新聞要點與關鍵操盤點)")
                        
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
    st.info("👈 請在左側側邊欄點擊「⚡ 啟動量子量化篩選與投組構建」按鈕，展開專業的賽博未來風量化決策終端。")
