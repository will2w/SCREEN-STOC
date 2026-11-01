# -*- coding: utf-8 -*-
"""
app.py
------
現代多維度量化股票篩選與決策引擎 (Streamlit 互動介面)
"""

import os
import streamlit as st
import pandas as pd
from screener_engine import QuantScreenerEngine

# 頁面基本設定
st.set_page_config(
    page_title="Global Quantitative Screening & Portfolio Engine",
    page_icon="📈",
    layout="wide"
)

# 載入自定義 CSS 樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🌍 全球多市場量化選股與動態資產配置引擎</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">整合多維度量化評分 (Piotroski F, Altman Z, Sharpe, IC) 與威科夫微觀結構的專業投研系統</div>', unsafe_allow_html=True)

    # 初始化引擎
    watchlist_file = "Watchlist_Stocks.xlsx"
    if not os.path.exists(watchlist_file) and os.path.exists("Watchlist_Stocks.csv"):
        watchlist_file = "Watchlist_Stocks.csv"
        
    engine = QuantScreenerEngine(watchlist_path=watchlist_file)

    # 側邊欄控制面板
    st.sidebar.header("⚙️ 投研參數與宏觀設定")
    
    # 取得自動偵測的宏觀狀態
    market_state = engine.get_current_market_state()
    
    st.sidebar.subheader("📊 宏觀信貸脈衝偵測")
    credit_status = st.sidebar.selectbox(
        "信貸脈衝週期狀態",
        ["擴張期 (Expansion - 流動性充沛)", "中性期 (Neutral)", "收縮期 (Contraction - 防禦為主)"],
        index=0 if "Expansion" in market_state["credit_impulse"] else 1
    )
    
    m2_gap = st.sidebar.slider(
        "超額 M2 剪刀差 (%)",
        min_value=-2.0, max_value=5.0,
        value=float(market_state["m2_gap"]), step=0.1
    )
    
    capital = st.sidebar.number_input(
        "總投資資本 (€)",
        min_value=10000, max_value=10000000,
        value=100000, step=10000
    )
    
    method = st.sidebar.selectbox(
        "動態倉位配置模型",
        ["Quarter Kelly (凱利公式修正版)", "Risk Parity (風險平價)", "Equal Weight (等權重)"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 監控標的清單預覽")
    if engine.watchlist:
        st.sidebar.info(f"目前共載入 **{len(engine.watchlist)}** 檔監控標的")
        with st.sidebar.expander("檢視標的清單"):
            for s in engine.watchlist:
                st.text(f"• {s}")
    else:
        st.sidebar.warning("⚠️ 尚未載入任何標的，請確認外部檔案。")

    # 主畫面按鈕
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        run_btn = st.button("🚀 執行量化篩選與投組配置", type="primary", use_container_width=True)

    if run_btn or 'has_run' in st.session_state:
        st.session_state['has_run'] = True
        
        with st.spinner("🔄 正在透過雙軌通道抓取全球即時行情、計算量化指標與威科夫結構中..."):
            passed_df, failed_df = engine.run_screening_with_unqualified(
                selected_stocks=engine.watchlist,
                capital=capital,
                credit_impulse_status=credit_status,
                m2_gap=m2_gap,
                method=method
            )

        st.markdown("---")
        st.subheader("🎯 Portfolio Top 核心配置清單 (通過量化篩選)")
        
        if not passed_df.empty:
            # 調整欄位顯示順序
            display_cols = [
                "股票名稱", "股票代碼", "最新現價", "綜合評分", 
                "投資建議", "建議倉位比例", "建議配置金額 (€)", 
                "Sharpe Ratio", "Piotroski F", "Altman Z", 
                "技術面分析 (威科夫/ATR)", "消息面與基本面解讀", "ATR 停損位"
            ]
            valid_cols = [c for c in display_cols if c in passed_df.columns]
            
            st.dataframe(
                passed_df[valid_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ 目前沒有任何標的通過嚴格的量化與流動性篩選標準。")

        # 失敗或不合格標的清單
        with st.expander("📌 未通過篩選標的與剔除原因（點擊展開）"):
            if not failed_df.empty:
                fail_cols = ["股票名稱", "股票代碼", "最新現價", "不合格原因"]
                valid_fail_cols = [c for c in fail_cols if c in failed_df.columns]
                st.dataframe(failed_df[valid_fail_cols], use_container_width=True, hide_index=True)
            else:
                st.success("🎉 太棒了！所有標的均通過篩選。")

        # AI 深度投研診斷報告
        st.markdown("---")
        st.subheader("🤖 華爾街級別 AI 量化投研與總經深度診斷報告")
        if st.button("✨ 生成 AI 深度解析報告", use_container_width=False):
            with st.spinner("💡 正在結合宏觀信貸脈衝與投組結構生成專業報告中..."):
                ai_report = engine.analyze_with_gemini(passed_df, credit_status, m2_gap)
                st.markdown(ai_report)

    else:
        st.info("👈 請在左側設定投研參數，並點擊上方「執行量化篩選與投組配置」按鈕開始分析。")

if __name__ == "__main__":
    main()
