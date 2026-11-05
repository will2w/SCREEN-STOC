# -*- coding: utf-8 -*-
"""
app.py
------
BANSHEE QUEEN // INSTITUTIONAL QUANTITATIVE TERMINAL (SYLVANAS MYTHIC EDITION)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import feedparser
import urllib.parse
from screener_engine import QuantScreenerEngine

st.set_page_config(
    page_title="INSTITUTIONAL QUANTITATIVE TERMINAL",
    page_icon="👑",
    layout="wide"
)

st.markdown("""
<style>
    /* 🦇 希爾瓦娜斯暗夜幽冥核心背景：被遺忘者禁忌深淵 */
    .stApp {
        background-color: #030305;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(88, 28, 135, 0.3) 0%, transparent 65%),
            radial-gradient(circle at 20% 85%, rgba(16, 185, 129, 0.12) 0%, transparent 50%),
            linear-gradient(rgba(148, 163, 184, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 35px 35px, 35px 35px;
        color: #E2E8F0;
        font-family: 'Cinzel', 'Segoe UI', 'Courier New', monospace, sans-serif;
    }

    /* 👑 希爾瓦娜斯史詩標題：黯月霜銀與劇毒凋零綠漸層 */
    .cyber-header {
        font-size: 2.8rem;
        font-weight: 900;
        background: linear-gradient(135deg, #F1F5F9 0%, #34D399 30%, #A855F7 70%, #6D28D9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 35px rgba(52, 211, 153, 0.35), 0 0 70px rgba(168, 85, 247, 0.25);
        margin-bottom: 0.1rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* ☠️ 被遺忘者禁忌戰情副標題線 */
    .cyber-sub {
        font-size: 1.02rem;
        color: #34D399;
        font-weight: 700;
        margin-bottom: 2rem;
        border-left: 4px solid #A855F7;
        padding-left: 0.85rem;
        background: linear-gradient(90deg, rgba(168, 85, 247, 0.15) 0%, transparent 100%);
        padding-top: 0.4rem;
        padding-bottom: 0.4rem;
        letter-spacing: 0.12em;
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.5);
    }

    /* 側邊欄：幽暗城暗影議會風格 */
    [data-testid="stSidebar"] {
        background-color: rgba(8, 8, 14, 0.96);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(168, 85, 247, 0.35);
        box-shadow: 10px 0 40px rgba(0, 0, 0, 0.95);
    }

    /* 數據表格：被遺忘者黑曜石框體 */
    div.stDataFrame {
        border: 1px solid rgba(52, 211, 153, 0.35);
        border-radius: 0.6rem;
        background-color: rgba(10, 10, 18, 0.92);
        backdrop-filter: blur(12px);
        padding: 0.6rem;
        box-shadow: 0 12px 35px -5px rgba(0, 0, 0, 0.95), 0 0 25px rgba(52, 211, 153, 0.1);
    }

    /* 分頁標籤：女妖之嚎能量條風格 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(10, 10, 18, 0.95);
        padding: 10px;
        border-radius: 0.6rem;
        border: 1px solid rgba(168, 85, 247, 0.3);
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
        color: #34D399;
        background-color: rgba(52, 211, 153, 0.1);
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.7);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #581C87 0%, #065F46 60%, #0F172A 100%);
        color: #F8FAFC !important;
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.4), inset 0 0 12px rgba(52, 211, 153, 0.5);
        border: 1px solid rgba(52, 211, 153, 0.6);
    }

    /* 按鈕：暗影之箭烈焰按鈕 */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #7E22CE 0%, #047857 50%, #312E81 100%);
        border: 1px solid rgba(52, 211, 153, 0.6);
        color: white;
        font-weight: 900;
        letter-spacing: 0.12em;
        border-radius: 0.4rem;
        box-shadow: 0 0 35px rgba(126, 34, 206, 0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #9333EA 0%, #10B981 50%, #4338CA 100%);
        box-shadow: 0 0 50px rgba(52, 211, 153, 0.8), 0 0 25px rgba(168, 85, 247, 0.9);
        transform: translateY(-2px) scale(1.02);
    }

    /* 數據指標外框 */
    [data-testid="stMetric"] {
        background-color: rgba(12, 12, 22, 0.88);
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 15px;
        border-radius: 0.5rem;
        box-shadow: 0 0 25px rgba(0, 0, 0, 0.85);
    }
    [data-testid="stMetricValue"] {
        color: #34D399 !important;
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.6);
    }

    /* ☠️ 分數變化彩色標籤 (Buff / Debuff Badge) */
    .buff-badge {
        color: #34D399;
        background-color: rgba(52, 211, 153, 0.15);
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 800;
        text-shadow: 0 0 8px rgba(52, 211, 153, 0.6);
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

st.markdown('<div class="cyber-header">👑 BANSHEE QUEEN // QUANTUM ALPHA TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-sub">[INSTITUTIONAL_QUANT_CORE] // BLACK-LITTERMAN BAYESIAN OPTIMIZATION & TAIL RISK SCREENING</div>', unsafe_allow_html=True)

engine = QuantScreenerEngine()
default_watchlist = engine.watchlist

market_state = engine.get_current_market_state()
default_impulse = market_state["credit_impulse"]
default_m2 = market_state["m2_gap"]

st.sidebar.header("🎛️ 總體經濟與流動性控制台")
st.sidebar.info(f"🌐 實時宏觀數據同步 ({market_state['sync_date']}): 10年期美債收益率 {market_state['benchmark_tnx']}%")

impulse_options = [
    "擴張期 (Expansion - 流動性充沛)", 
    "中性期 (Neutral)", 
    "收縮期 (Contraction - 防禦為主)"
]
default_impulse_idx = impulse_options.index(default_impulse) if default_impulse in impulse_options else 0

credit_impulse = st.sidebar.selectbox(
    "1. 宏觀信貸脈衝 (Credit Impulse)", 
    impulse_options, 
    index=default_impulse_idx
)

m2_gap = st.sidebar.slider(
    "2. 超額貨幣供應剪刀差 (ΔM2 - ΔGDP %)", 
    -2.0, 6.0, float(default_m2), 0.1
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 📁 資產池來源與輸入模式")

watchlist_source = st.sidebar.radio(
    "選擇證券池來源", 
    ["預設專業清單檔案", "上傳自定義資料集 (Excel/CSV)", "手動輸入標的代碼"],
    label_visibility="collapsed"
)

active_watchlist = default_watchlist

if watchlist_source == "上傳自定義資料集 (Excel/CSV)":
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
            st.sidebar.success(f"✅ 成功載入上傳標的集，共 {len(active_watchlist)} 檔。")
        except Exception as e:
            st.sidebar.error(f"❌ 讀取檔案失敗: {e}")

elif watchlist_source == "手動輸入標的代碼":
    manual_input = st.sidebar.text_area(
        "輸入證券代碼 (支援逗號或換行分隔)", 
        value="NVDA, AAPL, TSLA, MSFT, BAS.DE, EON.DE",
        height=100
    )
    if manual_input:
        raw_items = manual_input.replace(";", ",").replace("\n", ",").split(",")
        active_watchlist = [item.strip() for item in raw_items if item.strip()]
        st.sidebar.success(f"✅ 已解析手動輸入之 {len(active_watchlist)} 檔標的。")

st.sidebar.markdown("---")
selection_mode = st.sidebar.radio(
    "篩選執行範圍", 
    ["全體證券評估", "自選特定子集組合"], 
    index=0
)

if selection_mode == "全體證券評估":
    selected_stocks = active_watchlist
    st.sidebar.info(f"📊 將全面執行當前來源之 {len(active_watchlist)} 檔標的量化模型審判。")
else:
    selected_stocks = st.sidebar.multiselect("從清單中勾選目標標的", active_watchlist, default=active_watchlist[:15] if len(active_watchlist)>=15 else active_watchlist)

st.sidebar.markdown("---")
kelly_mode = st.sidebar.selectbox(
    "3. 投資組合配置模型 (Portfolio Optimization)", 
    ["Black-Litterman 貝葉斯資產配置模型 (機構推薦)", "fractional Kelly Criterion (0.25 凱利模型)", "ATR Volatility-Targeted Sizing (波動率目標化)"], 
    index=0
)

total_capital = st.sidebar.number_input(
    "總運用資本額 (Total Capital, € / $)", 
    value=100000, 
    step=10000
)

st.sidebar.markdown("---")
run_btn = st.sidebar.button("👑 執行多因子計量模型審判與投組最佳化", type="primary", use_container_width=True)

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
        st.warning("請至少選取或輸入一檔證券標的。")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🦇 [01/03] 建立安全數據連線、同步宏觀經濟指標與實時信貸脈衝...")
        progress_bar.progress(25)
        time.sleep(0.2)
        
        status_text.text("🚀 [02/03] 運行多維度量化因子模型、Sortino/MDD 尾部風險與貝葉斯估值...")
        progress_bar.progress(60)
        
        df_res, df_unqualified = engine.run_screening_with_unqualified(
            selected_stocks, 
            capital=total_capital, 
            credit_impulse_status=credit_impulse, 
            m2_gap=m2_gap, 
            method=kelly_mode
        )
        
        status_text.text("💎 [03/03] 計算 Calmar 報酬回撤比、Beta 系統風險與淨資本配置權重...")
        progress_bar.progress(90)
        time.sleep(0.2)
        
        if df_res.empty and df_unqualified.empty:
            progress_bar.empty()
            status_text.empty()
            st.error("量化篩選結果為空，請檢查網路連線或標的代碼是否正確。")
        else:
            st.session_state['df_res'] = df_res
            st.session_state['df_unqualified'] = df_unqualified
            st.session_state['credit_impulse'] = credit_impulse
            st.session_state['m2_gap'] = m2_gap
            
            progress_bar.progress(100)
            status_text.text("✨ 華爾街級計量資產審判與核心投資組合 (Portfolio Top) 構築完成！")
            time.sleep(0.3)
            
            progress_bar.empty()
            status_text.empty()
            st.rerun()

if 'df_res' in st.session_state and ('df_unqualified' in st.session_state):
    df_res = st.session_state['df_res']
    df_unqualified = st.session_state['df_unqualified']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("宏觀信貸脈衝 (Credit Impulse)", st.session_state['credit_impulse'].split()[0], f"美債收益率 {market_state['benchmark_tnx']}%")
    col2.metric("超額貨幣剪刀差 (ΔM2-ΔGDP)", f"+{st.session_state['m2_gap']}%", "動態估值驅動因子")
    col3.metric("計量審判合格標的數", f"{len(df_res)} 檔", "多因子計量模型通過")
    col4.metric("風控模型剔除標的數", f"{len(df_unqualified)} 檔", "流動性或尾部風險未達標")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 合格證券全景量化清單",
        "⚠️ 風控模型剔除標的清單",
        "🎯 Portfolio Top 15 核心投資組合", 
        "⚡ TOP 10 短期動能與中長線價值雙軌戰情室",
        "💰 資本配置與資產分配總覽", 
        "🏆 依投資建議分類之 TOP 5 深度計量解讀"
    ])
    
    with tab1:
        st.markdown("### 📊 通過多維度計量檢驗之合格證券資產池 (含機構級風控參數)")
        if df_res.empty:
            st.warning("⚠️ 目前無符合量化標準之合格標的。")
        else:
            excel_view_df = df_res.drop(columns=['raw_price', '貨幣', '建議倉位比例', '建議配置金額 (€)', '不合格原因'], errors='ignore')
            st.dataframe(excel_view_df, use_container_width=True, height=600)
        
    with tab2:
        st.markdown("### ⚠️ 未通過量化檢驗 / 遭風控模型剔除之標的清單與原因")
        if df_unqualified.empty:
            st.info("🎉 太棒了！當前資產池中無任何標的觸發風控剔除機制。")
        else:
            unqualified_display = df_unqualified.drop(columns=['raw_price', '貨幣', '建議倉位比例', '建議配置金額 (€)'], errors='ignore')
            st.dataframe(unqualified_display, use_container_width=True, height=550)
        
    with tab3:
        st.markdown("### 🎯 Portfolio Top 15 核心投資組合推薦 (Black-Litterman Bayesian Allocation)")
        if df_res.empty:
            st.warning("⚠️ 目前無合格標的可用以建構投資組合。")
        else:
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
                    font_color='#F8FAFC',
                    title_font_color='#34D399'
                )
                st.plotly_chart(fig_top15, use_container_width=True)

    with tab4:
        st.markdown("### ⚡ TOP 10 短期動能操作 vs TOP 10 中長線價值配置雙軌戰情室")
        if df_res.empty:
            st.warning("⚠️ 目前無合格標的可用以生成雙軌戰情室。")
        else:
            st.markdown("結合**量化計量指標**、**即時 RSS 財經頭條新聞**與 **Gemini AI 貝葉斯情感觀點**，為您完整開展短中長線的精準操盤指引。")
            
            df_short_top10, df_long_top10 = engine.get_dual_track_top10(df_res, capital=total_capital)
            
            st.markdown("---")
            st.markdown("#### 🚀 TOP 10 短期動能操作精選標的 (Tactical Momentum)")
            if df_short_top10.empty:
                st.info("合格資產池數量不足 10 檔。")
            else:
                st.dataframe(df_short_top10, use_container_width=True, height=450)
                
            st.markdown("---")
            st.markdown("#### 🏛️ TOP 10 中長線價值佈局精選標的 (Strategic Value)")
            if df_long_top10.empty:
                st.info("合格資產池數量不足 10 檔。")
            else:
                st.dataframe(df_long_top10, use_container_width=True, height=450)
        
    with tab5:
        st.markdown("### 💰 投資建議與動態資本配置總覽")
        if df_res.empty or '投資建議' not in df_res.columns:
            st.warning("⚠️ 目前無合格標的或資料結構不足以進行配置總覽。")
        else:
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
                    title_font_color='#34D399'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab6:
        st.markdown("### 🏆 依華爾街投資建議分類之 TOP 5 深度技術、基本面與關鍵操盤解讀")
        if df_res.empty or '投資建議' not in df_res.columns:
            st.warning("⚠️ 目前無合格標的可用以進行深度計量解讀。")
        else:
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
                        diff_val_str = str(row['分數變化 (Δ)'])
                        is_positive = not diff_val_str.startswith("-")
                        badge_class = "buff-badge" if is_positive else "debuff-badge"
                        delta_html = f'<span class="{badge_class}">Δ {diff_val_str}</span>'

                        with st.expander(f"📌 {row['股票名稱']} ({row['股票代碼']}) — 現價: {row['最新現價']} | 綜合評分: {row['綜合評分']}分 ({delta_html}) | 建議: {row['投資建議']}", expanded=False):
                            ca, cb, cc, cd = st.columns(4)
                            ca.metric("索提諾比率 (Sortino Ratio)", row.get('Sortino Ratio', 1.0))
                            cb.metric("最大回撤 (Maximum Drawdown)", row.get('最大回撤 (MDD)', '0.0%'))
                            cc.metric("市場貝塔 (Market Beta)", row.get('貝塔係數 (Beta)', 1.0))
                            cd.metric("卡爾瑪比率 (Calmar Ratio)", row.get('卡爾瑪比率', 1.0))
                            
                            st.markdown(f"""
                            * **技術面指標數據**: `{row['技術面數據']}` | **消息面量化得分**: `{row['消息面分數']}`
                            * **資訊係數預測 (IC Score)**: `{row['量化預測 IC']}` | **前版純量化基準分**: `{row['上一版純量化分']}`
                            * **建議資本配置比例**: `{row['建議倉位比例']}` (約合 `{row['建議配置金額 (€)']:,} €`)
                            * **📊 威科夫微觀結構與 ATR 風控**: `{row['技術面分析 (威科夫/ATR)']}`
                            """)
                            
                            st.markdown("---")
                            st.markdown("##### ⚡ 華爾街級 AI 戰情情報 (新聞總結、貝葉斯觀點與操盤指引)")
                            
                            with st.spinner(f"正在同步 {row['股票名稱']} 實時新聞情報與計量模型中..."):
                                ai_insight, rss_news = cached_ai_analysis(
                                    stock_name=row['股票名稱'],
                                    symbol=row['股票代碼'],
                                    tech_str=row['技術面分析 (威科夫/ATR)'],
                                    fundamental_str=row['消息面與基本面解讀']
                                )
                            
                            if rss_news:
                                with st.expander("查看參考之即時 RSS 財經頭條"):
                                    for news in rss_news:
                                        st.markdown(f"- [{news['title']}]({news['link']}) `({news['published'][:16]})`")
                            
                            st.markdown(ai_insight)
                            
        st.markdown("---")
        st.markdown("### 🤖 Gemini AI 全局資產配置與宏觀戰情室報告")
        if st.button("✨ 啟動 Gemini AI 巨集戰情室總結診斷", type="primary"):
            with st.spinner("正在生成全局宏觀與投組配置總結報告..."):
                ai_report = engine.analyze_with_gemini(
                    df_res, 
                    st.session_state['credit_impulse'],
                    st.session_state['m2_gap']
                )
                st.markdown(ai_report)
else:
    st.info("👈 請在左側側邊欄點擊「👑 執行多因子計量模型審判與投組最佳化」按鈕，展開專業的機構級量化決策終端。")
