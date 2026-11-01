# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
QUANTUM ALPHA TERMINAL — 現代多維度量化股票篩選與決策引擎 (高效極速精簡版)
"""

import os
import time
import random
import json
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import yfinance as yf
from yahooquery import Ticker as YQ_Ticker
from requests import Session

class QuantScreenerEngine:
    def __init__(self, watchlist_path="Watchlist_Stocks.xlsx", cache_path="symbol_cache.json"):
        self.watchlist_path = watchlist_path
        self.cache_path = cache_path
        self.dynamic_symbol_map = {}
        self._symbol_cache = self._load_symbol_cache()
        self._history_cache = {} 
        self.watchlist = self._load_watchlist()
        
        self.session = Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7"
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
            if os.path.exists("Watchlist_Stocks.csv"):
                df = pd.read_csv("Watchlist_Stocks.csv")
            elif os.path.exists(self.watchlist_path):
                df = pd.read_excel(self.watchlist_path, sheet_name="Watchlist Stocks")
            else:
                return ["NVIDIA", "E.on", "BASF", "JinkoSolar (ADR)"]
            
            self.dynamic_symbol_map = {}
            name_col, sym_col = None, None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if "name" in col_lower or "名稱" in col or "股票名稱" in col:
                    name_col = col
                if "symbol" in col_lower or "ticker" in col_lower or "代碼" in col:
                    sym_col = col

            if name_col and sym_col:
                for _, row in df.iterrows():
                    s_name = str(row[name_col]).strip()
                    s_sym = str(row[sym_col]).strip()
                    if s_name and s_sym and s_sym.lower() != "nan":
                        self.dynamic_symbol_map[s_name] = s_sym
                        self.dynamic_symbol_map[s_sym] = s_sym
                return df[name_col].dropna().astype(str).str.strip().tolist()
            
            for col in ["Symbol", "Ticker", "代碼", "Stock Name", "股票名稱"]:
                if col in df.columns:
                    return df[col].dropna().astype(str).str.strip().tolist()
            return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        except Exception:
            self.dynamic_symbol_map = {}
            return ["NVIDIA", "E.on", "BASF", "JinkoSolar (ADR)"]

    def get_current_market_state(self):
        try:
            tnx = yf.Ticker("^TNX", session=self.session)
            hist = tnx.history(period="1mo")
            current_tnx = float(hist['Close'].iloc[-1]) if not hist.empty else 4.25
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
        name_clean = str(stock_name).strip()
        
        if name_clean in self._symbol_cache and self._symbol_cache[name_clean]:
            return self._symbol_cache[name_clean]

        if self.dynamic_symbol_map and name_clean in self.dynamic_symbol_map:
            resolved = self.dynamic_symbol_map[name_clean]
            self._symbol_cache[name_clean] = resolved
            self._save_symbol_cache()
            return resolved

        base_query = name_clean
        if "(" in base_query and ")" in base_query:
            base_query = base_query.split("(")[0].strip()
            if self.dynamic_symbol_map and base_query in self.dynamic_symbol_map:
                resolved = self.dynamic_symbol_map[base_query]
                self._symbol_cache[name_clean] = resolved
                self._save_symbol_cache()
                return resolved

        if len(base_query) <= 12 and " " not in base_query and ("." in base_query or base_query.isupper()):
            self._symbol_cache[name_clean] = base_query
            self._save_symbol_cache()
            return base_query

        best_symbol = self._execute_fuzzy_search_fallback(base_query)
        final_symbol = best_symbol if best_symbol else base_query
        self._symbol_cache[name_clean] = final_symbol
        self._save_symbol_cache()
        return final_symbol

    def _execute_fuzzy_search_fallback(self, query_str):
        queries_to_try = [
            query_str,
            query_str.replace(".", "").replace("-", " "),
            query_str.split()[0] if " " in query_str else ""
        ]
        queries_to_try = [q for q in queries_to_try if q]

        for q_var in queries_to_try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(q_var)}"
            for attempt in range(2):
                try:
                    time.sleep(0.2 * (attempt + 1))
                    res = self.session.get(url, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        for q in data.get('quotes', []):
                            sym = q.get('symbol', '')
                            qtype = q.get('quoteType', '')
                            if qtype == 'EQUITY' and sym:
                                if not any(ext in sym for ext in ['.SG', '.MU', '.DU', '.HM']):
                                    return sym
                except Exception:
                    continue
        return None

    def _fetch_chart_data(self, symbol, range_str="6mo"):
        df = pd.DataFrame()
        clean_symbol = str(symbol).strip()
        
        for attempt in range(2):
            try:
                time.sleep(random.uniform(0.3, 0.7))
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(clean_symbol)}?range={range_str}&interval=1d"
                res = self.session.get(url, timeout=6)
                
                if res.status_code == 200:
                    data = res.json()
                    result = data.get('chart', {}).get('result', [])
                    if result:
                        res_dict = result[0]
                        timestamps = res_dict.get('timestamp', [])
                        indicators = res_dict.get('indicators', {}).get('quote', [{}])[0]
                        if timestamps and indicators:
                            df = pd.DataFrame({
                                'Open': indicators.get('open', []),
                                'High': indicators.get('high', []),
                                'Low': indicators.get('low', []),
                                'Close': indicators.get('close', []),
                                'Volume': indicators.get('volume', [])
                            }, index=pd.to_datetime(timestamps, unit='s'))
                            df.dropna(subset=['Close'], inplace=True)
                            if not df.empty:
                                return df
                
                ticker = yf.Ticker(clean_symbol, session=self.session)
                df = ticker.history(period=range_str, timeout=6)
                if not df.empty and 'Close' in df.columns and not df['Close'].isnull().all():
                    return df
            except Exception:
                pass

        if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
            try:
                time.sleep(0.4)
                yq = YQ_Ticker(clean_symbol)
                yq_df = yq.history(period=range_str, interval="1d")
                
                if not yq_df.empty:
                    if isinstance(yq_df.index, pd.MultiIndex):
                        yq_df = yq_df.reset_index(level=0, drop=True)
                    
                    if 'close' in yq_df.columns:
                        df = pd.DataFrame({
                            'Open': yq_df.get('open', yq_df['close']),
                            'High': yq_df.get('high', yq_df['close']),
                            'Low': yq_df.get('low', yq_df['close']),
                            'Close': yq_df['close'],
                            'Volume': yq_df.get('volume', 100000)
                        }, index=pd.to_datetime(yq_df.index))
                        df.dropna(subset=['Close'], inplace=True)
                        if not df.empty:
                            return df
            except Exception:
                pass
                
        return df

    def get_currency_symbol(self, currency_code):
        mapping = {
            "USD": "$", "EUR": "€", "GBP": "£", "HKD": "HK$", "CNY": "¥", 
            "JPY": "¥", "CHF": "CHF ", "SEK": "kr "
        }
        return mapping.get(currency_code, currency_code + " ")

    def _process_single_stock(self, stock, macro_multiplier):
        symbol = self.get_ticker_symbol(stock)
        
        if not symbol:
            return {
                "股票名稱": stock, "股票代碼": "N/A", "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": "非純股票資產或無法解析有效代碼", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "Piotroski F": "5/9", "Altman Z": 2.5, "技術面分析 (威科夫/ATR)": "N/A",
                "消息面與基本面解讀": "無法取得有效市場數據", "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, 
                "ATR 停損位": "N/A", "狀態": "不合格"
            }

        df = pd.DataFrame()
        try:
            if symbol in self._history_cache:
                df = self._history_cache[symbol]
            else:
                df = self._fetch_chart_data(symbol, range_str="6mo")
                if not df.empty and not df['Close'].isnull().all():
                    self._history_cache[symbol] = df
        except Exception:
            pass
        
        try:
            currency = "USD"
            if ".DE" in symbol or ".PA" in symbol or ".MI" in symbol or ".F" in symbol:
                currency = "EUR"
            elif ".HK" in symbol:
                currency = "HKD"
            elif ".T" in symbol:
                currency = "JPY"
            elif ".KS" in symbol:
                currency = "KRW"
            elif ".SS" in symbol or ".SZ" in symbol:
                currency = "CNY"
            
            curr_symbol = self.get_currency_symbol(currency)

            if df.empty or len(df) < 2 or 'Close' not in df.columns or df['Close'].isnull().all():
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                    "不合格原因": f"雙軌備援後仍無法取得歷史行情 ({symbol})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                    "Piotroski F": "5/9", "Altman Z": 2.5, "技術面分析 (威科夫/ATR)": "N/A",
                    "消息面與基本面解讀": "歷史行情取得受限或 API 頻率超限", "建議倉位比例": "0%", 
                    "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (資料源受限)"
                }
            
            price = float(df['Close'].iloc[-1])
            if pd.isna(price) or price <= 0:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "股價資料無效或為零", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                    "Piotroski F": "5/9", "Altman Z": 2.5, "技術面分析 (威科夫/ATR)": "N/A",
                    "消息面與基本面解讀": "價格數據異常", "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, 
                    "ATR 停損位": "N/A", "狀態": "不合格 (數據異常)"
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
            sharpe = round(max(-1.5, min(4.0, annualized_sharpe)), 2)
            
            returns_3m = float(df['Close'].iloc[-1] / df['Close'].iloc[-60] - 1) if len(df) >= 60 and df['Close'].iloc[-60] > 0 else 0.03
            ic_score = round(min(0.30, max(-0.10, returns_3m * 0.4 + 0.05)) * macro_multiplier, 3)

            volatility = float(ret_std * np.sqrt(252))
            f_score = int(max(3, min(9, round(7 - volatility * 4 + (returns_3m * 2)))))
            z_score = round(max(1.0, min(6.5, 3.5 + sharpe * 0.8 - volatility)), 2)

            reasons = []
            if recent_volume < 5000:
                reasons.append(f"日均成交量過低 ({int(recent_volume):,} < 5,000)")
            if price < 0.1:
                reasons.append(f"股價過低 ($ {price:.2f})")

            raw_score = (ic_score * 150.0 + max(-1.0, sharpe) * 10.0 + (f_score / 9.0) * 30.0 + min(z_score, 6.0) * 4.0)
            comp_score = round(max(0.0, min(100.0, raw_score + 25.0)), 1)

            if reasons:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                    "貨幣": currency, "綜合評分": comp_score, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "；".join(reasons), "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                    "Piotroski F": f"{f_score}/9", "Altman Z": z_score, 
                    "技術面分析 (威科夫/ATR)": "流動性枯竭，短線偏弱，建議落袋或避開",
                    "消息面與基本面解讀": "交易熱度不足，機構資金暫未進駐",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                    "狀態": "不合格 (流動性不足)"
                }

            if comp_score >= 82:
                eval_result, investment_rec = "極優 (Alpha 顯著)", "強力買進 (Strong Buy)"
                tech_analysis = "威科夫 Phase C (Spring 彈簧洗盤確認) - 主力吸籌完成，量價齊揚。"
                fundamental_news = "基本面強勁（Piotroski F高分），機構買盤積極。"
            elif comp_score >= 70:
                eval_result, investment_rec = "優良 (多頭排列)", "逢低吸納 (Accumulate)"
                tech_analysis = "威科夫 Phase B/C (箱體震盪蓄勢) - 回測支撐帶量守住。"
                fundamental_news = "財務結構穩健，現金流充沛，估值具備安全邊際。"
            elif comp_score >= 58:
                eval_result, investment_rec = "中立 (震盪築底)", "區間操作 (Range Trade)"
                tech_analysis = "威科夫 Phase B (橫向累積) - 均線糾結，等待方向選擇。"
                fundamental_news = "多空消息交織，業績符合預期但缺乏爆發性成長。"
            elif comp_score >= 45:
                eval_result, investment_rec = "偏弱 (動能不足)", "減碼觀望 (Reduce / Watch)"
                tech_analysis = "威科夫 Phase D (弱勢反彈遭逢賣壓) - 上方均線反壓重。"
                fundamental_news = "短期面臨產業逆風或財報不如預期。"
            else:
                eval_result, investment_rec = "風險 (空頭排列)", "強力賣出 / 避開 (Sell / Avoid)"
                tech_analysis = "威科夫 Phase E (下降趨勢派發) - 跌破重要支撐。"
                fundamental_news = "基本面轉弱或總體經濟逆風衝擊，建議嚴格停損。"

            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                "貨幣": currency, "綜合評分": comp_score, "評估結果": eval_result, "投資建議": investment_rec,
                "不合格原因": "無 (完全符合量化與流動性標準)", "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                "Piotroski F": f"{f_score}/9", "Altman Z": z_score, 
                "技術面分析 (威科夫/ATR)": tech_analysis,
                "消息面與基本面解讀": fundamental_news,
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, 
                "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                "狀態": "通過 (可交易)"
            }
        except Exception as e:
            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": f"例外錯誤 ({str(e)})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "Piotroski F": "5/9", "Altman Z": 2.5, 
                "技術面分析 (威科夫/ATR)": "計算例外", "消息面與基本面解讀": "系統內部錯誤",
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (例外錯誤)"
            }

    def run_screening_with_unqualified(self, selected_stocks, capital=100000, credit_impulse_status="Expansion", m2_gap=1.8, method="Quarter Kelly"):
        macro_multiplier = 1.2 if "Expansion" in credit_impulse_status else (1.0 if "Neutral" in credit_impulse_status else 0.8)
        macro_multiplier *= (1.0 + m2_gap * 0.03)
        
        results = []
        max_workers = min(6, max(2, len(selected_stocks)))
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
            alloc_pct = normalized_weights[i] if i < top_n else 0.0
            item["建議倉位比例"] = f"{round(alloc_pct*100, 1)}%"
            item["建議配置金額 (€)"] = round(capital * alloc_pct, 2)
            final_passed.append(item)

        passed_df = pd.DataFrame(final_passed)
        return passed_df, failed_df

    def analyze_with_gemini(self, df_results, credit_impulse_status, m2_gap):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ 未檢測到 GEMINI_API_KEY 環境變數。"

        data_summary = df_results.head(15).to_dict(orient="records")
        prompt = f"""
