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
st.markdown("*基於《核心股票分析技巧指南》：融合威科夫量價微觀結構、信貸脈衝宏觀 Beta、可交易性掩碼與分段凱利頭寸管理。*")

engine = QuantScreenerEngine()
watchlist = engine.watchlist

st.sidebar.header("🎛️ 策略參數與過濾面板")
credit_impulse = st.sidebar.selectbox(
    "1. 信貸脈衝狀態 (Credit Impulse)", 
    ["擴張期 (Expansion - 流動性充沛)", "中性期 (Neutral)", "收縮期 (Contraction - 防禦為主)"], 
    index=0
)
m2_gap = st.sidebar.slider("2. 超額 M2 剪刀差 (ΔM2 - ΔGDP %)", -2.0, 6.0, 2.0, 0.1)

# 提供一鍵全選所有 EXCEL 股票或自選標的
selection_mode = st.sidebar.radio("股票池選取模式", ["評估 Excel 中的全部股票 (210檔)", "自選特定標的池"], index=0)

if selection_mode == "評估 Excel 中的全部股票 (210檔)":
    selected_stocks = watchlist
    st.sidebar.info(f"已自動載入 Excel 中的全部 {len(watchlist)} 檔股票進行全景量化評估與篩選。")
else:
    selected_stocks = st.sidebar.multiselect("選取目標標的池", watchlist, default=watchlist[:15] if len(watchlist)>=15 else watchlist)

kelly_mode = st.sidebar.selectbox(
    "3. 資金控管與頭寸模型", 
    ["四分之一凱利 (0.25 f* - 機構推薦)", "半凱利 (0.5 f*)", "ATR 波動率目標化 (ATR Sizing)"], 
    index=0
)
total_capital = st.sidebar.number_input("總投資資本 (€ / $)", value=100000, step=10000)

if st.sidebar.button("執行全景量化篩選與威科夫診斷", type="primary"):
    if not selected_stocks:
        st.warning("請至少選取或載入一檔股票。")
    else:
        with st.spinner(f"正在對 {len(selected_stocks)} 檔標的套用可交易性掩碼、威科夫結構、宏觀信貸脈衝與凱利頭寸模型運算..."):
            df_res = engine.run_screening(
                selected_stocks, 
                capital=total_capital, 
                credit_impulse_status=credit_impulse, 
                m2_gap=m2_gap, 
                method=kelly_mode
            )
            
        if df_res.empty:
            st.error("篩選結果為空，請檢查網絡連線或標的流動性狀態。")
        else:
            st.session_state['df_res'] = df_res
            st.session_state['credit_impulse'] = credit_impulse
            st.session_state['m2_gap'] = m2_gap
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("宏觀信貸脈衝", credit_impulse.split()[0], "流動性支持")
            col2.metric("超額 M2 剪刀差", f"+{m2_gap}%", "估值擴張驅動")
            col3.metric("過濾後合格標的", f"{len(df_res)} 檔", "通過可交易性掩碼")
            col4.metric("總配置資金", f"€ {total_capital:,.0f}", "分段凱利優化")
            
            st.markdown("### 📊 全景量化篩選與動態頭寸分配結果清單 (Top Alpha)")
            st.dataframe(df_res, use_container_width=True)
            
            # 視覺化 Top 15 配置
            top_chart_df = df_res.head(15)
            fig = px.bar(
                top_chart_df, 
                x='股票名稱', 
                y='建議配置金額 (€)', 
                color='量化預測 IC',
                title=' Top 15 潛力標的之最佳資本配置與 Alpha IC 評分',
                labels={'建議配置金額 (€)': '配置金額 (€)', '量化預測 IC': 'Alpha IC 評分'}
            )
            st.plotly_chart(fig, use_container_width=True)

if 'df_res' in st.session_state and not st.session_state['df_res'].empty:
    st.markdown("---")
    st.markdown("### 🤖 Gemini AI 智能投研與選股深度診斷報告")
    if st.button("✨ 一鍵生成 Gemini 專業投研分析與配置優化報告", type="primary"):
        with st.spinner("正在調用 Gemini AI (gemini-3.8-flash) 進行多維度量化與基本面深度解讀..."):
            ai_report = engine.analyze_with_gemini(
                st.session_state['df_res'], 
                st.session_state['credit_impulse'],
                st.session_state['m2_gap']
            )
            st.markdown(ai_report)
else:
    st.info("👈 請在左側點擊「執行全景量化篩選與威科夫診斷」按鈕，對 Excel 中的股票進行全方位評估與過濾。"
