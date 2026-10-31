# -*- coding: utf-8 -*-
"""
app.py
------
現代多維度量化股票篩選與投組配置終端 (Streamlit 介面主程式)
"""

import streamlit as st
import pandas as pd
import os
from screener_engine import QuantScreenerEngine

# 頁面基本設定
st.set_page_config(
    page_title="QuantScreener & Portfolio Engine",
    page_icon="📈",
    layout="wide"
)

st.title("📈 現代多維度量化股票篩選與決策引擎")
st.markdown("結合宏觀信貸脈衝、IC 預測分數、Piotroski F-Score、Altman Z 與威科夫微觀結構的量化投研終端機。")

# 初始化引擎
@st.cache_resource
def get_engine():
    return QuantScreenerEngine(watchlist_path="Watchlist_Stocks.xlsx", cache_path="symbol_cache.json")

engine = get_engine()

# 側邊欄控制面板
st.sidebar.header("⚙️ 投研控制面板")
capital = st.sidebar.number_input("總配置資金 (€)", min_value=1000, max_value=10000000, value=100000, step=5000)

# 取得當前宏觀狀態
market_state = engine.get_current_market_state()
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 即時宏觀狀態")
st.sidebar.info(f"**同步日期**: {market_state['sync_date']}\n\n"
                f"**美國 10 年期國債 (TNX)**: {market_state['benchmark_tnx']}%\n\n"
                f"**信貸脈衝週期**: {market_state['credit_impulse']}\n\n"
                f"**超額 M2 剪刀差**: +{market_state['m2_gap']}%")

st.sidebar.markdown("---")
run_btn = st.sidebar.button("🚀 開始量化篩選與投組建構", type="primary")

# 主畫面標籤頁
tab1, tab2, tab3 = st.tabs(["📊 核心投資組合 (Top 15)", "⚠️ 排除清單與評估明細", "🤖 AI 深度投研診斷"])

# 載入觀察清單
watchlist = engine.watchlist
if not watchlist:
    st.warning("⚠️ 找不到 `Watchlist_Stocks.xlsx` 或清單為空，請確認檔案是否存在。")

# 點擊執行篩選
if run_btn:
    if not watchlist:
        st.error("無法執行篩選：觀察清單為空。")
    else:
        with st.status("🔄 正在透過模擬真人 Session 與 Chart API 高效通道進行量化計算...", expanded=True) as status:
            st.write("步驟 1/3: 初始化市場宏觀與代碼解析...")
            
            # 執行量化篩選
            passed_df, failed_df = engine.run_screening_with_unqualified(
                watchlist, 
                capital=capital, 
                credit_impulse_status=market_state['credit_impulse'], 
                m2_gap=market_state['m2_gap']
            )
            
            st.write("步驟 2/3: 計算 Sharpe 比例、IC Score 與 100% 歸一化動態頭寸...")
            st.write("步驟 3/3: 生成投組配置與報告...")
            
            # 暫存至 session_state 供各 Tab 顯示
            st.session_state['passed_df'] = passed_df
            st.session_state['failed_df'] = failed_df
            st.session_state['market_state'] = market_state
            st.session_state['capital'] = capital
            
            status.update(label="✅ 量化篩選與投組配置計算完成！", state="complete", expanded=False)

# 從 session_state 讀取結果顯示
passed_df = st.session_state.get('passed_df', pd.DataFrame())
failed_df = st.session_state.get('failed_df', pd.DataFrame())

with tab1:
    st.subheader("🌟 Portfolio Top 15 核心投資組合配置")
    if not passed_df.empty:
        # 🛡️ 防禦性檢查：確認欄位存在再計算總金額
        total_amt = passed_df['建議配置金額 (€)'].sum() if '建議配置金額 (€)' in passed_df.columns else 0.0
        total_pct = passed_df['建議倉位比例'].str.rstrip('%').astype(float).sum() if '建議倉位比例' in passed_df.columns else 0.0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("通過篩選標的數", f"{len(passed_df)} 檔")
        col2.metric("總配置資金", f"€ {total_amt:,.2f}")
        col3.metric("總倉位佔比", f"{total_pct:.1f}%")
        
        st.dataframe(passed_df, use_container_width=True)
    else:
        st.info("ℹ️ 目前尚無通過篩選的標的。請點擊側邊欄的「開始量化篩選」按鈕，或檢查觀察清單與網路狀態。")

with tab2:
    st.subheader("🔍 未通過 / 暫時剔除標的與原因明細")
    if not failed_df.empty:
        st.dataframe(failed_df, use_container_width=True)
    else:
        st.info("ℹ️ 目前沒有被排除的標的。")

with tab3:
    st.subheader("🤖 華爾街量化投研 AI 深度診斷報告")
    if not passed_df.empty:
        if st.button("✨ 生成 Gemini AI 深度解析"):
            with st.spinner("正在呼叫 Gemini 模型生成專業投研報告..."):
                ai_report = engine.analyze_with_gemini(
                    passed_df, 
                    market_state['credit_impulse'], 
                    market_state['m2_gap']
                )
                st.markdown(ai_report)
    else:
        st.warning("⚠️ 請先執行量化篩選，確保有可用的 Top 15 投組數據後再生成 AI 診斷報告。")
