import http.server
import os
import socketserver
import json
import urllib.request
 
PORT = int(os.environ.get("PORT", 8080))

HTML_CONTENT = """<!DOCTYPE html>
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
        .gauge-score { font-size: 1.4rem; font-weight: bold; color: var(--accent); margin-top: 4px; }
        
        .tab-container { display: flex; gap: 8px; margin-bottom: 14px; overflow-x: auto; padding-bottom: 4px; }
        .tab-btn { background: #161a1e; border: 1px solid var(--card-border); color: var(--text-sub); padding: 8px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; cursor: pointer; white-space: nowrap; transition: 0.2s; display: flex; align-items: center; gap: 4px; }
        .tab-btn.active { background: #2b313a; border-color: var(--accent); color: var(--text-main); }
        
        .badge-active { background: rgba(14, 203, 129, 0.15); color: var(--green); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .badge-expired { background: rgba(246, 70, 93, 0.15); color: var(--red); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .score-badge { background: rgba(240, 185, 11, 0.15); color: var(--accent); padding: 3px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: bold; }
        
        .card { background-color: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
        .card.expired-card { background-color: #121519; border: 1px solid rgba(246, 70, 93, 0.3); }
        
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .coin-title { font-size: 1.15rem; font-weight: bold; }
        .price-val { font-size: 1.1rem; font-weight: bold; }
        
        .price-compare-box { background: #111418; border-radius: 8px; padding: 8px 10px; margin: 8px 0; display: flex; justify-content: space-between; font-size: 0.78rem; }
        .metrics-grid { background: #111418; border-radius: 8px; padding: 10px; margin: 8px 0; font-size: 0.78rem; display: grid; grid-template-columns: 1fr 1fr; gap: 6px; color: var(--text-sub); }
        .metric-item b { color: var(--text-main); }
        .tp-box { background: rgba(240, 185, 11, 0.08); border: 1px solid rgba(240, 185, 11, 0.2); border-radius: 8px; padding: 8px 10px; margin: 8px 0; font-size: 0.78rem; }
        
        .loading { text-align: center; color: var(--text-sub); padding: 30px; font-size: 0.85rem; }
        .view-section { display: none; }
        .view-section.active-view { display: block; }
    </style>
</head>
<body>
    <div class="gauge-card">
        <div style="font-size: 0.8rem; color: var(--text-sub);">📊 OKX 智慧汰弱留強與動能追蹤系統</div>
        <div class="gauge-score">動態監控中</div>
        <div style="font-size: 0.78rem; color: var(--green); margin-top: 4px;">🟢 後端直連 OKX API 穩定運行中</div>
    </div>

    <div class="tab-container">
        <div class="tab-btn active" id="tab-tracking" onclick="switchView('tracking')">📈 即時追蹤</div>
        <div class="tab-btn" id="tab-expired" onclick="switchView('expired')">⚠️ 已失效 / 結算紀錄</div>
    </div>

    <div id="view-tracking" class="view-section active-view">
        <div id="market-feed"><div class="loading">正在載入市場行情數據...</div></div>
    </div>

    <div id="view-expired" class="view-section">
        <div id="expired-feed"><div class="loading">目前尚無已結算之止盈/止損紀錄...</div></div>
    </div>

    <script>
        function switchView(tabName) {
            document.getElementById('tab-tracking').classList.toggle('active', tabName === 'tracking');
            document.getElementById('tab-expired').classList.toggle('active', tabName === 'expired');
            document.getElementById('view-tracking').classList.toggle('active-view', tabName === 'tracking');
            document.getElementById('view-expired').classList.toggle('active-view', tabName === 'expired');
        }

        async function loadData() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                renderTracking(data.activeSignals);
                renderExpired(data.expiredSignals);
            } catch (e) {
                console.error(e);
            }
        }

        function renderTracking(signals) {
            let html = '';
            let keys = Object.keys(signals);
            if (keys.length === 0) {
                html = '<div class="loading">正在掃描市場強勢幣種...</div>';
            } else {
                keys.forEach(k => {
                    let sig = signals[k];
                    let isDiffPos = sig.diffPct >= 0;
                    let capitalFlowColor = sig.capitalFlow.includes("流入") ? "var(--green)" : (sig.capitalFlow.includes("背離") ? "var(--red)" : "var(--accent)");
                    
                    html += `
                        <div class="card">
                            <div class="row" style="margin-bottom: 8px;">
                                <span class="badge-active">🚀 警報時間: ${sig.alertDateTime}</span>
                                <span class="score-badge">綜合評分 +${sig.score} 分</span>
                            </div>
                            <div class="row">
                                <div><span class="coin-title">${sig.symbol}</span> <span style="font-size: 0.75rem; color: var(--text-sub);">OKX 永續</span></div>
                                <div class="price-box" style="text-align: right;">
                                    <div class="price-val">$${sig.priceStr}</div>
                                    <div style="font-size: 0.75rem; color: ${isDiffPos ? 'var(--green)' : 'var(--red)'};">追蹤動能: ${isDiffPos ? '+' : ''}${sig.diffPct}%</div>
                                </div>
                            </div>
                            <div class="price-compare-box">
                                <div>🚨 <b>警報當下點位</b><br><span style="color:var(--text-main); font-weight:bold;">$${sig.alertPriceStr}</span></div>
                                <div style="text-align: right;">📊 <b>當前即時價位</b><br><span style="color:var(--text-main); font-weight:bold;">$${sig.priceStr}</span></div>
                            </div>

                            <div class="metrics-grid">
                                <div class="metric-item">🛑 推薦止損位置：<b style="color:var(--red);">$${sig.slStr} (支撐下)</b></div>
                                <div class="metric-item">⚠️ 止損觸發狀態：<b style="color: var(--green);">🟢 未觸發 (持續追蹤)</b></div>
                            </div>

                            <div class="tp-box">
                                <div style="font-size: 0.78rem; color: var(--accent); margin-bottom: 2px;">🎯 <b>推薦止盈點位：</b>① $${sig.tp1} (+10%) | ② $${sig.tp2} (+25%) | ③ $${sig.tp3} (+40%)</div>
                                <div style="color: var(--accent); font-weight: bold;">📊 止盈紀錄欄位：${sig.tpStatus}</div>
                            </div>

                            <div class="metrics-grid" style="grid-template-columns: 1fr 1fr;">
                                <div class="metric-item">🔥 超過30%飆漲紀錄(最高點)：<b style="color: var(--accent);">${sig.peak30Display}</b></div>
                                <div class="metric-item">📈 目前波段最大漲幅：<b>+${sig.maxGain}%</b></div>
                            </div>

                            <div class="metrics-grid">
                                <div class="metric-item">真實持倉量(OI)：<b>${sig.currentOI.toLocaleString()}張</b></div>
                                <div class="metric-item">OI 變化率：<b style="color: ${sig.isOiPos ? 'var(--green)' : 'var(--red)'};">${sig.isOiPos ? '+' : ''}${sig.oiPct}%</b></div>
                                <div class="metric-item">資金費率：<b style="color: ${sig.isFundingPos ? 'var(--green)' : 'var(--red)'};">${sig.isFundingPos ? '+' : ''}${sig.fundingRate}%</b></div>
                                <div class="metric-item">強度數值：<b>${sig.netCapitalFlow}</b></div>
                                <div class="metric-item" style="grid-column: span 2;">資金流向計算：<b style="color: ${capitalFlowColor}">${sig.capitalFlow}</b></div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('market-feed').innerHTML = html;
        }

        function renderExpired(expired) {
            let html = '';
            let keys = Object.keys(expired);
            if (keys.length === 0) {
                html = '<div class="loading">目前尚無已結算之止盈/止損紀錄</div>';
            } else {
                keys.forEach(k => {
                    let exp = expired[k];
                    html += `
                        <div class="card expired-card">
                            <div class="row" style="margin-bottom: 6px;">
                                <span class="badge-expired">${exp.exitReason}</span>
                                <span style="font-size: 0.72rem; color: var(--text-sub);">${exp.timeStr} 結算下架</span>
                            </div>
                            <div class="row">
                                <div><span class="coin-title">${exp.symbol}</span></div>
                                <div style="font-size: 0.8rem; color: var(--text-sub);">警報價: $${exp.firstAlertPrice} ➔ 結算價: $${exp.exitPrice}</div>
                            </div>
                            <div class="metrics-grid" style="margin-top: 6px;">
                                <div class="metric-item">📊 歷史最高漲幅紀錄：<b>+${exp.maxGain}%</b></div>
                                <div class="metric-item">🔥 超過30%紀錄：<b style="color:var(--accent);">${exp.peak30}</b></div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('expired-feed').innerHTML = html;
        }

        loadData();
        setInterval(loadData, 15000);
    </script>
</body>
</html>
"""

