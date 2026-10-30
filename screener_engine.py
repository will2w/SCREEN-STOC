def get_ticker_symbol(self, stock_name):
        """
        動態候選測試與成交量最優選擇法 (Trial & Evaluate Best Match)：
        自動搜尋多個候選代碼，實際測試並抓取其成交量，自動挑選流動性最高、最活躍的主板代碼。
        """
        name_clean = str(stock_name).strip()
        
        # 若本身已經是標準大寫代碼，直接返回
        if len(name_clean) <= 6 and name_clean.isupper() and "." not in name_clean:
            return name_clean

        search_query = name_clean.split('(')[0].strip()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        candidates = []
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                quotes = data.get('quotes', [])
                for q in quotes:
                    sym = q.get('symbol', '')
                    qtype = q.get('quoteType', '')
                    if qtype in ['EQUITY', 'ETF']:
                        # 排除明顯的垃圾或德國地方小交易所 (.SG, .MU, .F 等)
                        if any(ext in sym for ext in ['.SG', '.MU', '.F', '.DU', '.HM']):
                            continue
                        candidates.append(sym)
        except Exception:
            pass

        # 如果搜尋不到候選，先嘗試把原名稱直接當作代碼測試
        if not candidates:
            candidates = [search_query]

        # 核心：逐一嘗試抓取數據，選出成交量最大、最活躍的「最佳代碼」！
        best_symbol = candidates[0]
        max_volume = -1.0

        for sym in candidates[:5]:  # 最多測試前 5 個候選
            try:
                test_ticker = yf.Ticker(sym)
                hist = test_ticker.history(period="5d")
                if not hist.empty and 'Volume' in hist.columns:
                    avg_vol = float(hist['Volume'].mean())
                    # 確保有實際成交量且大於當前最優解
                    if not pd.isna(avg_vol) and avg_vol > max_volume:
                        max_volume = avg_vol
                        best_symbol = sym
            except Exception:
                continue

        # 如果測試過後有找到有成交量的代碼就返回它，否則退回第一個候選
        return best_symbol if max_volume > 0 else candidates[0]
