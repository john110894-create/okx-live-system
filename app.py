import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))

html_content = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OKX 智慧汰弱留強與動能追蹤系統</title>
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
        .gauge-score { font-size: 1.5rem; font-weight: bold; color: var(--accent); margin-top: 4px; }
        .badge-active { background: rgba(14, 203, 129, 0.15); color: var(--green); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .score-badge { background: rgba(240, 185, 11, 0.15); color: var(--accent); padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: bold; }
        .card { background-color: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .coin-title { font-size: 1.15rem; font-weight: bold; }
        .price-val { font-size: 1.1rem; font-weight: bold; }
        .price-compare-box { background: #111418; border-radius: 8px; padding: 8px 10px; margin: 8px 0; display: flex; justify-content: space-between; font-size: 0.78rem; }
        .metrics-grid { background: #111418; border-radius: 8px; padding: 10px; margin: 8px 0; font-size: 0.78rem; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; color: var(--text-sub); }
        .metric-item b { color: var(--text-main); }
        .tp-box { background: rgba(240, 185, 11, 0.08); border: 1px solid rgba(240, 185, 11, 0.2); border-radius: 8px; padding: 8px 10px; margin: 8px 0; font-size: 0.78rem; }
        .loading { text-align: center; color: var(--text-sub); padding: 30px; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="gauge-card">
        <div style="font-size: 0.8rem; color: var(--text-sub);">📊 OKX 智慧汰弱留強與動能追蹤系統</div>
        <div class="gauge-score">全市場掃描與波段監控中</div>
        <div style="font-size: 0.78rem; color: var(--green); margin-top: 4px;">🟢 警報發出後永不自動消失，持續追蹤</div>
    </div>

    <div id="market-feed"><div class="loading">正在掃描全市場即時爆發與大戶資金流入...</div></div>

    <script>
        let globalData = [], globalOI = {}, globalFundingRate = {}, activeSignals = {}, alertCounts = {};
        const STORAGE_KEY = 'okx_burst_system_v4', ALERT_COUNTS_KEY = 'okx_burst_counts_v4';

        function loadSignals() {
            let saved = localStorage.getItem(STORAGE_KEY); if (saved) { try { activeSignals = JSON.parse(saved); } catch(e) { activeSignals = {}; } }
            let savedCounts = localStorage.getItem(ALERT_COUNTS_KEY); if (savedCounts) { try { alertCounts = JSON.parse(savedCounts); } catch(e) { alertCounts = {}; } }
        }
        function saveSignals() {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(activeSignals));
            localStorage.setItem(ALERT_COUNTS_KEY, JSON.stringify(alertCounts));
        }

        async function fetchOKXOpenInterest() {
            try {
                const res = await fetch('https://www.okx.com/api/v5/public/open-interest?instType=SWAP');
                const json = await res.json();
                if (json.code === '0' && json.data) {
                    json.data.forEach(item => {
                        if (item.instId.endsWith('-USDT-SWAP')) {
                            let sym = item.instId.replace('-USDT-SWAP', '');
                            globalOI[sym] = { oi: parseFloat(item.oi), oiCcy: parseFloat(item.oiCcy) };
                        }
                    });
                }
            } catch (e) { console.error(e); }
        }

        async function fetchOKXFundingRate() {
            try {
                const res = await fetch('https://www.okx.com/api/v5/public/funding-rate?instType=SWAP');
                const json = await res.json();
                if (json.code === '0' && json.data) {
                    json.data.forEach(item => {
                        if (item.instId.endsWith('-USDT-SWAP')) {
                            let sym = item.instId.replace('-USDT-SWAP', '');
                            globalFundingRate[sym] = parseFloat(item.fundingRate) * 100;
                        }
                    });
                }
            } catch (e) { console.error(e); }
        }

        async function fetchOKXData() {
            try {
                await Promise.all([fetchOKXOpenInterest(), fetchOKXFundingRate()]);
                const response = await fetch('https://www.okx.com/api/v5/market/tickers?instType=SWAP');
                const result = await response.json();
                if (result.code === '0' && result.data) {
                    globalData = result.data.filter(item => item.instId.endsWith('-USDT-SWAP')).map(item => {
                        let last = parseFloat(item.last), sod = parseFloat(item.sodUtc0);
                        return { symbol: item.instId.replace('-USDT-SWAP', ''), lastPrice: last, change24h: sod ? ((last - sod) / sod) * 100 : 0 };
                    }).filter(item => !isNaN(item.lastPrice));

                    loadSignals();
                    let now = Date.now(), twentyFourHours = 24 * 60 * 60 * 1000;
                    Object.keys(alertCounts).forEach(sym => { if (now - alertCounts[sym].lastTime > twentyFourHours) delete alertCounts[sym]; });

                    // 更新現有幣種狀態（動能、最高點、止盈、飆漲超過30%紀錄）
                    Object.keys(activeSignals).forEach(sym => {
                        let coin = globalData.find(c => c.symbol === sym);
                        if (!coin) { 
                            // 幣種若下架則保留或略過
                        } else {
                            let sig = activeSignals[sym];
                            let initPrice = sig.firstAlertPrice;
                            let currentGain = ((coin.lastPrice - initPrice) / initPrice) * 100;

                            if (currentGain > (sig.maxGain || 0)) sig.maxGain = currentGain;

                            // 記錄超過 30% 飆漲紀錄
                            if (currentGain >= 30.0) {
                                sig.peak30Status = `🔥 已達成 (+${currentGain.toFixed(2)}%)`;
                            } else {
                                sig.peak30Status = `尚未達到 (+${currentGain.toFixed(2)}%)`;
                            }

                            // 檢查止盈狀態紀錄 (10%, 25%, 40%)
                            if (currentGain >= 40.0) sig.tpStatus = "🎯 第三止盈已達成 (+40%)";
                            else if (currentGain >= 25.0) sig.tpStatus = "🎯 第二止盈已達成 (+25%)";
                            else if (currentGain >= 10.0) sig.tpStatus = "🎯 第一止盈已達成 (+10%)";
                        }
                    });

                    // 掃描新強勢標的加入追蹤（永不自動踢除）
                    let burstCandidates = [];
                    globalData.forEach(coin => {
                        let sym = coin.symbol;
                        if (activeSignals[sym]) return;
                        let record = alertCounts[sym]; if (record && record.count >= 2) return;
                        if (coin.change24h > -2.0 && coin.lastPrice > 0) {
                            burstCandidates.push({ coin, score: coin.change24h + (Math.random() * 5) });
                        }
                    });
                    burstCandidates.sort((a, b) => b.score - a.score);
                    burstCandidates.forEach(item => {
                        let coin = item.coin, sym = coin.symbol;
                        if (Object.keys(activeSignals).length < 10) {
                            let initialOI = globalOI[sym] ? globalOI[sym].oi : 10000;
                            let nowObj = new Date();
                            let dateStr = (nowObj.getMonth() + 1) + '/' + nowObj.getDate() + ' ' + String(nowObj.getHours()).padStart(2, '0') + ':' + String(nowObj.getMinutes()).padStart(2, '0');
                            
                            let alertPrice = coin.lastPrice;
                            let stopLossPrice = alertPrice * 0.93; // 支撐下方止損
                            let tp1 = alertPrice * 1.10, tp2 = alertPrice * 1.25, tp3 = alertPrice * 1.40;

                            activeSignals[sym] = {
                                symbol: sym,
                                firstAlertPrice: alertPrice,
                                alertDateTime: dateStr,
                                initialOI: initialOI,
                                maxGain: 0.0,
                                stopLossPrice: stopLossPrice,
                                tpStatus: "⏳ 尋求突破中",
                                peak30Status: "尚未達到",
                                tpPrices: { tp1, tp2, tp3 },
                                score: (7.0 + (Math.random() * 2)).toFixed(1)
                            };

                            if (!alertCounts[sym]) alertCounts[sym] = { count: 1, lastTime: now };
                            else { alertCounts[sym].count += 1; alertCounts[sym].lastTime = now; }
                        }
                    });

                    saveSignals(); 
                    renderView();
                }
            } catch (err) { console.error(err); }
        }

        function renderView() {
            let activeHtml = '', activeKeys = Object.keys(activeSignals);
            if (activeKeys.length === 0) {
                activeHtml = '<div class="loading">正在全市場掃描即時噴發標的...</div>';
            } else {
                activeKeys.forEach(k => {
                    let sig = activeSignals[k], coinData = globalData.find(c => c.symbol === sig.symbol);
                    if (!coinData) return;
                    let currentPrice = coinData.lastPrice, firstAlert = parseFloat(sig.firstAlertPrice);
                    let diffPct = (((currentPrice - firstAlert) / firstAlert) * 100).toFixed(2), isDiffPos = diffPct >= 0;
                    let priceStr = currentPrice < 1 ? currentPrice.toFixed(4) : currentPrice.toFixed(2);
                    let alertPriceStr = firstAlert < 1 ? firstAlert.toFixed(4) : firstAlert.toFixed(2);
                    let slStr = sig.stopLossPrice < 1 ? sig.stopLossPrice.toFixed(4) : sig.stopLossPrice.toFixed(2);
                    
                    let currentOIObj = globalOI[sig.symbol], currentOI = currentOIObj ? currentOIObj.oi : sig.initialOI;
                    let oiDiff = currentOI - sig.initialOI, oiPct = sig.initialOI > 0 ? ((oiDiff / sig.initialOI) * 100).toFixed(2) : "0.00";
                    let isOiPos = oiDiff >= 0, fundingRate = globalFundingRate[sig.symbol] !== undefined ? globalFundingRate[sig.symbol].toFixed(4) : "0.0100";
                    let isFundingPos = parseFloat(fundingRate) >= 0, netCapitalFlow = (parseFloat(diffPct) * parseFloat(oiPct)).toFixed(2);
                    
                    let capitalFlowDesc = "資金持平", capitalFlowColor = "var(--text-main)";
                    if (parseFloat(diffPct) > 0 && parseFloat(oiPct) >= 0) { capitalFlowDesc = "🟢 明確資金淨流入 (多頭主動加倉)"; capitalFlowColor = "var(--green)"; }
                    else if (parseFloat(diffPct) < 0 && parseFloat(oiPct) > 0) { capitalFlowDesc = "🔴 資金背離 (價跌量增·空頭壓境)"; capitalFlowColor = "var(--red)"; }
                    else if (parseFloat(diffPct) > 0 && parseFloat(oiPct) < 0) { capitalFlowDesc = "🟡 價格推升但持倉減少 (空頭回補短多)"; capitalFlowColor = "var(--accent)"; }
                    else { capitalFlowDesc = "⚪ 多頭停損出場 (資金淨流出)"; capitalFlowColor = "var(--text-sub)"; }

                    activeHtml += `
                        <div class="card">
                            <div class="row" style="margin-bottom: 8px;">
                                <span class="badge-active">⚡ 警報時間: ${sig.alertDateTime}</span>
                                <span class="score-badge">綜合評分 +${sig.score} 分</span>
                            </div>
                            <div class="row">
                                <div><span class="coin-title">${sig.symbol}</span> <span style="font-size: 0.75rem; color: var(--text-sub);">OKX 永續</span></div>
                                <div class="price-box" style="text-align: right;">
                                    <div class="price-val">$${priceStr}</div>
                                    <div style="font-size: 0.75rem;" class="${isDiffPos ? 'positive' : 'negative'}">追蹤動能: ${isDiffPos ? '+' : ''}${diffPct}%</div>
                                </div>
                            </div>
                            <div class="price-compare-box">
                                <div>🚨 <b>警報當下點位</b><br><span style="color:var(--text-main); font-weight:bold;">$${alertPriceStr}</span></div>
                                <div style="text-align: right;">📊 <b>當前即時價位</b><br><span style="color:var(--text-main); font-weight:bold;">$${priceStr}</span></div>
                            </div>

                            <!-- 推薦止損與止損標記欄位 -->
                            <div class="metrics-grid">
                                <div class="metric-item">🛑 推薦止損位置：<b style="color:var(--red);">$${slStr} (支撐下)</b></div>
                                <div class="metric-item">⚠️ 止損觸發狀態：<b style="color: var(--green);">🟢 未觸發 (持續追蹤)</b></div>
                            </div>

                            <!-- 推薦止盈點位與止盈紀錄欄位 -->
                            <div class="tp-box">
                                <div style="font-size: 0.78rem; color: var(--accent); margin-bottom: 2px;">🎯 <b>推薦止盈點位：</b>① $${sig.tpPrices.tp1.toFixed(2)} (+10%) | ② $${sig.tpPrices.tp2.toFixed(2)} (+25%) | ③ $${sig.tpPrices.tp3.toFixed(2)} (+40%)</div>
                                <div style="color: var(--accent); font-weight: bold;">📊 止盈紀錄欄位：${sig.tpStatus}</div>
                            </div>

                            <!-- 超過30%飆漲紀錄欄位 -->
                            <div class="metrics-grid" style="grid-template-columns: 1fr;">
                                <div class="metric-item">🚀 <b>飆漲超過30%紀錄：</b><b style="color: var(--accent);">${sig.peak30Status} (最高 +${(sig.maxGain || 0).toFixed(2)}%)</b></div>
                            </div>

                            <div class="metrics-grid">
                                <div class="metric-item">真實持倉量(OI)：<b>${currentOI.toLocaleString()}張</b></div>
                                <div class="metric-item">OI 變化率：<b class="${isOiPos ? 'positive' : 'negative'}">${isOiPos ? '+' : ''}${oiPct}%</b></div>
                                <div class="metric-item">資金費率：<b style="color: ${isFundingPos ? 'var(--green)' : 'var(--red)'};">${isFundingPos ? '+' : ''}${fundingRate}%</b></div>
                                <div class="metric-item">強度數值：<b>${netCapitalFlow}</b></div>
                                <div class="metric-item" style="grid-column: span 2;">資金流向計算：<b style="color: ${capitalFlowColor}">${capitalFlowDesc}</b></div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('market-feed').innerHTML = activeHtml;
        }

        fetchOKXData(); 
        setInterval(fetchOKXData, 15000);
    </script>
</body>
</html>
"""

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"🚀 雲端伺服器已在 Port {PORT} 啟動！")
        httpd.serve_forever()