# 記憶體內簡單儲存狀態
active_signals = {}
expired_signals = {}
alert_counts = {}

def fetch_okx_data():
    try:
        # 1. 抓取 Tickers
        req = urllib.request.Request("https://www.okx.com/api/v5/market/tickers?instType=SWAP", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            tickers_res = json.loads(response.read().decode())
        
        # 2. 抓取 OI
        req_oi = urllib.request.Request("https://www.okx.com/api/v5/public/open-interest?instType=SWAP", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_oi, timeout=5) as response:
            oi_res = json.loads(response.read().decode())
        
        global_oi = {}
        if oi_res.get("code") == "0":
            for item in oi_res.get("data", []):
                if item["instId"].endswith("-USDT-SWAP"):
                    sym = item["instId"].replace("-USDT-SWAP", "")
                    global_oi[sym] = float(item["oi"])

        # 3. 抓取資金費率
        req_fr = urllib.request.Request("https://www.okx.com/api/v5/public/funding-rate?instType=SWAP", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req_fr, timeout=5) as response:
            fr_res = json.loads(response.read().decode())
        
        global_fr = {}
        if fr_res.get("code") == "0":
            for item in fr_res.get("data", []):
                if item["instId"].endswith("-USDT-SWAP"):
                    sym = item["instId"].replace("-USDT-SWAP", "")
                    global_fr[sym] = float(item.get("fundingRate", 0)) * 100

        if tickers_res.get("code") == "0":
            tickers = tickers_res.get("data", [])
            for item in tickers:
                inst_id = item["instId"]
                if not inst_id.endswith("-USDT-SWAP"):
                    continue
                sym = inst_id.replace("-USDT-SWAP", "")
                last = float(item["last"])
                sod = float(item.get("sodUtc0", last))
                change24h = ((last - sod) / sod) * 100 if sod else 0

                # 檢查已追蹤的幣種
                if sym in active_signals:
                    sig = active_signals[sym]
                    init_price = sig["firstAlertPrice"]
                    gain = ((last - init_price) / init_price) * 100
                    if gain > sig["maxGain"]:
                        sig["maxGain"] = gain
                    if gain > 30.0 and gain > sig["peak30Plus"]:
                        sig["peak30Plus"] = gain

                    if gain >= 40.0: sig["tpStatus"] = "🎯 第三止盈已達成 (+40%)"
                    elif gain >= 25.0: sig["tpStatus"] = "🎯 第二止盈已達成 (+25%)"
                    elif gain >= 10.0: sig["tpStatus"] = "🎯 第一止盈已達成 (+10%)"

                    # 觸發止損
                    if last <= sig["stopLossPrice"]:
                        expired_signals[sym] = {
                            "symbol": sym,
                            "firstAlertPrice": init_price,
                            "exitPrice": last,
                            "maxGain": f"{sig['maxGain']:.2f}",
                            "peak30": f"+{sig['peak30Plus']:.2f}%" if sig["peak30Plus"] > 0 else "未達30%",
                            "exitReason": "🔴 觸發止損出場",
                            "timeStr": "剛剛"
                        }
                        del active_signals[sym]

            # 自動掃描新強勢幣加入
            for item in tickers:
                inst_id = item["instId"]
                if not inst_id.endswith("-USDT-SWAP"):
                    continue
                sym = inst_id.replace("-USDT-SWAP", "")
                if sym in active_signals or sym in expired_signals:
                    continue
                last = float(item["last"])
                sod = float(item.get("sodUtc0", last))
                change24h = ((last - sod) / sod) * 100 if sod else 0

                if change24h > 1.5 and len(active_signals) < 10:
                    init_oi = global_oi.get(sym, 10000)
                    sl = last * 0.93
                    active_signals[sym] = {
                        "symbol": sym,
                        "firstAlertPrice": last,
                        "alertDateTime": "剛剛",
                        "initialOI": init_oi,
                        "maxGain": 0.0,
                        "peak30Plus": 0.0,
                        "stopLossPrice": sl,
                        "tpStatus": "⏳ 尋求突破中",
                        "tpPrices": {"tp1": last * 1.1, "tp2": last * 1.25, "tp3": last * 1.4},
                        "score": "7.8"
                    }

            # 準備傳給前端的資料結構
            processed_active = {}
            for sym, sig in active_signals.items():
                # 這裡重新抓取最新價格
                current_coin = next((t for t in tickers if t["instId"] == f"{sym}-USDT-SWAP"), None)
                if not current_coin: continue
                last = float(current_coin["last"])
                init_p = sig["firstAlertPrice"]
                diff_pct = ((last - init_p) / init_p) * 100
                
                cur_oi = global_oi.get(sym, sig["initialOI"])
                oi_diff = cur_oi - sig["initialOI"]
                oi_pct = (oi_diff / sig["initialOI"]) * 100 if sig["initialOI"] else 0
                fr = global_fr.get(sym, 0.01)

                flow_desc = "🟢 明確資金淨流入 (多頭主動加倉)" if diff_pct > 0 and oi_pct >= 0 else "🟡 價格推升但持倉減少"

                processed_active[sym] = {
                    "symbol": sym,
                    "alertDateTime": sig["alertDateTime"],
                    "score": sig["score"],
                    "priceStr": f"{last:.4f}" if last < 1 else f"{last:.2f}",
                    "alertPriceStr": f"{init_p:.4f}" if init_p < 1 else f"{init_p:.2f}",
                    "diffPct": f"{diff_pct:.2f}",
                    "slStr": f"{sig['stopLossPrice']:.4f}" if sig['stopLossPrice'] < 1 else f"{sig['stopLossPrice']:.2f}",
                    "tp1": f"{sig['tpPrices']['tp1']:.2f}",
                    "tp2": f"{sig['tpPrices']['tp2']:.2f}",
                    "tp3": f"{sig['tpPrices']['tp3']:.2f}",
                    "tpStatus": sig["tpStatus"],
                    "peak30Display": f"+{sig['peak30Plus']:.2f}%" if sig["peak30Plus"] > 0 else "尚未達到 +30%",
                    "maxGain": f"{sig['maxGain']:.2f}",
                    "currentOI": int(cur_oi),
                    "oiPct": f"{oi_pct:.2f}",
                    "isOiPos": oi_pct >= 0,
                    "fundingRate": f"{fr:.4f}",
                    "isFundingPos": fr >= 0,
                    "netCapitalFlow": f"{(diff_pct * oi_pct):.2f}",
                    "capitalFlow": flow_desc
                }

            return {"activeSignals": processed_active, "expiredSignals": expired_signals}
    except Exception as e:
        print("API Error:", e)
        return {"activeSignals": active_signals, "expiredSignals": expired_signals}

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            data = fetch_okx_data()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"🚀 雲端伺服器已在 Port {PORT} 啟動！")
        httpd.serve_forever()