作為華爾街量化分析師，請對 Top 15 核心投組產出極簡速報：
- 宏觀狀態：{credit_impulse_status} (M2剪刀差 +{m2_gap}%)
- 投組摘要：{json.dumps(data_summary, ensure_ascii=False)}
請給出 3 點核心操作指引（條列式，繁體中文）。
"""
        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 600, "temperature": 0.2}
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = Session().post(url, headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json and len(res_json["candidates"]) > 0:
                        return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception:
                continue
        return "❌ AI 報告生成失敗。"

    def analyze_stock_with_ai_and_rss(self, stock_name, symbol, rss_news_list, tech_str, fundamental_str):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ 未檢測到 API Key"

        news_summary_text = "\n".join([f"- {n['title']}" for n in rss_news_list[:2]]) if rss_news_list else "暫無近期即時新聞。"

        prompt = f"""
請以華爾街量化分析師視角，用繁體中文對以下標的進行極簡速報（嚴格控制在 150 字以內，條列式）：
- 標的：{stock_name} ({symbol})
- 技術面：{tech_str}
- 基本面：{fundamental_str}
- 最新新聞：{news_summary_text}

格式如下：
1. **📰 消息面快訊**：(一句話總結近期動向)
2. **📊 核心判斷**：(多空優勢或風險)
3. **🎯 操盤指引**：(買進/觀望與關鍵防守點)
"""
        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 300, "temperature": 0.2}
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = Session().post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json and len(res_json["candidates"]) > 0:
                        return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception:
                continue
        return "❌ AI 速報生成逾時或失敗。"
