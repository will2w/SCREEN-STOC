def get_ticker_symbol(self, stock_name):
        name_clean = str(stock_name).strip()
        
        # 1. 若快取中存在且為有效代碼，直接返回
        if name_clean in self._symbol_cache and self._symbol_cache[name_clean]:
            return self._symbol_cache[name_clean]

        if len(name_clean) <= 8 and " " not in name_clean and ("." in name_clean or name_clean.isupper()):
            return name_clean

        search_query = name_clean.split('(')[0].strip()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}"
        
        best_symbol = None
        is_rate_limited = False

        for attempt in range(2):
            try:
                time.sleep(0.3 * (attempt + 1))
                res = self.session.get(url, timeout=5)
                
                # 🔍 明確檢查是否觸發 429 頻率限制
                if res.status_code == 429:
                    is_rate_limited = True
                    time.sleep(1.5) # 遇 429 進行冷卻等待
                    continue
                
                if res.status_code == 200:
                    data = res.json()
                    quotes = data.get('quotes', [])
                    for q in quotes:
                        sym = q.get('symbol', '')
                        qtype = q.get('quoteType', '')
                        
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

        # 針對歐洲大廠（如 BASF, E.ON 等）若搜尋受阻時的智慧後綴補償
        if not best_symbol or len(best_symbol) > 10 or " " in best_symbol:
            upper_query = search_query.upper()
            european_fallbacks = {
                "BASF": "BAS.DE",
                "E.ON": "EOAN.DE",
                "CECONOMY": "CEC.DE",
                "IVECO": "IVG.MI"
            }
            if upper_query in european_fallbacks:
                best_symbol = european_fallbacks[upper_query]
            else:
                best_symbol = ""

        # ⚠️ 關鍵防護：只有當成功取得合法代碼時才寫入快取！若因頻率受限或失敗則不快取，確保下次重試
        if best_symbol and not is_rate_limited:
            self._symbol_cache[name_clean] = best_symbol
            self._save_symbol_cache()
            
        return best_symbol
