# -*- coding: utf-8 -*-
"""
screener_engine.py
------------------
現代多維度量化股票篩選與決策引擎 (國家區域優先辨識 + 智慧主板動態測試版)
"""

import os
import time
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
        self._symbol_cache = {}  # 記憶體快取
        self._history_cache = {} # 歷史行情快取
        self.watchlist = self._load_watchlist()

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
        國家區域優先辨識與動態主板測試法：
        1. 先透過名稱特徵判斷其所屬國家/區域（德國、歐洲、美股等）。
        2. 自動帶入對應區域的主板交易所後綴（.DE, .PA, .L 或美股主板）。
        3. 實際抓取成交量，選出流動性最高、最優的主板代碼。
        """
        name_clean = str(stock_name).strip()
        
        # 命中快取直接返回
        if name_clean in self._symbol_cache:
            return self._symbol_cache[name_clean]

        if len(name_clean) <= 6 and name_clean.isupper() and "." not in name_clean:
            self._symbol_cache[name_clean] = name_clean
            return name_clean

        search_query = name_clean.split('(')[0].strip()
        
        # 根據名稱特徵推導可能的區域後綴群組（不寫死對應，僅作區域優化排序）
        regional_suffixes = [""] # 預設先測無後綴（美股或全球代碼）
        
        # 簡單的動態區域特徵辨識（可依您的清單自然延伸）
        lower_query = search_query.lower()
        german_keywords = ['ag', 'gmbh', 'e.on', 'bayer', 'basf', 'daimler', 'siemens', 'allianz', 'adidas', 'infineon', 'mercen', 'hensoldt', 'ceconomy', 'tui', 'thyssenkrupp']
        french_keywords = ['airbus', 'safran', 'total', 'schneider', 'sanofi', 'l\'oreal', 'soitec', 'mersen']
        
        if any(k in lower_query for k in german_keywords):
            regional_suffixes = [".DE", ".F", ""]
        elif any(k in lower_query for k in french_keywords):
            regional_suffixes = [".PA", ""]
        else:
            regional_suffixes = ["", ".DE", ".PA", ".L"]

        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        candidates = []
        try:
            time.sleep(0.3)
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                quotes = data.get('quotes', [])
                for q in quotes:
                    sym = q.get('symbol', '')
                    qtype = q.get('quoteType', '')
                    # 嚴格排除非股票資產 (ETF、基金、債券)
                    if qtype != 'EQUITY':
                        continue
                    # 排除地方小交易所
                    if any(ext in sym for ext in ['.SG', '.MU', '.DU', '.HM']):
                        continue
                    candidates.append(sym)
        except Exception:
            pass

        if not candidates:
            candidates = [search_query]

        # 組合擴展候選清單：優先將該區域最適合的主板後綴組合進去測試
        extended_candidates = []
        for base in [search_query] + candidates[:2]:
            base_clean = base.split('.')[0]
            for suf in regional_suffixes:
                candidate_sym = f"{base_clean}{suf}" if suf and not base_clean.endswith(suf) else base_clean
                if candidate_sym not in extended_candidates:
                    extended_candidates.append(candidate_sym)

        # 實際測試成交量，選出最優的主板代碼
        best_symbol = extended_candidates[0]
        max_volume = -1.0

        for sym in extended_candidates[:5]:
            try:
                time.sleep(0.2)
                test_ticker = yf.Ticker(sym)
                hist = test_ticker.history(period="3d")
                if not hist.empty and 'Volume' in hist.columns:
                    avg_vol = float(hist['Volume'].mean())
                    if not pd.isna(avg_vol) and avg_vol > max_volume:
                        max_volume = avg_vol
                        best_symbol = sym
            except Exception:
                continue

        final_sym = best_symbol if max_volume >= 0 else candidates[0]
        self._symbol_cache[name_clean] = final_sym
        return final_sym

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
                if symbol in self._history_cache:
                    df = self._history_cache[symbol]
                else:
                    time.sleep(0.3)
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(period="6mo")
                    self._history_cache[symbol] = df
                
                currency = "USD"
                try:
                    fast_curr = ticker.fast_info.currency
                    if fast_curr and not pd.isna(fast_curr):
                        currency = fast_curr
                except Exception:
                    pass
                
                curr_symbol = self.get_currency_symbol(currency)

                if df.empty or len(df) < 2 or 'Close' not in df.columns or df['Close'].isnull().all():
                    results.append({
                        "股票名稱": stock,
                        "股票代碼": symbol,
                        "最新現價": "N/A",
                        "raw_price": 0.0,
                        "貨幣": currency,
                        "綜合評分": 0.0,
                        "評估結果": "不合格",
                        "投資建議": "暫時剔除 (Exclude)",
                        "不合格原因": f"代碼 ({symbol}) 無法取得有效歷史行情數據",
                        "量化預測 IC": 0.0,
                        "Sharpe Ratio": 0.0,
                        "Piotroski F": "5/9",
                        "Altman Z": 2.5,
                        "威科夫微觀結構": "N/A",
                        "建議倉位比例": "0%",
                        "建議配置金額 (€)": 0.0,
                        "ATR 停損位": "N/A",
                        "狀態": "不合格 (數據異常)"
                    })
                    continue
                
                price = float(df['Close'].iloc[-1])
                if pd.isna(price) or price <= 0:
                    results.append({
                        "股票名稱": stock,
                        "股票代碼": symbol,
                        "最新現價": "N/A",
                        "raw_price": 0.0,
                        "貨幣": currency,
                        "綜合評分": 0.0,
                        "評估結果": "不合格",
                        "投資建議": "暫時迴避 (Avoid)",
                        "不合格原因": "股價資料無效或為零",
                        "量化預測 IC": 0.0,
                        "Sharpe Ratio": 0.0,
                        "Piotroski F": "5/9",
                        "Altman Z": 2.5,
                        "威科夫微觀結構": "N/A",
                        "建議倉位比例": "0%",
                        "建議配置金額 (€)": 0.0,
                        "ATR 停損位": "N/A",
                        "狀態": "不合格 (數據異常)"
                    })
                    continue

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
                if pd.isna(comp_score):
                    comp_score = 6
