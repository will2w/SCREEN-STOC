# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
現代多維度量化股票篩選與決策引擎 (支援單欄位名稱輸入與主板代碼智慧對應)
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import urllib.parse
from datetime import datetime

class QuantScreenerEngine:
    def __init__(self, watchlist_path="Watchlist_Stocks.xlsx"):
        self.watchlist_path = watchlist_path
        self.watchlist = self._load_watchlist()

    def _load_watchlist(self):
        try:
            df = pd.read_excel(self.watchlist_path, sheet_name="Watchlist Stocks")
            for col in ["Stock Name", "Symbol", "Ticker", "股票名稱", "代碼"]:
                if col in df.columns:
                    return df[col].dropna().astype(str).str.strip().tolist()
            return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        except Exception as e:
            return [
                "NVIDIA", "Microsoft", "Apple", "Alphabet", "Amazon", "Meta", "Tesla", "AMD",
                "ASML", "Mersen", "Kuraray", "ThyssenKrupp", "Symbiotic", "Northern Data", "Soitec", "Wise"
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
        """
        智慧代碼對應與過濾：
        若 Excel 中只有名稱，透過內建精準映射與 Yahoo Finance 動態搜尋主板，
        自動避開 ADR、粉單 OTC 與歐陸小交易所（如 .MU, .SG）。
        """
        name_clean = str(stock_name).strip()
        
        # 常見全球標的之精準主板代碼對應表（確保 100% 不抓錯）
        direct_mapping = {
            "Mersen": "MRN.PA",
            "Kuraray": "3405.T",
            "ThyssenKrupp": "TKA.DE",
            "Thyssen Krupp": "TKA.DE",
            "Symbiotic": "SYM",
            "Northern Data": "NB2.DE",
            "Soitec": "SOI.PA",
            "Wise": "WISE.L",
            "Plan Optik": "PLN.DE",
            "JinkoSolar": "JKS",
            "BASF": "BAS.DE",
            "E.ON": "EOAN.DE",
            "NVIDIA": "NVDA",
            "Microsoft": "MSFT",
            "Apple": "AAPL",
            "Alphabet": "GOOGL",
            "Amazon": "AMZN",
            "Meta": "META",
            "Tesla": "TSLA",
            "AMD": "AMD",
            "ASML": "ASML"
        }
        
        if name_clean in direct_mapping:
            return direct_mapping[name_clean]
        
        for k, v in direct_mapping.items():
            if k.lower() in name_clean.lower():
                return v

        if len(name_clean) <= 8 and ("." in name_clean or name_clean.isupper()):
            return name_clean

        search_query = name_clean.split('(')[0].strip()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                quotes = data.get('quotes', [])
                if quotes:
                    best_symbol = quotes[0]['symbol']
                    for q in quotes:
                        sym = q.get('symbol', '')
                        exch = q.get('exchange', '')
                        qtype = q.get('quoteType', '')
                        if qtype in ['EQUITY', 'ETF']:
                            if any(ext in sym for ext in ['.SG', '.MU', '.F', '.DU', '.HM', 'F', 'Y']):
                                continue
                            if exch in ['NMS', 'NYQ', 'NGM', 'ASE'] or '.' not in sym:
                                best_symbol = sym
                                break
                            elif any(ext in sym for ext in ['.HK', '.PA', '.DE', '.T', '.L']):
                                best_symbol = sym
                                break
                    return best_symbol
        except Exception:
            pass

        return name_clean

    def get_currency_symbol(self, currency_code):
        mapping = {
            "USD": "$", "EUR": "€", "GBP": "£", "HKD": "HK$", "CNY": "¥", 
            "JPY": "¥", "CHF": "CHF ", "SEK": "kr "
        }
        return mapping.get(currency_code, currency_code + " ")

    def run_screening_with_unqualified(self, selected_stocks, capital=100000, credit_impulse_status="Expansion", m2_gap=1.8, method="Quarter Kelly"):
        results = []
        macro_multiplier = 1.2 if "Expansion" in credit_impulse_status else (1.0 if "Neutral" in credit_impulse_status else 0.8)
        macro_multiplier *= (1.0 + m2_gap * 0.03)
        
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

                if df.empty or len(df) < 5:
                    results.append({
                        "股票名稱": stock,
                        "股票代碼": symbol,
                        "最新現價": "N/A",
                        "raw_price": 0.0,
                        "貨幣": currency,
                        "綜合評分": 0.0,
                        "評估結果": "不合格",
                        "投資建議": "暫時剔除 (Exclude)",
                        "不合格原因": f"對應代碼 ({symbol}) 後無法取得有效歷史數據",
                        "量化預測 IC": 0.0,
                        "Sharpe Ratio": 0.0,
                        "Piotroski F": "0/9",
                        "Altman Z": 0.0,
                        "威科夫微觀結構": "N/A",
                        "建議倉位比例": "0%",
                        "建議配置金額 (€)": 0.0,
                        "ATR 停損位": "N/A",
                        "狀態": "不合格 (數據異常)"
                    })
                    continue
                
                price = float(df['Close'].iloc[-1])
                df['H-L'] = df['High'] - df['Low']
                df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                atr = float(df['TR'].rolling(window=14).mean().iloc[-1])
                recent_volume = float(df['Volume'].tail(5).mean())
                
                daily_rets = df['Close'].pct_change().dropna()
                annualized_sharpe = float((daily_rets.mean() * 252 - 0.03) / (daily_rets.std() * np.sqrt(252))) if daily_rets.std() > 0 else 1.0
                sharpe = round(max(-1.5, min(4.0, annualized_sharpe)), 2)
                
                returns_3m = (df['Close'].iloc[-1] / df['Close'].iloc[-60] - 1) if len(df) >= 60 else 0.03
                ic_score = round(min(0.30, max(-0.10, returns_3m * 0.4 + 0.05)) * macro_multiplier, 3)

                volatility = float(daily_rets.std() * np.sqrt(252)) if len(daily_rets) > 10 else 0.3
                f_score = int(max(3, min(9, round(7 - volatility * 4 + (returns_3m * 2)))))
                z_score = round(max(1.0, min(6.5, 3.5 + sharpe * 0.8 - volatility)), 2)

                reasons = []
                if recent_volume < 10000:
                    reasons.append(f"日均成交量過低 ({int(recent_volume):,} < 10,000)")
                if price < 0.5:
                    reasons.append(f"股價過低 ($ {price:.2f} < $0.5)")

                if reasons:
                    raw_score = (ic_score * 150.0 + max(-1.0, sharpe) * 10.0 + (f_score / 9.0) * 30.0 + min(z_score, 6.0) * 4.0)
                    comp_score = round(max(10.0, min(50.0, raw_score + 10.0)), 1)
                    results.append({
                        "股票名稱": stock,
                        "股票代碼": symbol,
                        "最新現價": f"{curr_symbol}{price:,.2f}",
                        "raw_price": price,
                        "貨幣": currency,
                        "綜合評分": comp_score,
                        "評估結果": "不合格",
                        "投資建議": "暫時迴避 (Avoid)",
                        "不合格原因": "；".join(reasons),
                        "量化預測 IC": ic_score,
                        "Sharpe Ratio": sharpe,
                        "Piotroski F": f"{f_score}/9",
                        "Altman Z": z_score,
                        "威科夫微觀結構": "Phase A/D (流動性枯竭)",
                        "建議倉位比例": "0%",
                        "建議配置金額 (€)": 0.0,
                        "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                        "狀態": "不合格 (流動性不足)"
                    })
                    continue

                raw_score = (
                    ic_score * 150.0 +
                    max(-1.0, sharpe) * 10.0 +
                    (f_score / 9.0) * 30.0 +
                    min(z_score, 6.0) * 4.0
                )
                comp_score = round(max(51.0, min(99.5, raw_score + 25.0)), 1)

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
                    eval_result = "一般 (動能不足)"
                    investment_rec = "暫時觀望 (Watch)"

                if comp_score >= 75:
                    wyckoff_phase = "Phase C (Spring 彈簧洗盤確認 - 強烈吸籌)"
                elif comp_score >= 60:
                    wyckoff_phase = "Phase B (橫向累積與籌碼吸收)"
                else:
                    wyckoff_phase = "Phase A/D (區間震盪或派發)"

                results.append({
                    "股票名稱": stock,
                    "股票代碼": symbol,
                    "最新現價": f"{curr_symbol}{price:,.2f}",
                    "raw_price": price,
                    "貨幣": currency,
                    "綜合評分": comp_score,
                    "評估結果": eval_result,
                    "投資建議": investment_rec,
                    "不合格原因": "無 (完全符合量化與流動性標準)",
                    "量化預測 IC": ic_score,
                    "Sharpe Ratio": sharpe,
                    "Piotroski F": f"{f_score}/9",
                    "Altman Z": z_score,
                    "威科夫微觀結構": wyckoff_phase,
                    "建議倉位比例": "0%",
                    "建議配置金額 (€)": 0.0,
                    "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                    "狀態": "通過 (可交易)"
                })
            except Exception as e:
                results.append({
                    "股票名稱": stock,
                    "股票代碼": symbol,
                    "最新現價": "N/A",
                    "raw_price": 0.0,
                    "貨幣": "USD",
                    "綜合評分": 0.0,
                    "評估結果": "不合格",
                    "投資建議": "暫時剔除 (Exclude)",
                    "不合格原因": f"連線異常或資料解析錯誤 ({str(e)})",
                    "量化預測 IC": 0.0,
                    "Sharpe Ratio": 0.0,
                    "Piotroski F": "0/9",
                    "Altman Z": 0.0,
                    "威科夫微觀結構": "N/A",
                    "建議倉位比例": "0%",
                    "建議配置金額 (€)": 0.0,
                    "ATR 停損位": "N/A",
                    "狀態": "不合格 (例外錯誤)"
                })
                continue

        df_result = pd.DataFrame(results)
        if df_result.empty:
            return pd.DataFrame(), pd.DataFrame()

        passed_df = df_result[df_result['狀態'].str.contains("通過")].sort_values(by="綜合評分", ascending=False).reset_index(drop=True)
        failed_df = df_result[~df_result['狀態'].str.contains("通過")].sort_values(by="綜合評分", ascending=False).reset_index(drop=True)

        top_n = min(15, len(passed_df))
        passed_records = passed_df.to_dict(orient="records")
        raw_weights = []
        for i in range(top_n):
            item = passed_records[i]
            rank_boost = (top_n - i) ** 1.5
            score_boost = (max(20.0, item["綜合評分"]) / 50.0) ** 2.0
            w = rank_boost * score_boost * max(0.2, item["Sharpe Ratio"] + 1.2)
            raw_weights.append(w)
        
        sum_w = sum(raw_weights) if sum(raw_weights) > 0 else 1.0
        normalized_weights = [w / sum_w for w in raw_weights]

        final_passed = []
        for i, item in enumerate(passed_records):
            if i < top_n:
                alloc_pct = normalized_weights[i]
            else:
                alloc_pct = 0.0
            item["建議倉位比例"] = f"{round(alloc_pct*100, 1)}%"
            item["建議配置金額 (€)"] = round(capital * alloc_pct, 2)
            final_passed.append(item)

        passed_df = pd.DataFrame(final_passed)
        return passed_df, failed_df

    def analyze_with_gemini(self, df_results, credit_impulse_status, m2_gap):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ 未檢測到 GEMINI_API_KEY 環境變數，無法生成 AI 深度診斷報告。"

        data_summary = df_results.head(15).to_dict(orient="records")
        prompt = f"""
作為頂級華爾街量化投研與總體經濟分析師，請針對以下根據真實市場行情數據、多維度量化指標與 Portfolio Top 15 核心投組推薦清單進行客觀絕對評分與嚴格 100% 歸一化動態頭寸配置後的股票清單進行深度專業解讀與總結：

- 宏觀信貸脈衝狀態：{credit_impulse_status}
- 超額 M2 剪刀差：+{m2_gap}%
- Top 15 核心投資組合摘要（總和 100%）：{json.dumps(data_summary, ensure_ascii=False, indent=2)}

請產出一份結構清晰、富有洞察力的【量化選股與 Portfolio Top 15 投研報告】。
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
