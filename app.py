import http.server
import json
import os
import socketserver
import threading
import urllib.request

PORT = int(os.environ.get("PORT", 8080))

# 快取 BingX 數據的字典
bingx_cache = {"tickers": [], "premium": []}


def fetch_bingx_background():
  import time
  while True:
    try:
      # 1. 抓取 BingX 合約 Ticker (24h 行情)
      req_ticker = urllib.request.Request(
          "https://open-api.bingx.com/openApi/swap/v2/quote/ticker",
          headers={"User-Agent": "Mozilla/5.0"},
      )
      with urllib.request.urlopen(req_ticker, timeout=5) as res:
        ticker_data = json.loads(res.read().decode("utf-8"))

      # 2. 抓取 BingX 資金費率
      req_prem = urllib.request.Request(
          "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex",
          headers={"User-Agent": "Mozilla/5.0"},
      )
      with urllib.request.urlopen(req_prem, timeout=5) as res:
        prem_data = json.loads(res.read().decode("utf-8"))

      if ticker_data.get("code") == 0:
        bingx_cache["tickers"] = ticker_data.get("data", [])
      if prem_data.get("code") == 0:
        bingx_cache["premium"] = prem_data.get("data", [])
    except Exception as e:
      print("背景抓取 BingX 失敗:", e)

    time.sleep(10)  # 每 10 秒背景更新一次


