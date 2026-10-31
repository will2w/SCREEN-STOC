if run_btn:
    if not watchlist:
        st.error("無法執行篩選：觀察清單為空。")
    else:
        # 🚀 新增：建立視覺化進度條與狀態文字
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 正在初始化模擬真人 Session 與宏觀市場狀態...")
        progress_bar.progress(15)
        
        # 執行原本的量化篩選引擎
        passed_df, failed_df = engine.run_screening_with_unqualified(
            watchlist, 
            capital=capital, 
            credit_impulse_status=market_state['credit_impulse'], 
            m2_gap=market_state['m2_gap']
        )
        
        status_text.text("📊 正在計算 IC 分數、Sharpe 比例與 100% 動態頭寸配置...")
        progress_bar.progress(70)
        
        # 暫存至 session_state
        st.session_state['passed_df'] = passed_df
        st.session_state['failed_df'] = failed_df
        st.session_state['market_state'] = market_state
        st.session_state['capital'] = capital
        
        progress_bar.progress(100)
        status_text.text("✨ 量化篩選與投組建構完成！")
        
        # 稍作停留後清除進度條
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        # 重新整理畫面顯示結果
        st.rerun()
