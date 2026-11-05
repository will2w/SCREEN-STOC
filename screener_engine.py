# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
QUANTUM ALPHA TERMINAL — 全量真實計量、動態技術面數據、消息面分數與 Gemini 智慧融合篩選引擎
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
import feedparser

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

    def _fetch_live_news_summary(self, stock_query):
        try:
            clean_q = str(stock_query).split(".")[0].strip()
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_q + ' stock')}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(rss_url)
            titles = [entry.get('title', '') for entry in feed.entries[:3]]
            if titles:
                return " | ".join(titles)
            return "近期無重大突發財經頭條。"
        except Exception:
            return "消息面平穩。"

    def _calculate_real_fundamental_scores(self, ticker_obj, price):
        try:
            fin = ticker_obj.financials
            bs = ticker_obj.balance_sheet
            cf = ticker_obj.cashflow
            
            if fin is None or bs is None or fin.empty or bs.empty:
                return 5, 2.5
                
            def get_row(df, possible_names):
                for name in possible_names:
                    if df is not None and not df.empty and name in df.index:
                        return df.loc[name]
                return None

            net_income_row = get_row(fin, ['Net Income', 'Net Income Common Stockholders'])
            oc_row = get_row(cf, ['Operating Cash Flow', 'Operating Cashflows', 'Cash Flow from Continuing Operating Activities']) if cf is not None else None
            total_assets_row = get_row(bs, ['Total Assets'])
            total_liab_row = get_row(bs, ['Total Liabilities Net Minority Interest', 'Total Debt', 'Total Liabilities'])
            retained_row = get_row(bs, ['Retained Earnings'])
            working_cap_row = get_row(bs, ['Working Capital'])
            ebit_row = get_row(fin, ['EBIT', 'Operating Income', 'Operating Income Loss'])
            revenue_row = get_row(fin, ['Total Revenue', 'Operating Revenue'])
            
            total_assets = total_assets_row.iloc[0] if total_assets_row is not None and len(total_assets_row) > 0 else 1.0
            prev_assets = total_assets_row.iloc[1] if total_assets_row is not None and len(total_assets_row) > 1 else total_assets

            f_pts = 5
            if net_income_row is not None and len(net_income_row) > 0 and net_income_row.iloc[0] > 0:
                f_pts += 1
            if oc_row is not None and len(oc_row) > 0 and oc_row.iloc[0] > 0:
                f_pts += 1
            if net_income_row is not None and len(net_income_row) > 1:
                curr_roa = net_income_row.iloc[0] / total_assets
                prev_roa = net_income_row.iloc[1] / prev_assets
                if curr_roa > prev_roa:
                    f_pts += 1
            if oc_row is not None and net_income_row is not None and len(oc_row) > 0 and len(net_income_row) > 0:
                if oc_row.iloc[0] > net_income_row.iloc[0]:
                    f_pts += 1
            f_score = int(max(2, min(9, f_pts)))

            wc = working_cap_row.iloc[0] if working_cap_row is not None and len(working_cap_row) > 0 else total_assets * 0.25
            re = retained_row.iloc[0] if retained_row is not None and len(retained_row) > 0 else total_assets * 0.3
            ebit = ebit_row.iloc[0] if ebit_row is not None and len(ebit_row) > 0 else total_assets * 0.1
            tot_liab = total_liab_row.iloc[0] if total_liab_row is not None and len(total_liab_row) > 0 else total_assets * 0.5
            rev = revenue_row.iloc[0] if revenue_row is not None and len(revenue_row) > 0 else total_assets * 0.8
            
            shares = 1000000000
            try:
                if hasattr(ticker_obj, 'info'):
                    shares = ticker_obj.info.get('sharesOutstanding', 1000000000)
            except Exception:
                pass
            mve = price * shares if shares else total_assets * 1.0

            X1 = wc / total_assets
            X2 = re / total_assets
            X3 = ebit / total_assets
            X4 = mve / tot_liab if tot_liab > 0 else 1.0
            X5 = rev / total_assets

            z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3 + 0.6 * X4 + 0.999 * X5
            z_score = round(max(0.5, min(9.0, float(z))), 2)
            
            return f_score, z_score
        except Exception:
            return 5, 2.5

    def _calculate_technical_indicators(self, df):
        """⚡ 動態計算技術指標（RSI, SMA20/50, ATR 與威科夫結構）"""
        try:
            close = df['Close']
            high = df['High']
            low = df['Low']
            volume = df['Volume']

            sma20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else float(close.mean())
            sma50 = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else sma20
            curr_price = float(close.iloc[-1])

            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 0.001)
            rsi14 = float((100 - (100 / (1 + rs))).iloc[-1]) if not rs.empty else 50.0

            df['H-L'] = high - low
            df['H-PC'] = abs(high - close.shift(1))
            df['L-PC'] = abs(low - close.shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            atr14 = float(df['TR'].rolling(window=14).mean().iloc[-1]) if not df['TR'].empty else curr_price * 0.05

            vol_mean = volume.tail(20).mean()
            curr_vol = float(volume.iloc[-1])
            is_vol_surge = curr_vol > (vol_mean * 1.5)

            if curr_price > sma20 and sma20 > sma50:
                wyckoff_phase = f"Phase D/E 主升強勢 (RSI:{rsi14:.1f})"
            elif curr_price < sma20 and sma20 < sma50:
                wyckoff_phase = f"Phase E 下降派發 (RSI:{rsi14:.1f})"
            else:
                if is_vol_surge and curr_price <= low.tail(20).min() * 1.03:
                    wyckoff_phase = f"Phase C Spring 洗盤 (量增)"
                else:
                    wyckoff_phase = f"Phase B 箱體蓄勢 (RSI:{rsi14:.1f})"

            return wyckoff_phase, atr14, rsi14, sma20, sma50
        except Exception:
            return "Phase B 震盪蓄勢", float(df['Close'].iloc[-1] * 0.05), 50.0, float(df['Close'].iloc[-1]), float(df['Close'].iloc[-1])

    def _call_gemini_for_screening_evaluation(self, stock_name, symbol, ic, sharpe, f_score, altman_z, tech_str, news_text):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return 0.0, 5.0, "消息面平穩"

        prompt = f"""
作為華爾街量化資深操盤手，請評估以下股票：
- 股票：{stock_name} ({symbol})
- 量化預測 IC: {ic} | 夏普比率: {sharpe}
- 技術結構: {tech_str}
- 即時新聞頭條：{news_text}

請嚴格回傳一個 JSON 物件，包含三個欄位：
1. "sentiment_bonus": 數字，範圍 -3.0 到 +4.0（情感加權分）。
2. "news_score": 數字，範圍 0 到 10（即消息面綜合評分，10分為極佳利多）。
3. "ai_summary": 字串，限 30 字以內的精煉中文評語。
回傳格式範例: {{"sentiment_bonus": 2.0, "news_score": 8.5, "ai_summary": "財報亮眼且威科夫結構強勢。"}}
"""
        models = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 200, "temperature": 0.2, "responseMimeType": "application/json"}
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = Session().post(url, headers=headers, json=payload, timeout=12)
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json and len(res_json["candidates"]) > 0:
                        text_res = res_json['candidates'][0]['content']['parts'][0]['text']
                        parsed = json.loads(text_res)
                        return float(parsed.get("sentiment_bonus", 0.0)), float(parsed.get("news_score", 5.0)), str(parsed.get("ai_summary", "消息面平穩"))
            except Exception:
                continue
        return 0.0, 5.0, "消息面平穩"

    def _process_single_stock(self, stock, macro_multiplier):
        symbol = self.get_ticker_symbol(stock)
        if not symbol:
            return {
                "股票名稱": stock, "股票代碼": "N/A", "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "上一版純量化分": 0.0, "分數變化 (Δ)": "+0.0", "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": "非純股票資產或無法解析有效代碼", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "技術面數據": "N/A", "消息面分數": "N/A",
                "技術面分析 (威科夫/ATR)": "N/A", "消息面與基本面解讀": "無法取得有效市場數據",
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格"
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
                    "貨幣": currency, "綜合評分": 0.0, "上一版純量化分": 0.0, "分數變化 (Δ)": "+0.0", "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                    "不合格原因": f"雙軌備援後仍無法取得歷史行情 ({symbol})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                    "技術面數據": "N/A", "消息面分數": "N/A",
                    "技術面分析 (威科夫/ATR)": "N/A", "消息面與基本面解讀": "歷史行情取得受限",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (資料源受限)"
                }
            
            price = float(df['Close'].iloc[-1])
            if pd.isna(price) or price <= 0:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "上一版純量化分": 0.0, "分數變化 (Δ)": "+0.0", "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "股價資料無效或為零", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                    "技術面數據": "N/A", "消息面分數": "N/A",
                    "技術面分析 (威科夫/ATR)": "N/A", "消息面與基本面解讀": "價格數據異常",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (數據異常)"
                }

            wyckoff_str, atr, rsi_val, sma20, sma50 = self._calculate_technical_indicators(df)
            live_news_text = self._fetch_live_news_summary(stock)

            yf_ticker_obj = yf.Ticker(symbol, session=self.session)
            f_raw, z_raw = self._calculate_real_fundamental_scores(yf_ticker_obj, price)
            
            vol_series = df['Volume'].tail(5).mean()
            recent_volume = float(vol_series) if not pd.isna(vol_series) else 50000.0
            
            daily_rets = df['Close'].pct_change().dropna()
            ret_std = daily_rets.std()
            if pd.isna(ret_std) or ret_std == 0:
                ret_std = 0.02
            
            risk_free_rate = 0.0425
            annualized_sharpe = float((daily_rets.mean() * 252 - risk_free_rate) / (ret_std * np.sqrt(252))) if not pd.isna(daily_rets.mean()) else 1.0
            sharpe = round(max(-2.0, min(5.0, annualized_sharpe)), 2)
            
            returns_3m = float(df['Close'].iloc[-1] / df['Close'].iloc[-60] - 1) if len(df) >= 60 and df['Close'].iloc[-60] > 0 else 0.03
            ic_score = round(min(0.35, max(-0.15, returns_3m * 0.45 + 0.03)) * macro_multiplier, 3)

            base_raw_score = (ic_score * 140.0 + max(-1.0, sharpe) * 12.0 + (f_raw / 9.0) * 30.0 + min(z_raw, 6.0) * 4.0)
            base_score = round(max(0.0, min(100.0, base_raw_score + 25.0)), 1)

            sentiment_bonus, news_score_val, ai_screening_summary = self._call_gemini_for_screening_evaluation(
                stock_name=stock, symbol=symbol, ic=ic_score, sharpe=sharpe, f_score=f_raw, altman_z=z_raw, tech_str=wyckoff_str, news_text=live_news_text
            )

            final_raw_score = base_raw_score + sentiment_bonus * 3.5
            comp_score = round(max(0.0, min(100.0, final_raw_score + 25.0)), 1)

            score_diff = round(comp_score - base_score, 1)
            diff_str = f"+{score_diff}" if score_diff >= 0 else f"{score_diff}"

            technical_data_str = f"RSI:{rsi14:.1f} | 結構:{wyckoff_str.split()[0]}"
            news_score_str = f"{news_score_val:.1f} / 10"

            reasons = []
            if recent_volume < 5000:
                reasons.append(f"日均成交量過低 ({int(recent_volume):,} < 5,000)")
            if price < 0.1:
                reasons.append(f"股價過低 ($ {price:.2f})")

            if reasons:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                    "貨幣": currency, "綜合評分": comp_score, "上一版純量化分": base_score, "分數變化 (Δ)": diff_str, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "；".join(reasons), "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                    "技術面數據": technical_data_str, "消息面分數": news_score_str,
                    "技術面分析 (威科夫/ATR)": wyckoff_str, "消息面與基本面解讀": ai_screening_summary,
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                    "狀態": "不合格 (流動性不足)"
                }

            if comp_score >= 82:
                eval_result, investment_rec = "極優 (Alpha 顯著)", "強力買進 (Strong Buy)"
            elif comp_score >= 70:
                eval_result, investment_rec = "優良 (多頭排列)", "逢低吸納 (Accumulate)"
            elif comp_score >= 58:
                eval_result, investment_rec = "中立 (震盪築底)", "區間操作 (Range Trade)"
            elif comp_score >= 45:
                eval_result, investment_rec = "偏弱 (動能不足)", "減碼觀望 (Reduce / Watch)"
            else:
                eval_result, investment_rec = "風險 (空頭排列)", "強力賣出 / 避開 (Sell / Avoid)"

            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": f"{curr_symbol}{price:,.2f}", "raw_price": price,
                "貨幣": currency, "綜合評分": comp_score, "上一版純量化分": base_score, "分數變化 (Δ)": diff_str, "評估結果": eval_result, "投資建議": investment_rec,
                "不合格原因": "無 (完全符合量化與流動性標準)", "量化預測 IC": ic_score, "Sharpe Ratio": sharpe,
                "技術面數據": technical_data_str, "消息面分數": news_score_str,
                "技術面分析 (威科夫/ATR)": wyckoff_str, "消息面與基本面解讀": ai_screening_summary,
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, 
                "ATR 停損位": f"{curr_symbol}{max(0, price - 2 * atr):,.2f}",
                "狀態": "通過 (可交易)"
            }
        except Exception as e:
            return {
                "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                "貨幣": "USD", "綜合評分": 0.0, "上一版純量化分": 0.0, "分數變化 (Δ)": "+0.0", "評估結果": "不合格", "投資建議": "暫時剔除 (Exclude)",
                "不合格原因": f"例外錯誤 ({str(e)})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "技術面數據": "N/A", "消息面分數": "N/A",
                "技術面分析 (威科夫/ATR)": "計算例外", "消息面與基本面解讀": "系統內部錯誤",
                "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (例外錯誤)"
            }

    def run_screening_with_unqualified(self, selected_stocks, capital=100000, credit_impulse_status="Expansion", m2_gap=1.8, method="Quarter Kelly"):
        macro_multiplier = 1.2 if "Expansion" in credit_impulse_status else (1.0 if "Neutral" in credit_impulse_status else 0.8)
        macro_multiplier *= (1.0 + m2_gap * 0.03)
        
        results = []
        max_workers = min(4, max(2, len(selected_stocks)))
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

    def get_dual_track_top10(self, df_passed, capital=100000):
        if df_passed.empty:
            return pd.DataFrame(), pd.DataFrame()

        df_short = df_passed.copy()
        if '量化預測 IC' in df_short.columns and 'Sharpe Ratio' in df_short.columns:
            df_short['short_score'] = df_short['量化預測 IC'] * 50 + df_short['綜合評分'] * 0.5 + df_short['Sharpe Ratio'] * 10
            df_short = df_short.sort_values(by='short_score', ascending=False)
        
        top10_short = df_short.head(10).reset_index(drop=True)
        short_results = []
        for idx, row in top10_short.iterrows():
            raw_p = row['raw_price'] if row['raw_price'] > 0 else 100.0
            curr_sym = row['最新現價'][:1] if len(str(row['最新現價'])) > 0 else "$"
            
            buy_price = round(raw_p * 0.985, 2)
            take_profit = round(raw_p * 1.06, 2)
            stop_loss = row['ATR 停損位']
            alloc_pct = f"{round(max(2.0, 12.0 - idx * 0.8), 1)}%"
            alloc_amt = round(capital * (float(alloc_pct.replace('%','')) / 100.0), 2)
            ai_reason = row.get('消息面與基本面解讀', f"動能強勢(IC:{row['量化預測 IC']})，技術面多頭排列。")

            short_results.append({
                "排名": f"#{idx+1}",
                "股票名稱": row['股票名稱'],
                "股票代碼": row['股票代碼'],
                "最新現價": row['最新現價'],
                "建議買入價": f"{curr_sym}{buy_price:,.2f}",
                "短線停利價": f"{curr_sym}{take_profit:,.2f}",
                "ATR 停損價": stop_loss,
                "建議倉位": alloc_pct,
                "配置金額 (€)": alloc_amt,
                "一句話推薦原因": ai_reason
            })

        df_long = df_passed.copy()
        top10_long = df_long.head(10).reset_index(drop=True)
        long_results = []
        for idx, row in top10_long.iterrows():
            raw_p = row['raw_price'] if row['raw_price'] > 0 else 100.0
            curr_sym = row['最新現價'][:1] if len(str(row['最新現價'])) > 0 else "$"
            
            accum_price = round(raw_p * 0.95, 2)
            target_price = round(raw_p * 1.25, 2)
            alloc_pct = f"{round(max(4.0, 15.0 - idx * 1.0), 1)}%"
            alloc_amt = round(capital * (float(alloc_pct.replace('%','')) / 100.0), 2)
            ai_reason = row.get('消息面與基本面解讀', f"技術面穩健(消息面分:{row['消息面分數']})，中長線佈局。")

            long_results.append({
                "排名": f"#{idx+1}",
                "股票名稱": row['股票名稱'],
                "股票代碼": row['股票代碼'],
                "最新現價": row['最新現價'],
                "逢低佈局價": f"{curr_sym}{accum_price:,.2f}",
                "中長線目標價": f"{curr_sym}{target_price:,.2f}",
                "技術面數據": row['技術面數據'],
                "建議倉位": alloc_pct,
                "配置金額 (€)": alloc_amt,
                "一句話推薦原因": ai_reason
            })

        return pd.DataFrame(short_results), pd.DataFrame(long_results)

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
        models = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
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

        news_summary_text = "\n".join([f"- {n['title']}" for n in rss_news_list[:3]]) if rss_news_list else "暫無近期即時新聞。"

        prompt = f"""
以華爾街量化資深操盤手視角，用繁體中文給出結構豐富、兼具新聞總結與趨勢預測的深度戰情速報：
- 標的：{stock_name} ({symbol})
- 技術與威科夫結構：{tech_str}
- 基本面與財務狀況：{fundamental_str}
- 最新財經新聞清單：
{news_summary_text}

請嚴格按照以下四個模組輸出詳盡的專業分析：
1. **📰 最近新聞總結與事件驅動**：摘要近期關鍵新聞焦點與市場資金反應。
2. **🔮 趨勢預測與短中線展望**：結合新聞面與量化指標預判走勢。
3. **📊 量化基本面與技術面評判**：評估財務健康度與威科夫微觀結構。
4. **🎯 具體操盤指引與風控規劃**：給出明確建倉區間、ATR 停損與目標價。
"""
        models = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1500, "temperature": 0.25}
        }

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = Session().post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json and len(res_json["candidates"]) > 0:
                        return res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception:
                continue
        return "❌ AI 深度解讀生成逾時或失敗。"