html_content = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BingX 飆漲幣精準追蹤系統</title>
    <style>
        :root {
            --bg: #0b0e11;
            --card-bg: #161a1e;
            --card-border: #23272e;
            --text-main: #eaecef;
            --text-sub: #848e9c;
            --green: #0ecb81;
            --red: #f6465d;
            --accent: #f0b90b;
        }
        html, body { height: 100%; overflow-y: auto; -webkit-overflow-scrolling: touch; }
        body { font-family: -apple-system, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 10px; }
        .gauge-card { background: linear-gradient(135deg, #1e2329 0%, #111418 100%); border: 1px solid var(--card-border); border-radius: 14px; padding: 14px; text-align: center; margin-bottom: 12px; }
        .gauge-score { font-size: 1.6rem; font-weight: bold; color: var(--accent); margin-top: 4px; }
        .tab-container { display: flex; gap: 8px; margin-bottom: 14px; overflow-x: auto; padding-bottom: 4px; }
        .tab-btn { background: #161a1e; border: 1px solid var(--card-border); color: var(--text-sub); padding: 8px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; cursor: pointer; white-space: nowrap; transition: 0.2s; display: flex; align-items: center; gap: 4px; }
        .tab-btn.active { background: #2b313a; border-color: var(--accent); color: var(--text-main); }
        .badge-active { background: rgba(14, 203, 129, 0.15); color: var(--green); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .badge-repeat { background: rgba(240, 185, 11, 0.2); color: var(--accent); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; margin-left: 4px; }
        .badge-expired { background: rgba(246, 70, 93, 0.15); color: var(--red); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .rating-stars { color: var(--accent); font-size: 0.85rem; font-weight: bold; }
        .card { background-color: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 12px; cursor: pointer; transition: 0.2s; }
        .card.expired-card { background-color: #121519; border: 1px solid rgba(246, 70, 93, 0.3); }
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .coin-title { font-size: 1.15rem; font-weight: bold; }
        .price-val { font-size: 1.1rem; font-weight: bold; }
        .price-compare-box { background: #111418; border-radius: 8px; padding: 8px 10px; margin: 8px 0; display: flex; justify-content: space-between; font-size: 0.78rem; }
        .metrics-grid { background: #111418; border-radius: 8px; padding: 10px; margin: 8px 0; font-size: 0.78rem; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; color: var(--text-sub); }
        .metric-item b { color: var(--text-main); }
        .loading { text-align: center; color: var(--text-sub); padding: 30px; font-size: 0.85rem; }
        .view-section { display: none; }
        .view-section.active-view { display: block; }
        .positive { color: var(--green); }
        .negative { color: var(--red); }
    </style>
</head>
<body>
    <div class="gauge-card">
        <div style="font-size: 0.8rem; color: var(--text-sub);">📊 BingX 飆漲幣精準追蹤系統 (前50強篩選 · 最多15個)</div>
        <div class="gauge-score">實時飆漲動能掃描中</div>
        <div style="font-size: 0.78rem; color: var(--green); margin-top: 4px;">🟢 止損 -2% · 正盈利回檔 10% 移至失效區</div>
    </div>
    <div class="tab-container">
        <div class="tab-btn active" id="tab-tracking" onclick="switchView('tracking')">📈 飆漲動能追蹤 (嚴選 Top)</div>
        <div class="tab-btn" id="tab-expired" onclick="switchView('expired')">⚠️ 已失效 / 迴避</div>
    </div>
    <div id="view-tracking" class="view-section active-view"><div id="market-feed"><div class="loading">正在透過後端取得 BingX 前 50 強漲幅榜...</div></div></div>
    <div id="view-expired" class="view-section"><div id="expired-feed"><div class="loading">目前尚無回檔失效標的...</div></div></div>
    <script>
        let globalData = [], globalFundingRate = {}, activeSignals = {}, expiredSignals = {}, alertCounts = {}, currentTab = 'tracking';
        const STORAGE_KEY = 'bingx_pumping_v1', EXPIRED_KEY = 'bingx_pumping_expired_v1', COUNTS_KEY = 'bingx_pumping_counts_v1';

        function switchView(tabName) {
            currentTab = tabName;
            document.getElementById('tab-tracking').classList.toggle('active', tabName === 'tracking');
            document.getElementById('tab-expired').classList.toggle('active', tabName === 'expired');
            document.getElementById('view-tracking').classList.toggle('active-view', tabName === 'tracking');
            document.getElementById('view-expired').classList.toggle('active-view', tabName === 'expired');
        }
        function loadSignals() {
            let saved = localStorage.getItem(STORAGE_KEY); if (saved) { try { activeSignals = JSON.parse(saved); } catch(e) { activeSignals = {}; } }
            let savedExpired = localStorage.getItem(EXPIRED_KEY); if (savedExpired) { try { expiredSignals = JSON.parse(savedExpired); } catch(e) { expiredSignals = {}; } }
            let savedCounts = localStorage.getItem(COUNTS_KEY); if (savedCounts) { try { alertCounts = JSON.parse(savedCounts); } catch(e) { alertCounts = {}; } }
        }
        function saveSignals() {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(activeSignals));
            localStorage.setItem(EXPIRED_KEY, JSON.stringify(expiredSignals));
            localStorage.setItem(COUNTS_KEY, JSON.stringify(alertCounts));
        }

        async function fetchBingXData() {
            try {
                const res = await fetch('/api/bingx');
                const json = await res.json();
                
                if (json.premium) {
                    let pData = Array.isArray(json.premium) ? json.premium : [json.premium];
                    pData.forEach(item => {
                        if (item.symbol && item.symbol.endsWith('-USDT')) {
                            globalFundingRate[item.symbol] = parseFloat(item.lastFundingRate || 0) * 100;
                        }
                    });
                }

                if (json.tickers) {
                    let rawTickers = Array.isArray(json.tickers) ? json.tickers : [json.tickers];
                    globalData = rawTickers.filter(item => item.symbol && item.symbol.endsWith('-USDT')).map(item => {
                        let last = parseFloat(item.lastPrice || item.close || 0);
                        let prev24h = parseFloat(item.prevClosePrice || item.openPrice || last);
                        let change = prev24h > 0 ? ((last - prev24h) / prev24h) * 100 : parseFloat(item.priceChangePercent || 0);
                        return { symbol: item.symbol, lastPrice: last, change24h: change };
                    }).filter(item => !isNaN(item.lastPrice) && item.lastPrice > 0);

                    // 依照 24 小時漲幅由大到小排序
                    globalData.sort((a, b) => b.change24h - a.change24h);

                    loadSignals();
                    let now = Date.now(), twentyFourHours = 24 * 60 * 60 * 1000;
                    Object.keys(expiredSignals).forEach(sym => { if (now - expiredSignals[sym].timestamp > twentyFourHours) delete expiredSignals[sym]; });
                    Object.keys(alertCounts).forEach(sym => { if (now - alertCounts[sym].lastTime > twentyFourHours) delete alertCounts[sym]; });

                    // 1. 檢查現有追蹤標的是否觸發風控 (-2% 止損或回檔 10%)
                    Object.keys(activeSignals).forEach(sym => {
                        let coin = globalData.find(c => c.symbol === sym);
                        if (coin) {
                            let initPrice = activeSignals[sym].firstAlertPrice;
                            let currentGain = ((coin.lastPrice - initPrice) / initPrice) * 100;
                            
                            if (currentGain > (activeSignals[sym].maxGain || 0)) {
                                activeSignals[sym].maxGain = currentGain;
                            }
                            
                            let maxGain = activeSignals[sym].maxGain || 0;
                            let shouldExpire = false;
                            let expireReason = "";

                            if (currentGain <= -2.0) {
                                shouldExpire = true;
                                expireReason = "止損 (-2%)";
                            }
                            else if (maxGain > 0 && (currentGain <= maxGain - 10.0)) {
                                shouldExpire = true;
                                expireReason = `盈利回檔 10% (高點 +${maxGain.toFixed(2)}%)`;
                            }

                            if (shouldExpire) {
                                expiredSignals[sym] = { 
                                    symbol: sym, 
                                    firstAlertPrice: initPrice, 
                                    expiredPrice: coin.lastPrice, 
                                    maxGain: maxGain.toFixed(2), 
                                    reason: expireReason,
                                    timestamp: now, 
                                    timeStr: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) 
                                };
                                delete activeSignals[sym];
                            }
                        }
                    });

                    // 2. 從前 50 強中嚴格篩選飆漲幣（設定門檻：24h漲幅須大於 3%）
                    let top50Pool = globalData.slice(0, 50);
                    let qualifiedCoins = top50Pool.filter(coin => coin.change24h >= 3.0 && !expiredSignals[coin.symbol]);

                    // 3. 寧缺勿濫，最多取 15 個
                    let selectedCoins = qualifiedCoins.slice(0, 15);
                    let selectedSymbols = selectedCoins.map(c => c.symbol);

                    Object.keys(activeSignals).forEach(sym => {
                        if (!selectedSymbols.includes(sym) && (activeSignals[sym].maxGain || 0) < 1.0) {
                            delete activeSignals[sym];
                        }
                    });

                    selectedCoins.forEach(coin => {
                        let sym = coin.symbol;
                        if (!activeSignals[sym]) {
                            let timeString = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                            
                            if (!alertCounts[sym]) {
                                alertCounts[sym] = { count: 1, lastTime: now };
                            } else {
                                alertCounts[sym].count += 1;
                                alertCounts[sym].lastTime = now;
                            }

                            activeSignals[sym] = { 
                                symbol: sym, 
                                firstAlertPrice: coin.lastPrice, 
                                alertTime: timeString, 
                                maxGain: 0.0, 
                                score: coin.change24h.toFixed(2),
                                alertCount: alertCounts[sym].count
                            };
                        } else {
                            if (alertCounts[sym]) {
                                activeSignals[sym].alertCount = alertCounts[sym].count;
                            }
                        }
                    });

                    let activeKeys = Object.keys(activeSignals);
                    if (activeKeys.length > 15) {
                        activeKeys.sort((a, b) => {
                            let cA = globalData.find(c => c.symbol === a)?.change24h || 0;
                            let cB = globalData.find(c => c.symbol === b)?.change24h || 0;
                            return cB - cA;
                        });
                        for (let i = 15; i < activeKeys.length; i++) {
                            delete activeSignals[activeKeys[i]];
                        }
                    }

                    saveSignals(); 
                    renderView();
                }
            } catch (err) { console.error("BingX 數據載入錯誤:", err); }
        }

        function getRecommendationStars(change24h, diffPct) {
            let score = (change24h * 0.4) + (parseFloat(diffPct) * 0.6);
            if (score > 12) return "⭐⭐⭐⭐⭐ (極強飆漲)";
            if (score > 8)  return "⭐⭐⭐⭐ (強勢追價)";
            if (score > 4)  return "⭐⭐⭐ (波段關注)";
            if (score > 0)  return "⭐⭐ (震盪偏多)";
            return "⭐ (保守觀望)";
        }

        function toggleCard(cardElement) { cardElement.classList.toggle('expanded'); }

        function renderView() {
            let activeHtml = '', activeKeys = Object.keys(activeSignals);
            if (activeKeys.length === 0) activeHtml = '<div class="loading">目前 BingX 前 50 強中暫無符合條件的飆漲幣（寧缺勿濫）...</div>';
            else {
                activeKeys.sort((a, b) => {
                    let cA = globalData.find(c => c.symbol === a)?.change24h || 0;
                    let cB = globalData.find(c => c.symbol === b)?.change24h || 0;
                    return cB - cA;
                });

                activeKeys.forEach(k => {
                    let sig = activeSignals[k], coinData = globalData.find(c => c.symbol === sig.symbol);
                    if (!coinData) return;
                    let currentPrice = coinData.lastPrice, firstAlert = parseFloat(sig.firstAlertPrice);
                    let diffPct = (((currentPrice - firstAlert) / firstAlert) * 100).toFixed(2), isDiffPos = diffPct >= 0;
                    let priceStr = currentPrice < 1 ? currentPrice.toFixed(4) : currentPrice.toFixed(2);
                    let alertPriceStr = firstAlert < 1 ? firstAlert.toFixed(4) : firstAlert.toFixed(2);
                    let fundingRate = globalFundingRate[sig.symbol] !== undefined ? globalFundingRate[sig.symbol].toFixed(4) : "0.0100";
                    let isFundingPos = parseFloat(fundingRate) >= 0;

                    let stars = getRecommendationStars(coinData.change24h, diffPct);
                    let count = sig.alertCount || 1;
                    let repeatBadge = count >= 2 ? `<span class="badge-repeat">⚠️ 第 ${count} 次警報</span>` : '';

                    activeHtml += `
                        <div class="card" onclick="toggleCard(this)">
                            <div class="row" style="margin-bottom: 6px;">
                                <div>
                                    <span class="badge-active">🚀 飆漲動能 · 24h: +${coinData.change24h.toFixed(2)}%</span>
                                    ${repeatBadge}
                                </div>
                                <span class="rating-stars">${stars}</span>
                            </div>
                            <div class="row">
                                <div><span class="coin-title">${sig.symbol}</span> <span style="font-size: 0.75rem; color: var(--text-sub);">BingX 永續</span></div>
                                <div class="price-box">
                                    <div class="price-val">$${priceStr}</div>
                                </div>
                            </div>
                            <div class="price-compare-box">
                                <div>🚨 <b>捕捉價位</b><br><span style="color:var(--text-main); font-weight:bold;">$${alertPriceStr}</span></div>
                                <div style="text-align: right;">📊 <b>當前即時價位</b><br><span style="color:var(--text-main); font-weight:bold;">$${priceStr}</span></div>
                            </div>
                            <div class="metrics-grid">
                                <div class="metric-item">追蹤動能：<b class="${isDiffPos ? 'positive' : 'negative'}">${isDiffPos ? '+' : ''}${diffPct}%</b></div>
                                <div class="metric-item">資金費率：<b style="color: ${isFundingPos ? 'var(--green)' : 'var(--red)'};">${isFundingPos ? '+' : ''}${fundingRate}%</b></div>
                                <div class="metric-item" style="grid-column: span 2;">最高盈利記錄：<b style="color: var(--accent);">+${(activeSignals[k].maxGain || 0).toFixed(2)}%</b></div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('market-feed').innerHTML = activeHtml;

            let expiredHtml = '', expiredKeys = Object.keys(expiredSignals);
            if (expiredKeys.length === 0) expiredHtml = '<div class="loading">目前尚無回檔失效標的</div>';
            else {
                expiredKeys.forEach(k => {
                    let exp = expiredSignals[k];
                    expiredHtml += `
                        <div class="card expired-card">
                            <div class="row" style="margin-bottom: 6px;">
                                <span class="badge-expired">⚠️ 已失效 · ${exp.reason} (曾高點 +${exp.maxGain}%)</span>
                                <span style="font-size: 0.72rem; color: var(--text-sub);">${exp.timeStr} 移出</span>
                            </div>
                            <div class="row">
                                <div><span class="coin-title">${exp.symbol}</span></div>
                                <div style="font-size: 0.8rem; color: var(--text-sub);">捕捉價: $${exp.firstAlertPrice} ➔ 離開價: $${exp.expiredPrice}</div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('expired-feed').innerHTML = expiredHtml;
        }

        fetchBingXData(); setInterval(fetchBingXData, 15000);
    </script>
</body>
</html>
"""


class MyHandler(http.server.SimpleHTTPRequestHandler):

  def do_GET(self):
    if self.path == "/api/bingx":
      self.send_response(200)
      self.send_header("Content-type", "application/json; charset=utf-8")
      self.end_headers()
      self.wfile.write(json.dumps(bingx_cache).encode("utf-8"))
    else:
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(html_content.encode("utf-8"))


if __name__ == "__main__":
  bg_thread = threading.Thread(target=fetch_bingx_background, daemon=True)
  bg_thread.start()

  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"🚀 BingX 飆漲追蹤雲端伺服器已在 Port {PORT} 啟動！")
    httpd.serve_forever()
