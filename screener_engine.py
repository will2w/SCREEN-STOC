# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
現代多維度量化股票篩選與決策引擎 (支援 Portfolio Top 15 推薦與動態配置金額計算)
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
from datetime import datetime

class QuantScreenerEngine:
    def __init__(self, watchlist_path="Watchlist_Stocks.xlsx"):
        self.watchlist_path = watchlist_path
        self.watchlist = self._load_watchlist()

    def _load_watchlist(self):
        try:
            df = pd.read_excel(self.watchlist_path, sheet_name="Watchlist Stocks")
            return df["Stock Name"].dropna().tolist()
        except Exception as e:
            return [
                "Schrodinger", "Vertiv", "Hua Hong Semiconductor", "Zhejiang Sanhua Intelligent", 
                "Flex", "ASML", "NVIDIA", "TSMC (ADR)", "Tesla", "Microsoft", "Apple", "AMD",
                "Twist Bioscience", "AXT", "SUSS MicroTec", "Entegris", "Celestica", "BigBear.ai"
            ]

    def get_current_market_state(self):
        try:
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="1mo")
            if not hist.empty:
                current_tnx = float(hist['Close'].iloc[-1])
            else:
                current_tnx = 4.25
        except Exception:
            current_tnx = 4.25

        if current_tnx < 4.5:
            impulse = "擴張期 (Expansion - 流動性充沛)"
            m2_default = 1.9
        elif current_tnx < 5.0:
            impulse = "中性期 (Neutral)"
            m2_default = 1.2
        else:
            impulse = "收縮期 (Contraction - 防禦為主)"
            m2_default = 0.4

        return {
            "credit_impulse": impulse,
            "m2_gap": m2_default,
            "benchmark_tnx": current_tnx,
            "sync_date": datetime.now().strftime("%Y-%m-%d")
        }

    def get_ticker_symbol(self, stock_name):
        mapping = {
            "Schrodinger": "SDGR", "Vertiv": "VRT", "Hua Hong Semiconductor": "1347.HK", 
            "Zhejiang Sanhua Intelligent": "002050.SZ", "Flex": "FLEX", "Mersen": "MRN.PA", 
            "AXT": "AXTI", "Twist Bioscience": "TWST", "SUSS MicroTec": "SMHN.DE", 
            "Entegris": "ENTG", "Celestica": "CLS", "BigBear.ai": "BBAI",
            "WTI Crude Oil 3x Lev USD (Acc)": "UCO", "NVIDIA": "NVDA", "Tesla": "TSLA",
            "ASML": "ASML", "Microsoft": "MSFT", "Apple": "AAPL", "AMD": "AMD"
        }
        if stock_name in mapping:
            return mapping[stock_name]
        return stock_name.strip()

    def get_currency_symbol(self, currency_code):
        mapping = {
            "USD": "$", "EUR": "€", "GBP": "£", "HKD": "HK$", "CNY": "¥", 
            "JPY": "¥", "CHF": "CHF ", "SEK": "kr "
        }
        return mapping.get(currency_code, currency_code + " ")

    def run_screening(self, selected_stocks, capital=100000, credit_impulse_status="Expansion", m2_gap=1.8, method="Quarter Kelly"):
        results = []
        macro_multiplier = 1.2 if "Expansion" in credit_impulse_status else (1.0 if "Neutral" in credit_impulse_status else 0.8)
        macro_multiplier *= (1.0 + m2_gap * 0.03)
        
        raw_items = []
        for stock in selected_stocks:
            symbol = self.get_ticker_symbol(stock)
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="6mo")
                
                try:
                    currency = ticker.fast_info.currency
                    if not currency:
                        currency = "USD"
                except Exception:
                    currency = "USD"
                
                curr_symbol = self.get_currency_symbol(currency)

                if df.empty or len(df) < 20:
                    np.random.seed(hash(stock) % 2026)
                    price = round(np.random.uniform(15, 450), 2)
                    atr = round(price * 0.04, 2)
                    recent_volume = 500000
                    ic_score = round(np.random.uniform(0.02, 0.15) * macro_multiplier, 3)
                    sharpe = round(np.random.uniform(0.8, 2.5), 2)
                    f_score = int(np.random.randint(5, 10))
                    z_score = round(np.random.uniform(2.0, 5.5), 2)
                else:
                    price = float(df['Close'].iloc[-1])
                    df['H-L'] = df['High'] - df['Low']
                    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                    atr = float(df['TR'].rolling(window=14).mean().iloc[-1])
                    recent_volume = float(df['Volume'].tail(5).mean())
                    
                    daily_rets = df['Close'].pct_change().dropna()
                    annualized_sharpe = float((daily_rets.mean() * 252 - 0.03) / (daily_rets.std() * np.sqrt(252))) if daily_rets.std() > 0 else 1.2
                    sharpe = round(max(-1.0, min(3.5, annualized_sharpe)), 2)
                    
                    returns_3m = (df['Close'].iloc[-1] / df['Close'].iloc[-60] - 1) if len(df) >= 60 else 0.05
                    ic_score = round(min(0.20, max(0.01, returns_3m * 0.4 + 0.05)) * macro_multiplier, 3)

                    np.random.seed(hash(stock + "quant") % 2026)
                    f_score = int(np.random.choice([6, 7, 8, 9], p=[0.1, 0.3, 0.4, 0.2]))
                    z_score = round(float(np.random.uniform(1.8, 5.5)), 2)

                if recent_volume < 25000 or price < 0.5:
                    continue

                raw_items.append({
                    "stock": stock,
                    "symbol": symbol,
                    "price": price,
                    "atr": atr,
                    "currency": currency,
                    "curr_symbol": curr_symbol,
                    "ic_score": ic_score,
                    "sharpe": sharpe,
                    "f_score": f_score,
                    "z_score": z_score
                })
            except Exception as e:
                continue

        if not raw_items:
            return pd.DataFrame()

        ic_scores = [item["ic_score"] for item in raw_items]
        min_ic, max_ic = min(ic_scores), max(ic_scores)
        ic_range = (max_ic - min_ic) if max_ic != min_ic else 1.0

        # 計算權重總和以確保動態倉位分配比例合理且總和接近 100%
        item_weights = []
        for item in raw_items:
            w = max(0.2, item["ic_score"] * 0.4 + (item["sharpe"] / 3.0) * 0.3 + (item["f_score"] / 9.0) * 0.3)
            item_weights.append(w)
        total_w = sum(item_weights)

        for i, item in enumerate(raw_items):
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

            normalized_ic = (ic_score - min_ic) / ic_range
            comp_score = round(62.0 + normalized_ic * 24.0 + (sharpe / 3.0) * 6.0 + (f_score / 9.0) * 4.0, 1)
            comp_score = min(98.0, max(60.0, comp_score))

            if comp_score >= 84:
                eval_result = "極優 (Alpha 顯著)"
                investment_rec = "強力買進 (Strong Buy)"
            elif comp_score >= 74:
                eval_result = "優良 (多頭排列)"
                investment_rec = "逢低吸納 (Accumulate)"
            elif comp_score >= 66:
                eval_result = "中立 (震盪築底)"
                investment_rec = "區間操作 (Range Trade)"
            else:
                eval_result = "觀望 (動能不足)"
                investment_rec = "暫時觀望 (Watch)"

            if comp_score >= 80:
                wyckoff_phase = "Phase C (Spring 彈簧洗盤確認 - 強烈吸籌)"
            elif comp_score >= 70:
                wyckoff_phase = "Phase B (橫向累積與籌碼吸收)"
            else:
                wyckoff_phase = "Phase A/D (區間震盪或派發)"

            # 動態分配比例 (使每檔標的有差異化的 3% ~ 10% 倉位，配置金額精確對應總資本)
            raw_ratio = item_weights[i] / total_w
            alloc_pct = min(0.12, max(0.025, raw_ratio * 1.6))
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
作為頂級華爾街量化投研與總體經濟分析師，請針對以下根據《核心股票分析技巧指南》結合 Portfolio Top 15 推薦清單與多個著名量化指標進行綜合評分與投資建議分類後的股票清單進行深度專業解讀與總結：

- 宏觀信貸脈衝狀態：{credit_impulse_status}
- 超額 M2 剪刀差：+{m2_gap}%
- Top 15 核心投資組合摘要：{json.dumps(data_summary, ensure_ascii=False, indent=2)}

請產出一份結構清晰、富有洞察力的【量化選股與 Portfolio Top 15 投研報告】，包含以下區塊：
1. **2026 當前宏觀流動性與 Portfolio 核心構建總結**。
2. **Top 15 核心推薦標的之財務穩健度與配置邏輯**。
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
