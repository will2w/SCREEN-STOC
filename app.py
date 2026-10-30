import streamlit as st
import pandas as pd
import plotly.express as px
from screener_engine import QuantScreenerEngine

st.set_page_config(
    page_title="多維度智能股票篩選與量化交易系統",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 現代多維度量化股票篩選與決策系統")
st.markdown("*基於《核心股票分析技巧指南》：即時聯動 Yahoo Finance、威科夫量價結構、凱利公式與 Gemini AI 深度投研診斷。*")

engine = QuantScreenerEngine()
watchlist = engine.watchlist

st.sidebar.header("🎛️ 策略參數與過濾面板")
credit_impulse = st.sidebar.selectbox("信貸脈衝狀態 (Credit Impulse)", ["擴張期 (Expansion - 偏多)", "收縮期 (Contraction - 防禦)"], index=0)
m2_gap = st.sidebar.slider("超額 M2 剪刀差 (ΔM2 - ΔGDP %)", -2.0, 5.0, 1.8, 0.1)

selected_stocks = st.sidebar.multiselect("選取目標標的池", watchlist, default=watchlist[:8] if len(watchlist)>=8 else watchlist)
kelly_mode = st.sidebar.selectbox("凱利公式模型", ["四分之一凱利 (0.25 f* - 機構推薦)", "半凱利 (0.5 f*)", "ATR 波動率目標化法"], index=0)

if st.sidebar.button("執行即時量化抓取與篩選", type="primary"):
    if not selected_stocks:
        st.warning("請至少選取一檔股票。")
    else:
        with st.spinner("正在聯動 Yahoo Finance API 抓取真實市場行情並計算量化指標..."):
            df_res = engine.run_screening(selected_stocks, capital=100000, credit_impulse_status=credit_impulse, method=kelly_mode)
            
        if df_res.empty:
            st.error("未能成功抓取選取標的的數據，請檢查網絡連線或標的代碼。")
        else:
            # Save to session state so Gemini analysis can access it
            st.session_state['df_res'] = df_res
            st.session_state['credit_impulse'] = credit_impulse
            
            col1, col2, col3 = st.columns(3)
            col1.metric("宏觀政策 Beta 評估", credit_impulse.split()[0], "流動性支持")
            col2.metric("超額 M2 剪刀差", f"+{m2_gap}%", "資產估值擴張")
            col3.metric("有效分析標的數", f"{len(df_res)} 檔", "即時數據聯動")
            
            st.markdown("### 📊 即時量化篩選與動態頭寸分配結果清單")
            st.dataframe(df_res, use_container_width=True)
            
            fig = px.bar(df_res, x='股票名稱', y='建議配置金額 (€)', color='量化預測 IC',
                         title='各標的之最佳資本配置與量化因子 IC 評分',
                         labels={'建議配置金額 (€)': '配置金額 (€)', '量化預測 IC': 'Alpha IC 評分'})
            st.plotly_chart(fig, use_container_width=True)

# 🤖 Gemini AI 深度投研診斷區塊
if 'df_res' in st.session_state and not st.session_state['df_res'].empty:
    st.markdown("---")
    st.markdown("### 🤖 Gemini AI 智能投研與選股深度診斷報告")
    if st.button("✨ 一鍵生成 Gemini 專業投研分析與配置優化報告", type="primary"):
        with st.spinner("正在調用 Gemini AI (gemini-3.8-flash) 進行多維度量化與基本面深度解讀..."):
            ai_report = engine.analyze_with_gemini(st.session_state['df_res'], st.session_state['credit_impulse'])
            st.markdown(ai_report)
else:
    st.info("👈 請先在左側選取標的並點擊「執行即時量化抓取與篩選」，隨後即可解鎖 Gemini AI 深度投研診斷報告。")
