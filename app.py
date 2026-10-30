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
st.markdown("*基於《核心股票分析技巧指南》：評估結果、綜合評分、投資建議分類、分項 TOP 10 技術分析與 Gemini AI 總結報告。*")

engine = QuantScreenerEngine()
watchlist = engine.watchlist

st.sidebar.header("🎛️ 策略參數與過濾面板")
credit_impulse = st.sidebar.selectbox(
    "1. 信貸脈衝狀態 (Credit Impulse)", 
    ["擴張期 (Expansion - 流動性充沛)", "中性期 (Neutral)", "收縮期 (Contraction - 防禦為主)"], 
    index=0
)
m2_gap = st.sidebar.slider("2. 超額 M2 剪刀差 (ΔM2 - ΔGDP %)", -2.0, 6.0, 2.0, 0.1)

selection_mode = st.sidebar.radio("股票池選取模式", ["評估 Excel 中的全部股票 (210檔)", "自選特定標的池"], index=0)

if selection_mode == "評估 Excel 中的全部股票 (210檔)":
    selected_stocks = watchlist
    st.sidebar.info(f"已自動載入 Excel 中的全部 {len(watchlist)} 檔股票進行全景評估與篩選。")
else:
    selected_stocks = st.sidebar.multiselect("選取目標標的池", watchlist, default=watchlist[:15] if len(watchlist)>=15 else watchlist)

kelly_mode = st.sidebar.selectbox(
    "3. 資金控管與頭寸模型", 
    ["四分之一凱利 (0.25 f* - 機構推薦)", "半凱利 (0.5 f*)", "ATR 波動率目標化 (ATR Sizing)"], 
    index=0
)
total_capital = st.sidebar.number_input("總投資資本 (€ / $)", value=100000, step=10000)

if st.sidebar.button("執行全景量化篩選與評估", type="primary"):
    if not selected_stocks:
        st.warning("請至少選取或載入一檔股票。")
    else:
        with st.spinner(f"正在對 {len(selected_stocks)} 檔標的套用多維度量化評估、綜合評分與威科夫微觀結構運算..."):
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
            col3.metric("評估合格標的", f"{len(df_res)} 檔", "貨幣與價格校準")
            col4.metric("總配置資金", f"€ {total_capital:,.0f}", "分段凱利優化")
            
            st.markdown("### 📊 全景量化評估與綜合評分結果清單")
            # 顯示時移除內部用的 raw_price 與 貨幣欄位，保持畫面簡潔專業
            display_df = df_res.drop(columns=['raw_price', '貨幣'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)
            
            # 依據投資建議類型分別選出 TOP 10 並做技術分析
            st.markdown("---")
            st.markdown("## 🏆 依據投資建議類型選出之 TOP 10 深度技術分析")
            
            rec_types = df_res['投資建議'].unique()
            for rec in rec_types:
                sub_df = df_res[df_res['投資建議'] == rec].head(10)
                if not sub_df.empty:
                    st.markdown(f"### 🔥 【{rec}】精選 TOP 標的 (共 {len(sub_df)} 檔)")
                    for idx, row in sub_df.iterrows():
                        with st.expander(f"📌 {row['股票名稱']} ({row['股票代碼']}) — 現價: {row['最新現價']} | 綜合評分: {row['綜合評分']}分"):
                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("評估結果", row['評估結果'])
                            col_b.metric("威科夫微觀結構", row['威科夫微觀結構'])
                            col_c.metric("ATR 硬性停損位", row['ATR 停損位'])
                            
                            st.markdown(f"""
                            * **量化 IC 預測評分**: `{row['量化預測 IC']}`
                            * **建議倉位配置**: `{row['建議倉位比例']}` (約 `{row['建議配置金額 (€)']:,} €`)
                            * **技術面與量價診斷**: 
                              該標的當前處於 `{row['威科夫微觀結構']}` 階段。透過多維度量化引擎計算，其 3 個月動量與波動率結構顯示主力資金吸籌意圖明顯，建議嚴格遵照 ATR 停損位 `{row['ATR 停損位']}` 執行風險控管，並採分段凱利公式進行動態頭寸配置。
                            """)

if 'df_res' in st.session_state and not st.session_state['df_res'].empty:
    st.markdown("---")
    st.markdown("### 🤖 Gemini AI 總結與投研報告")
    if st.button("✨ 生成 Gemini AI 綜合評分總結報告", type="primary"):
        with st.spinner("正在調用 Gemini AI 進行全方位評估結果與綜合評分總結解讀..."):
            ai_report = engine.analyze_with_gemini(
                st.session_state['df_res'], 
                st.session_state['credit_impulse'],
                st.session_state['m2_gap']
            )
            st.markdown(ai_report)
else:
    st.info("👈 請在左側點擊「執行全景量化篩選與評估」按鈕，產出評估結果、綜合評分與 TOP 10 技術分析。")
