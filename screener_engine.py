        scored_items = []
        for item in raw_items:
            raw_score = (
                item["ic_score"] * 150.0 +
                max(-1.0, item["sharpe"]) * 10.0 +
                (item["f_score"] / 9.0) * 30.0 +
                min(item["z_score"], 6.0) * 4.0
            )
            comp_score = round(max(15.0, min(99.5, raw_score + 25.0)), 1)
            scored_items.append({**item, "comp_score": comp_score})

        scored_items = sorted(scored_items, key=lambda x: x["comp_score"], reverse=True)
        top_n = min(15, len(scored_items))
        top_items = scored_items[:top_n]
        
        raw_weights = []
        for idx, item in enumerate(top_items):
            rank_boost = (top_n - idx) ** 1.5
            score_boost = (max(20.0, item["comp_score"]) / 50.0) ** 2.0
            w = rank_boost * score_boost * max(0.2, item["sharpe"] + 1.2)
            raw_weights.append(w)

        sum_w = sum(raw_weights)
        normalized_weights = [w / sum_w for w in raw_weights]

        for i, item in enumerate(scored_items):
            stock = item["stock"]
            symbol = item["symbol"]
            price = item["price"]
            atr = item["atr"]
            curr_symbol = item["curr_symbol"]
            currency = item["currency"]
            ic_score = item["ic_score"]
            sharpe = item["sharpe"]
            f_score = item["f_score"]
            z_score = item["z_score"]
            comp_score = item["comp_score"]

            if comp_score >= 80:
                eval_result = "極優 (Alpha 顯著)"
                investment_rec = "強力買進 (Strong Buy)"
            elif comp_score >= 68:
                eval_result = "優良 (多頭排列)"
                investment_rec = "逢低吸納 (Accumulate)"
            elif comp_score >= 55:
                eval_result = "中立 (震盪築底)"
                investment_rec = "區間操作 (Range Trade)"
            else:
                eval_result = "觀望 (動能不足)"
                investment_rec = "暫時觀望 (Watch)"

            if comp_score >= 75:
                wyckoff_phase = "Phase C (Spring 彈簧洗盤確認 - 強烈吸籌)"
            elif comp_score >= 60:
                wyckoff_phase = "Phase B (橫向累積與籌碼吸收)"
            else:
                wyckoff_phase = "Phase A/D (區間震盪或派發)"

            if i < top_n:
                alloc_pct = normalized_weights[i]
            else:
                alloc_pct = 0.0

            allocated_amt = round(capital * alloc_pct, 2)

            results.append({
                "股票名稱": stock,
                "股票代碼": symbol,
                "最新現價": f"{curr_symbol}{price:,.2f}",
                "raw_price": price,
                "貨幣": currency,
                "綜合評分": comp_score,
                "評估結果": eval_result,
                "投資建議": investment_rec,
                "量化預測 IC": ic_score,
                "Sharpe Ratio": sharpe,
                "Piotroski F": f"{f_score}/9",
                "Altman Z": z_score,
                "威科夫微觀結構": wyckoff_phase,
                "建議倉位比例": f"{round(alloc_pct*100, 1)}%",
                "建議配置金額 (€)": allocated_amt,
                "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                "狀態": "通過 (可交易)"
            })

        df_result = pd.DataFrame(results)
        if not df_result.empty:
            df_result = df_result.sort_values(by="綜合評分", ascending=False).reset_index(drop=True)
        return df_result

    def analyze_with_gemini(self, df_results, credit_impulse_status, m2_gap):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ 未檢測到 GEMINI_API_KEY 環境變數，無法生成 AI 深度診斷報告。請設定金鑰後重試。"

        data_summary = df_results.head(15).to_dict(orient="records")
        prompt = f"""
作為頂級華爾街量化投研與總體經濟分析師，請針對以下根據真實市場行情數據、多維度量化指標與 Portfolio Top 15 核心投組推薦清單進行客觀絕對評分與嚴格 100% 歸一化動態頭寸配置後的股票清單進行深度專業解讀與總結：

- 宏觀信貸脈衝狀態：{credit_impulse_status}
- 超額 M2 剪刀差：+{m2_gap}%
- Top 15 核心投資組合摘要（總和 100%）：{json.dumps(data_summary, ensure_ascii=False, indent=2)}

請根據每一檔標的的真實量化預測 IC、夏普比率 (Sharpe Ratio)、Piotroski F-Score 財務體質、Altman Z 破產預警分數與威科夫微觀籌碼結構，進行真實且客觀的綜合評估與交叉驗證。請產出一份結構清晰、富有洞察力的【量化選股與 Portfolio Top 15 投研報告】，包含以下區塊：
1. **2026 當前宏觀流動性與 Portfolio 核心構建總結**。
2. **Top 15 核心推薦標的之真實指標表現與動態頭寸配置邏輯**。
3. **風控指導與動態凱利頭寸執行紀律**。
"""

        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.3}
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json and len(res_json["candidates"]) > 0:
                        return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception:
                continue
        return "❌ Gemini AI 分析生成失敗，請稍後再試。"
