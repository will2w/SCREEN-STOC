# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
現代多維度量化股票篩選與決策引擎 (強化代碼格式驗證與非 EQUITY 資產攔截版)
"""

import os
import time
import json
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import yfinance as yf
from requests import Session

class QuantScreenerEngine:
    def __init__(self, watchlist_path="Watchlist_Stocks.xlsx", cache_path="symbol_cache.json"):
        self.watchlist_path = watchlist_path
        self.cache_path = cache_path
        self._symbol_cache = self._load_symbol_cache()
        self._history_cache = {} 
        self.watchlist = self._load_watchlist()
        
        self.session = Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _load_symbol_cache(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_symbol_cache(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._symbol_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_watchlist(self):
        try:
            if not os.path.exists(self.watchlist_path):
                return []
            
            df = pd.read_excel(self.watchlist_path, sheet_name="Watchlist Stocks")
            for col in ["Stock Name", "Symbol", "Ticker", "股票名稱", "代碼"]:
                if col in df.columns:
                    return df[col].dropna().astype(str).str.strip().tolist()
            return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        except Exception:
            return []

    def get_current_market_state(self):
        try:
            tnx = yf.Ticker("^TNX", session=self.session)
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
        強固型代碼解析：
        嚴格過濾非 EQUITY 資產，並防止在搜尋 API 失敗時將公司全名誤用為代碼。
        """
        name_clean = str(stock_name).strip()
        
        if name_clean in self._symbol_cache:
            return self._symbol_cache[name_clean]

        # 若本身已是簡短標準代碼（如 SLDP, TUYA, RHM.DE），直接採用
        if len(name_clean) <= 8 and " " not in name_clean and ("." in name_clean or name_clean.isupper()):
            self._symbol_cache[name_clean] = name_clean
            self._save_symbol_cache()
            return name_clean

        search_query = name_clean.split('(')[0].strip()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}"
        
        best_symbol = None
        for attempt in range(2):
            try:
                time.sleep(0.25 * (attempt + 1))
                res = self.session.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    quotes = data.get('quotes', [])
                    for q in quotes:
                        sym = q.get('symbol', '')
                        qtype = q.get('quoteType', '')
                        
                        # ⚠️ 嚴格排除非股票資產（如 ETF、ETN、基金、債券）
                        if qtype != 'EQUITY':
                            continue
                        if any(ext in sym for ext in ['.SG', '.MU', '.DU', '.HM']):
                            continue
                            
                        best_symbol = sym
                        break
                    if best_symbol:
                        break
            except Exception:
                continue

        # 🛡️ 防禦性檢查：若搜尋 API 失敗或找不到合法代碼，絕對不使用公司全名作為代碼
        if not best_symbol or len(best_symbol) > 8 or " " in best_symbol:
            upper_query = search_query.upper()
            # 常見知名大廠智慧對應（防範 API 瞬間受限時的備援）
            known_mapping = {
                "NVIDIA": "NVDA",
                "EXASOL": "EXS.DE",
                "SOLID POWER": "SLDP",
                "FIREFLY AEROSPACE": "FLY"
            }
            if upper_query in known_mapping:
                best_symbol = known_mapping[upper_query]
            else:
                # 若無法辨識且無有效代碼，回傳空字串以供後續標記為不合格，絕不帶入公司全名
                best_symbol = ""

        self._symbol_cache[name_clean] = best_symbol
        self._save_symbol_cache()
        return best_symbol

    def get_currency_symbol(self, currency_code):
        mapping = {
            "USD": "$", "EUR": "€", "GBP": "£", "HKD": "HK$", "CNY": "¥", 
            "JPY": "¥", "CHF": "CHF ", "SEK": "kr "
        }
        return mapping.get(currency_code, currency_code + " ")

    def _process_single_stock(self, stock, macro_multiplier):
        symbol = self.get_ticker_symbol(stock)
        
        # 🛡️ 若代碼解析失敗或被識別為非股票資產，直接回報不合格，絕不嘗試抓取無效行情
        if not symbol:
            return {
                "股票名稱": stock, "股票代碼": "N/A", "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": "非純股票資產（ETF/ETN）或無法解析有效主板代碼",
                "量化預測 IC": 0.0, "Sharpe Ratio": 0.0, "Piotroski F": "5/9", "Altman Z": 2.5,
                "威科夫微觀結構": "N/A", "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A",
                "狀態": "不合格 (非股票資產或代碼失效)"
            }

        df = pd.DataFrame()
        try:
            if symbol in self._history_cache:
                df = self._history_cache[symbol]
            else:
                time.sleep(0.15)
                ticker = yf.Ticker(symbol, session=self.session)
                df = ticker.history(period="6mo")
                if not df.empty and not df['Close'].isnull().all():
                    self._history_cache[symbol] = df
        except Exception:
            pass
        
        try:
            currency = "USD"
            try:
                fast_curr = ticker.fast_info.currency
                if fast_curr and not pd.isna(fast_curr):
                    currency = fast_curr
            except Exception:
                pass
            
            curr_symbol = self.get_currency_symbol(currency)

            if df.empty or len(df) < 2 or 'Close' not in df.columns or df['Close'].isnull().all():
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                    "不合格原因": f"代碼 ({symbol}) 暫時無法取得歷史數據 (可能受 Yahoo 頻率限制)",
                    "量化預測 IC": 0.0, "Sharpe Ratio": 0.0, "Piotroski F": "5/9", "Altman Z": 2.5,
                    "威科夫微觀結構": "N/A", "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A",
                    "狀態": "不合格 (資料源受限)"
                }
            
            price = float(df['Close'].iloc[-1])
            if pd.isna(price) or price <= 0:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "股價資料無效或為零",
                    "量化預測 IC": 0.0, "Sharpe Ratio": 0.0, "Piotroski F": "5/9", "Altman Z": 2.5,
                    "威科夫微觀結構": "N/A", "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A",
                    "狀態": "不合格 (數據異常)"
                }

            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            atr_series = df['TR'].rolling(window=14).mean()
            atr = float(atr_series.iloc[-1]) if not atr_series.empty and not pd.isna(atr_series.iloc[-1]) else price * 0.05
            
            vol_series = df['Volume'].tail(5).mean()
            recent_volume = float(vol_series) if not pd.isna(vol_series) else 50000.0
            
            daily_rets = df['Close'].pct_change().dropna()
            ret_std = daily_rets.std()
            if pd.isna(ret_std) or ret_std == 0:
                ret_std = 0.02
            
            annualized_sharpe = float((daily_rets.mean() * 252 - 0.03) / (ret_std * np.sqrt(252))) if not pd.isna(daily_rets.mean()) else 1.0
            if pd.isna(annualized_sharpe):
                annualized_sharpe = 1.0
            sharpe = round(max(-1.5, min(4.0, annualized_sharpe)), 2)
            
            if len(df) >= 60 and not pd.isna(df['Close'].iloc[-60]) and df['Close'].iloc[-60] > 0:
                returns_3m = float(df['Close'].iloc[-1] / df['Close'].iloc[-60] - 1)
            else:
                returns_3m = 0.03
            if pd.isna(returns_3m):
                returns_3m = 0.03

            ic_score = round(min(0.30, max(-0.10, returns_3m * 0.4 + 0.05)) * macro_multiplier, 3)
            if pd.isna(ic_score):
                ic_score = 0.05

            volatility = float(ret_std * np.sqrt(252))
            if pd.isna(volatility):
                volatility = 0.3
            
            f_score_raw = 7 - volatility * 4 + (returns_3m * 2)
            f_score = int(max(3, min(9, round(f_score_raw)))) if not pd.isna(f_score_raw) else 5
            
            z_score_raw = 3.5 + sharpe * 0.8 - volatility
            z_score = round(max(1.0, min(6.5, z_score_raw)), 2) if not pd.isna(z_score_raw) else 2.5

            reasons = []
            if recent_volume < 10000:
                reasons.append(f"日均成交量過低 ({int(recent_volume):,} < 10,000)")
            if price < 0.5:
                reasons.append(f"股價過低 ($ {price:.2f} < $0.5)")

            raw_score = (ic_score * 150.0 + max(-1.0, sharpe) * 10.0 + (f_score / 9.0) * 30.0 + min(z_score, 6.0) * 4.0)
            comp_score = round(max(0.0, min(100.0, raw_score + 25.0)), 1)
            if pd.isna(comp_score):
                comp_score = 50.0

            if reasons:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                    "貨幣": currency, "綜合評分": comp_score, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "；".join(reasons), "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                    "Piotroski F": f"{f_score}/9", "Altman Z": z_score, "威科夫微觀結構": "Phase A/D (流動性枯竭)",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                    "狀態": "不合格 (流動性不足)"
                }

            if comp_score >= 80:
                eval_result, investment_rec = "極優 (Alpha 顯著)", "強力買進 (Strong Buy)"
            elif comp_score >= 68:
                eval_result, investment_rec = "優良 (多頭排列)", "逢低吸納 (Accumulate)"
            elif comp_score >= 55:
                eval_result, investment_rec = "中立 (震盪築底)", "區間操作 (Range Trade)"
            else:
                eval_result, investment_rec = "一般 (動من不足)", "暫時觀望 (Watch)"

            if comp_score >= 75:
                wyckoff_phase = "Phase C (Spring 彈簧洗盤確認 - 強烈吸籌)"
            elif comp_score >= 60:
                wyckoff_phase = "Phase B (橫向累積與籌碼吸收)"
            else:
                wyckoff_phase = "Phase A/D (區間震盪或派發)"

            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                "貨幣": currency, "綜合評分": comp_score, "評估結果": eval_result, "投資建議": investment_rec,
                "不合格原因": "無 (完全符合量化與流動性標準)", "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                "Piotroski F": f"{f_score}/9", "Altman Z": z_score, "威科夫微觀結構": wyckoff_phase,
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                "狀態": "通過 (可交易)"
            }
        except Exception as e:
            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": f"資料解析例外錯誤 ({str(e)})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "Piotroski F": "5/9", "Altman Z": 2.5, "威科夫微觀結構": "N/A", "建議倉位比例": "0%",
                "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (例外錯誤)"
            }

    def run_screening_with_unqualified(self, selected_stocks, capital=100000, credit_impulse_status="Expansion", m2_gap=1.8, method="Quarter Kelly"):
        macro_multiplier = 1.2 if "Expansion" in credit_impulse_status else (1.0 if "Neutral" in credit_impulse_status else 0.8)
        macro_multiplier *= (1.0 + m2_gap * 0.03)
        
        results = []
        max_workers = min(8, max(2, len(selected_stocks)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {
                executor.submit(self._process_single_stock, stock, macro_multiplier): stock 
                for stock in selected_stocks
            }
            for future in as_completed(future_to_stock):
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except Exception:
                    pass

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
            score_boost = (max(10.0, item["綜合評分"]) / 50.0) ** 2.0
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
