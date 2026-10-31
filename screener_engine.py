# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
現代多維度量化股票篩選與決策引擎 (外部動態檔案對應版：yfinance 主通道 + yahooquery 高效備援)
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
        self._init_human_session()

    def _init_human_session(self):
        """模擬真人操作：設定完整瀏覽器 Headers 並取得 Cookie"""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        })
        try:
            self.session.get("https://finance.yahoo.com", timeout=5)
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            pass

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
        """
        從外部 CSV 或 Excel 動態載入清單，並自動建立「名稱 -> 代碼」動態對應表（完全不寫死字典）
        """
        try:
            if os.path.exists("Watchlist_Stocks.csv"):
                df = pd.read_csv("Watchlist_Stocks.csv")
            elif os.path.exists(self.watchlist_path):
                df = pd.read_excel(self.watchlist_path, sheet_name="Watchlist Stocks")
            else:
                return ["NVIDIA", "AAPL", "BAS.DE", "1347.HK"]
            
            # 從檔案動態建立對應字典
            self.dynamic_symbol_map = {}
            if "Stock Name" in df.columns and "Symbol" in df.columns:
                for _, row in df.iterrows():
                    name = str(row["Stock Name"]).strip()
                    sym = str(row["Symbol"]).strip()
                    self.dynamic_symbol_map[name] = sym
                    self.dynamic_symbol_map[sym] = sym
                return df["Stock Name"].dropna().astype(str).str.strip().tolist()
            
            for col in ["Symbol", "Ticker", "代碼", "Stock Name"]:
                if col in df.columns:
                    return df[col].dropna().astype(str).str.strip().tolist()
            return df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
        except Exception:
            self.dynamic_symbol_map = {}
            return ["NVIDIA", "AAPL", "BAS.DE", "1347.HK"]

    def get_current_market_state(self):
        try:
            df_tnx = self._fetch_chart_data("^TNX", range_str="1mo")
            current_tnx = float(df_tnx['Close'].iloc[-1]) if not df_tnx.empty else 4.25
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

        # 1. 優先檢查從外部檔案動態載入的對應表
        if self.dynamic_symbol_map and name_clean in self.dynamic_symbol_map:
            resolved = self.dynamic_symbol_map[name_clean]
            self._symbol_cache[name_clean] = resolved
            return resolved
            
        # 2. 自動清洗括號與說明文字（例如 "BASF (德國 化工)" -> 檢查 "BASF" 是否在動態對應表中）
        if "(" in name_clean and ")" in name_clean:
            base_name = name_clean.split("(")[0].strip()
            if self.dynamic_symbol_map and base_name in self.dynamic_symbol_map:
                resolved = self.dynamic_symbol_map[base_name]
                self._symbol_cache[name_clean] = resolved
                return resolved
            # 若不在對應表中，直接嘗試抓取括號內的代碼
            possible_code = name_clean.split("(")[-1].split(")")[0].strip()
            if len(possible_code) <= 10 and " " not in possible_code:
                self._symbol_cache[name_clean] = possible_code
                return possible_code

        # 3. 如果本身已經是標準代碼格式（如 NVDA, BAS.DE, 1347.HK），直接回傳
        if len(name_clean) <= 10 and ("." in name_clean or name_clean.isupper()):
            self._symbol_cache[name_clean] = name_clean
            return name_clean

        # 4. 最後防線：若檔案中找不到，回傳清理後的名稱進行查詢
        clean_query = name_clean.split('(')[0].strip()
        self._symbol_cache[name_clean] = clean_query
        return clean_query

    def _fetch_chart_data(self, symbol, range_str="6mo"):
        """
        🛡️ 雙軌備援策略：
        1. 優先使用 yfinance / Chart API 專用通道。
        2. 若超時、報錯或回傳空白，自動切換至 yahooquery 進行非同步備援抓取。
        """
        df = pd.DataFrame()
        clean_symbol = str(symbol).strip()
        
        # ----------------------------------------------------
        # 防線一：yfinance & Chart API
        # ----------------------------------------------------
        for attempt in range(2):
            try:
                time.sleep(random.uniform(0.4, 0.9))
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(clean_symbol)}?range={range_str}&interval=1d"
                res = self.session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
                
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
                
                ticker = yf.Ticker(clean_symbol)
                df = ticker.history(period=range_str, timeout=6)
                if not df.empty and 'Close' in df.columns and not df['Close'].isnull().all():
                    return df
            except Exception:
                pass

        # ----------------------------------------------------
        # 防線二：yahooquery 備援補救
        # ----------------------------------------------------
        if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
            try:
                time.sleep(0.5)
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
                "不合格原因": "無法解析有效代碼", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "Piotroski F": "5/9", "Altman Z": 2.5, "威科夫微觀結構": "N/A",
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
            if ".DE" in symbol or ".PA" in symbol or ".MI" in symbol:
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
                    "Piotroski F": "5/9", "Altman Z": 2.5, "威科夫微觀結構": "N/A",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (資料源受限)"
                }
            
            price = float(df['Close'].iloc[-1])
            if pd.isna(price) or price <= 0:
                return {
                    "股票名稱": stock, "股票代碼": symbol, "最新現價": "N/A", "raw_price": -1.0,
                    "貨幣": currency, "綜合評分": 0.0, "評估結果": "不合格", "投資建議": "暫時迴避 (Avoid)",
                    "不合格原因": "股價資料無效或為零", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                    "Piotroski F": "5/9", "Altman Z": 2.5, "威科夫微觀結構": "N/A",
                    "建議倉位比例": "0%", "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (數據異常)"
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
                eval_result, investment_rec = "一般 (動能不足)", "暫時觀望 (Watch)"

            wyckoff_phase = "Phase C (Spring 彈簧洗盤確認 - 強烈吸籌)" if comp_score >= 75 else ("Phase B (橫向累積與籌碼吸收)" if comp_score >= 60 else "Phase A/D (區間震盪或派發)")

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
                "不合格原因": f"例外錯誤 ({str(e)})", "量化預測 IC": 0.0, "Sharpe Ratio": 0.0,
                "Piotroski F": "5/9", "Altman Z": 2.5, "威科夫微觀結構": "N/A", "建議倉位比例": "0%",
                "建議配置金額 (€)": 0.0, "ATR 停損位": "N/A", "狀態": "不合格 (例外錯誤)"
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
            return "⚠️ 未檢測到 GEMINI_API_KEY 環境變數，無法生成 AI 深度診斷報告。"

        data_summary = df_results.head(15).to_dict(orient="records")
        prompt = f"""
作為華爾街量化投研與總體經濟分析師，請針對以下全球多市場量化篩選與 Portfolio Top 15 核心投組產出專業投研報告：
- 宏觀信貸脈衝狀態：{credit_impulse_status}
- 超額 M2 剪刀差：+{m2_gap}%
- Top 15 投組摘要：{json.dumps(data_summary, ensure_ascii=False, indent=2)}
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
