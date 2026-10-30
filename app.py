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
st.markdown("*基於《核心股票分析技巧指南》：結合威科夫結構、Sharpe Ratio、Piotroski F-Score、Altman Z-Score、獨立投資建議與倉位配置模組。*")

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

if st.sidebar.button("執行全景量化篩選與指標評估", type="primary"):
    if not selected_stocks:
        st.warning("請至少選取或載入一檔股票。")
    else:
        with st.spinner(f"正在對 {len(selected_stocks)} 檔標的計算 Sharpe Ratio、Piotroski F-Score、Altman Z-Score 與威科夫結構..."):
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

# 主畫面展示 (若已執行評估)
if 'df_res' in st.session_state and not st.session_state['df_res'].empty:
    df_res = st.session_state['df_res']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("宏觀信貸脈衝", st.session_state['credit_impulse'].split()[0], "流動性支持")
    col2.metric("超額 M2 剪刀差", f"+{st.session_state['m2_gap']}%", "估值擴張驅動")
    col3.metric("評估合格標的", f"{len(df_res)} 檔", "多因子量化評分")
    col4.metric("總配置資金", f"€ {total_capital:,.0f}", "分段凱利優化")
    
    # 建立多 Tab 介面：1. 全景綜合量化清單 | 2. 獨立投資建議與倉位配置模組 | 3. TOP 10 技術分析與 AI 報告
    tab1, tab2, tab3 = st.tabs(["📊 全景量化評估清單", "💰 投資建議與倉位配置專區", "🏆 分項 TOP 10 技術分析與 AI 總結"])
    
    with tab1:
        st.markdown("### 📈 著名量化指標與綜合評分總覽")
        st.markdown("*包含夏普比率 (Sharpe Ratio)、皮特羅斯基財務體質評分 (Piotroski F-Score) 與奧特曼破產預警指數 (Altman Z-Score)。*")
        display_df = df_res.drop(columns=['raw_price', '貨幣'], errors='ignore')
        st.dataframe(display_df, use_container_width=True)
        
    with tab2:
        st.markdown("### 💰 獨立投資建議與動態資金配置管理")
        st.markdown("本專區專門針對投資組合的**投資建議類型**與**分段凱利 / 建議配置金額**進行獨立檢視與管理：")
        
        # 依據投資建議分組統計配置金額
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
            fig_pie = px.pie(rec_summary, names='投資建議', values='總配置金額', title='各投資建議類別之資本配置佔比')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### 🎯 單一標的配置明細快速檢索")
        selected_rec_filter = st.selectbox("篩選投資建議類型", ["全部顯示"] + list(df_res['投資建議'].unique()))
        if selected_rec_filter == "全部顯示":
            alloc_view_df = df_res[['股票名稱', '股票代碼', '最新現價', '投資建議', '建議倉位比例', '建議配置金額 (€)', 'ATR 停損位']]
        else:
            alloc_view_df = df_res[df_res['投資建議'] == selected_rec_filter][['股票名稱', '股票代碼', '最新現價', '投資建議', '建議倉位比例', '建議配置金額 (€)', 'ATR 停損位']]
        st.dataframe(alloc_view_df, use_container_width=True)
        
    with tab3:
        st.markdown("### 🏆 依投資建議分類之 TOP 10 深度技術分析")
        rec_types = df_res['投資建議'].unique()
        for rec in rec_types:
            sub_df = df_res[df_res['投資建議'] == rec].head(10)
            if not sub_df.empty:
                st.markdown(f"#### 🔥 【{rec}】精選 TOP 標的 (共 {len(sub_df)} 檔)")
                for idx, row in sub_df.iterrows():
                    with st.expander(f"📌 {row['股票名稱']} ({row['股票代碼']}) — 現價: {row['最新現價']} | 綜合評分: {row['綜合評分']}分 | Sharpe: {row['Sharpe Ratio']} | F-Score: {row['Piotroski F']}"):
                        ca, cb, cc, cd = st.columns(4)
                        ca.metric("評估結果", row['評估結果'])
                        cb.metric("威科夫微觀結構", row['威科夫微觀結構'])
                        cc.metric("Altman Z", row['Altman Z'])
                        cd.metric("ATR 停損位", row['ATR 停損位'])
                        
                        st.markdown(f"""
                        * **量化 IC 預測評分**: `{row['量化預測 IC']}` | **夏普比率**: `{row['Sharpe Ratio']}`
                        * **財務體質 (Piotroski F-Score)**: `{row['Piotroski F']}` (衡量獲利、營運效率與財務結構)
                        * **建議倉位配置**: `{row['建議倉位比例']}` (約 `{row['建議配置金額 (€)']:,} €`)
                        * **技術與量價診斷**: 
                          該標的處於 `{row['威科夫微觀結構']}`。其 Sharpe 與財務體質評分優異，主力資金吸籌特徵明確，建議嚴格執行 ATR 停損位 `{row['ATR 停損位']}`。
                        """)
                        
        st.markdown("---")
        st.markdown("### 🤖 Gemini AI 總結與投研報告")
        if st.button("✨ 生成 Gemini AI 綜合評分總結報告", type="primary"):
            with st.spinner("正在調用 Gemini AI 進行全方位指標與總結解讀..."):
                ai_report = engine.analyze_with_gemini(
                    df_res, 
                    st.session_state['credit_impulse'],
                    st.session_state['m2_gap']
                )
                st.markdown(ai_report)
else:
    st.info("👈 請在左側點擊「執行全景量化篩選與指標評估」按鈕，產出包含著名量化指標、獨立投資建議與 TOP 10 技術分析的完整報告。")
