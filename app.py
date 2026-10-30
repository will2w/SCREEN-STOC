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
                          該標的處於 `{row['威科夫微觀結構']}`。結合實時宏觀流動性與財務體質評分優異，主力資金吸籌特徵明確，建議嚴格執行 ATR 停損位 `{row['ATR 停損位']}`。
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
    st.info("👈 請在左側側邊欄點擊「執行全景量化篩選與指標評估」按鈕，產出包含 Portfolio Top 15 核心投組推薦與單一標的配置明細的獨立專頁系統。")
