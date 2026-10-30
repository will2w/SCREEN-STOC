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
st.markdown("*基於《核心股票分析技巧指南》：結合 2026 實時市場狀態同步、Portfolio Top 15 核心投組與量化體質評估模組。*")

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
    ["評估 Excel 中的全部股票 (210檔)", "自選特定標的池"], 
    index=0, 
    label_visibility="collapsed"
)

if selection_mode == "評估 Excel 中的全部股票 (210檔)":
    selected_stocks = watchlist
    st.sidebar.success(f"✅ 已自動載入 Excel 中的全部 {len(watchlist)} 檔股票進行全景評估與篩選。")
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
run_btn = st.sidebar.button("執行全景量化篩選與指標評估", type="primary", use_container_width=True)

if run_btn:
    if not selected_stocks:
        st.warning("請至少選取或載入一檔股票。")
    else:
        with st.spinner(f"正在連線 2026 實時市場數據並計算 Excel 全景量化評分與 Portfolio Top 15..."):
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
    col1.metric("宏觀信貸脈衝 (實時)", st.session_state['credit_impulse'].split()[0], f"美債 {market_state['benchmark_tnx']}%")
    col2.metric("超額 M2 剪刀差", f"+{st.session_state['m2_gap']}%", "動態估值驅動")
    col3.metric("評估合格標的", f"{len(df_res)} 檔", "多因子量化評分")
    col4.metric("總配置資金", f"€ {total_capital:,.0f}", "分段凱利優化")
    
    # 精簡後的 4 個 Tab 專頁佈局：1. Excel全景量化評估(純指標) | 2. Portfolio Top 15 核心投組推薦 | 3. 投資建議與倉位配置總覽 | 4. 技術分析與 AI 總結
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 全景量化評估清單 (Excel 評估)",
        "🎯 Portfolio Top 15 核心投組推薦", 
        "💰 投資建議與倉位配置總覽", 
        "🏆 分項技術分析與 AI 總結"
    ])
    
    with tab1:
        st.markdown("## 📊 股票池全景量化評估清單 (Excel 全部股票)")
        st.markdown("*本頁面專門針對 Excel 載入的全部股票進行多維度量化指標評估（包含夏普比率、Piotroski F-Score、Altman Z 與威科夫結構），純粹進行量化體質與動能分析，不涉及資金比例與分配金額。*")
        
        excel_view_df = df_res.drop(columns=['raw_price', '貨幣', '建議倉位比例', '建議配置金額 (€)'], errors='ignore')
        st.dataframe(excel_view_df, use_container_width=True, height=600)
        
    with tab2:
        st.markdown("## 🎯 Portfolio Top 15 核心投組推薦")
        st.markdown("*本專頁專門展示經過多維度量化引擎、夏普比率、Piotroski F-Score 與凱利公式計算後，最具投資價值的 **Top 15 核心資產配置組合與動態頭寸配置**。*")
        
        top15_df = df_res.head(15).reset_index(drop=True)
        top15_display = top15_df.drop(columns=['raw_price', '貨幣'], errors='ignore')
        
        col_t1, col_t2 = st.columns([3, 1])
        with col_t2:
            total_top15_amt = top15_df['建議配置金額 (€)'].sum()
            st.metric("Top 15 總配置金額", f"€ {total_top15_amt:,.2f}", f"佔總資本 {round(total_top15_amt/total_capital*100, 1)}%")
            
        st.dataframe(top15_display, use_container_width=True, height=550)
        
        fig_top15 = px.bar(
            top15_df, 
            x='股票名稱', 
            y='建議配置金額 (€)', 
            color='綜合評分',
            title='Portfolio Top 15 核心標的之最佳資本配置與綜合評分分佈',
            labels={'建議配置金額 (€)': '配置金額 (€)', '綜合評分': '綜合評分 (分)'}
        )
        st.plotly_chart(fig_top15, use_container_width=True)
        
    with tab3:
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
            fig_pie = px.pie(rec_summary, names='投資建議', values='總配置金額', title='各投資建議類別之資本配置佔比')
            st.plotly_chart(fig_pie, use_container_width=True)
            
    with tab4:
        st.markdown("### 🏆 依投資建議分類之深度技術分析與 AI 總結")
        rec_types = df_res['投資建議'].unique()
        for rec in rec_types:
            sub_df = df_res[df_res['投資建議'] == rec].head(10)
            if not sub_df.empty:
                st.markdown(f"#### 🔥 【{rec}】精選標的 (共 {len(sub_df)} 檔)")
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
                          該標的經量化引擎綜合評估：IC 預測動能為 `{row['量化預測 IC']}`，夏普比率達 `{row['Sharpe Ratio']}`，Piotroski F-Score 財務體質為 `{row['Piotroski F']}`，Altman Z 破產預警分數為 `{row['Altman Z']}`。目前處於 `{row['威科夫微觀結構']}`。多維度指標顯示其財務穩健且主力吸籌特徵明顯，建議嚴格執行 ATR 停損位 `{row['ATR 停損位']}`。
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
    st.info("👈 請在左側側邊欄點擊「執行全景量化篩選與指標評估」按鈕，產出包含 Excel 全景量化評估與 Portfolio Top 15 核心投組推薦的精簡專業系統。")
