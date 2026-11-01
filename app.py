# -*- coding: utf-8 -*-
"""
app.py
------
現代多維度量化股票篩選與決策系統 (未來科技/賽博龐克風升級版)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import time
from screener_engine import QuantScreenerEngine

st.set_page_config(
    page_title="QUANTUM TERMINAL — 智能量化交易與決策系統",
    page_icon="⚡",
    layout="wide"
)

# ⚡ 注入未來科技/賽博龐克風格 CSS 樣式
st.markdown("""
<style>
    /* 全局背景與字型優化 */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 頂部標題未來感霓虹光暈 */
    .tech-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(56, 189, 248, 0.3);
        margin-bottom: 0.2rem;
        letter-spacing: -0.025em;
    }
    
    .tech-sub {
        font-size: 1.05rem;
        color: #94A3B8;
        font-weight: 400;
        margin-bottom: 2rem;
        border-left: 3px solid #38BDF8;
        padding-left: 0.75rem;
    }

    /* 側邊欄科技面板化 */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }

    /* 卡片與數據框微光邊框 */
    div.stDataFrame {
        border: 1px solid #1E293B;
        border-radius: 0.75rem;
        background-color: #0F172A;
        padding: 0.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.05);
    }
    
    /* 標籤頁 (Tabs) 科技化改造 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0F172A;
        padding: 6px;
        border-radius: 0.75rem;
        border: 1px solid #1E293B;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent;
        border-radius: 6px;
        color: #94A3B8;
        font-weight: 600;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284C7 0%, #4338CA 100%);
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(2, 132, 199, 0.5);
    }

    /* 按鈕霓虹光感 */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #0284C7 0%, #6366F1 100%);
        border: none;
        color: white;
        font-weight: 700;
        border-radius: 0.5rem;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369A1 0%, #4F46E5 100%);
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.7);
        transform: translateY(-1px);
    }

    /* Expander 展開面板優化 */
    div.streamlit-expanderHeader {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 0.5rem;
        color: #E2E8F0;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="tech-header">⚡ QUANTUM ALPHA TERMINAL</div>', unsafe_allow_html=True)
st.markdown('<div class="tech-sub">GLOBAL QUANTITATIVE SCREENING & DYNAMIC ASSET ALLOCATION ENGINE // 2026 CYBERNETIC EDITION</div>', unsafe_allow_html=True)

engine = QuantScreenerEngine()
watchlist = engine.watchlist

market_state = engine.get_current_market_state()
default_impulse = market_state["credit_impulse"]
default_m2 = market_state["m2_gap"]

st.sidebar.header("🎛️ 策略參數與過濾面板")
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

if run_btn:
    if not selected_stocks:
        st.warning("請至少選取或載入一檔股票。")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("⚡ 正在建立安全連線、同步全球宏觀與實時流動性狀態...")
        progress_bar.progress(25)
        time.sleep(0.3)
        
        status_text.text("🚀 執行多維度量化引擎、威科夫微觀結構與華爾街評分運算...")
        progress_bar.progress(60)
        
        df_res, df_unqualified = engine.run_screening_with_unqualified(
            selected_stocks, 
            capital=total_capital, 
            credit_impulse_status=credit_impulse, 
            m2_gap=m2_gap, 
            method=kelly_mode
        )
        
        status_text.text("💎 計算 Sharpe、IC 分數與 100% 歸一化動態頭寸配置...")
        progress_bar.progress(90)
        time.sleep(0.3)
        
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
            time.sleep(0.4)
            
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
                font_color='#E2E8F0'
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
                font_color='#E2E8F0'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab5:
        st.markdown("### 🏆 依華爾街投資建議分類之深度技術與基本面解讀")
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
                        * **📊 技術面分析 (威科夫結構與 ATR)**:  
                          > `{row['技術面分析 (威科夫/ATR)']}`
                        * **📰 消息面與基本面解讀**:  
                          > `{row['消息面與基本面解讀']}`
                        """)
                        
        st.markdown("---")
        st.markdown("### 🤖 Gemini AI 總結與投研報告")
        if st.button("✨ 啟動 Gemini AI 量子深度診斷", type="primary"):
            with st.spinner("正在調用量子大模型進行全方位指標與總結解讀..."):
                ai_report = engine.analyze_with_gemini(
                    df_res, 
                    st.session_state['credit_impulse'],
                    st.session_state['m2_gap']
                )
                st.markdown(ai_report)
else:
    st.info("👈 請在左側側邊欄點擊「⚡ 啟動量子量化篩選與投組構建」按鈕，展開專業的賽博未來風量化決策終端。")
