import http.server
import json
import os
import socketserver
import threading
import time
import urllib.request

PORT = int(os.environ.get("PORT", 8080))

bingx_cache = {"tickers": [], "premium": [], "updated_at": 0}


def fetch_bingx_background():
  while True:
    try:
      req_ticker = urllib.request.Request(
          "https://open-api.bingx.com/openApi/swap/v2/quote/ticker",
          headers={"User-Agent": "Mozilla/5.0"},
      )
      with urllib.request.urlopen(req_ticker, timeout=8) as res:
        ticker_data = json.loads(res.read().decode("utf-8"))

      req_prem = urllib.request.Request(
          "https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex",
          headers={"User-Agent": "Mozilla/5.0"},
      )
      with urllib.request.urlopen(req_prem, timeout=8) as res:
        prem_data = json.loads(res.read().decode("utf-8"))

      if ticker_data.get("code") == 0:
        bingx_cache["tickers"] = ticker_data.get("data", [])
      if prem_data.get("code") == 0:
        bingx_cache["premium"] = prem_data.get("data", [])
      bingx_cache["updated_at"] = int(time.time() * 1000)
    except Exception as e:
      print("背景抓取 BingX 失敗:", e)

    time.sleep(8)


html_content = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>BingX 漲幅榜前 100 強噴發追蹤系統</title>
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
        .sync-status { font-size: 0.72rem; color: var(--text-sub); margin-top: 6px; }
        .tab-container { display: flex; gap: 8px; margin-bottom: 14px; overflow-x: auto; padding-bottom: 4px; }
        .tab-btn { background: #161a1e; border: 1px solid var(--card-border); color: var(--text-sub); padding: 8px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; cursor: pointer; white-space: nowrap; transition: 0.2s; display: flex; align-items: center; gap: 4px; }
        .tab-btn.active { background: #2b313a; border-color: var(--accent); color: var(--text-main); }
        .badge-active { background: rgba(14, 203, 129, 0.15); color: var(--green); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .badge-repeat { background: rgba(240, 185, 11, 0.2); color: var(--accent); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; margin-left: 4px; }
        .badge-expired { background: rgba(246, 70, 93, 0.15); color: var(--red); padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: bold; }
        .rating-stars { color: var(--accent); font-size: 0.85rem; font-weight: bold; }
        .card { background-color: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 12px; transition: 0.2s; }
        .card.expired-card { background-color: #121519; border: 1px solid rgba(246, 70, 93, 0.3); }
        .monthly-card { background: #161a1e; border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
        .monthly-title { font-size: 1.1rem; font-weight: bold; color: var(--accent); margin-bottom: 8px; border-bottom: 1px solid var(--card-border); padding-bottom: 6px; }
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
        <div style="font-size: 0.8rem; color: var(--text-sub);">📊 BingX 漲幅榜前 100 強噴發追蹤系統 (最多 10 檔)</div>
        <div class="gauge-score">高潛力噴發掃描中</div>
        <div style="font-size: 0.78rem; color: var(--green); margin-top: 4px;">🟢 止損 -2% · 正盈利回檔 10% 移至失效區</div>
        <div class="sync-status" id="sync-status">同步狀態：正在連線...</div>
    </div>
    <div class="tab-container">
        <div class="tab-btn active" id="tab-tracking" onclick="switchView('tracking')">📈 噴發動能追蹤 (Top 10)</div>
        <div class="tab-btn" id="tab-expired" onclick="switchView('expired')">⚠️ 已失效 / 迴避</div>
        <div class="tab-btn" id="tab-monthly" onclick="switchView('monthly')">📊 每月覆盤統計</div>
    </div>
    <div id="view-tracking" class="view-section active-view"><div id="market-feed"><div class="loading">正在從前 100 大漲幅榜篩選高噴發標的...</div></div></div>
    <div id="view-expired" class="view-section"><div id="expired-feed"><div class="loading">目前尚無回檔失效標的...</div></div></div>
    <div id="view-monthly" class="view-section"><div id="monthly-feed"><div class="loading">正在統計每月表現...</div></div></div>
    <script>
        let globalData = [], globalFundingRate = {}, activeSignals = {}, expiredSignals = {}, alertCounts = {}, currentTab = 'tracking';
        let isFetching = false;
        const STORAGE_KEY = 'bingx_top100_v1', EXPIRED_KEY = 'bingx_top100_expired_v1', COUNTS_KEY = 'bingx_top100_counts_v1';

        function switchView(tabName) {
            currentTab = tabName;
            document.getElementById('tab-tracking').classList.toggle('active', tabName === 'tracking');
            document.getElementById('tab-expired').classList.toggle('active', tabName === 'expired');
            document.getElementById('tab-monthly').classList.toggle('active', tabName === 'monthly');
            document.getElementById('view-tracking').classList.toggle('active-view', tabName === 'tracking');
            document.getElementById('view-expired').classList.toggle('active-view', tabName === 'expired');
            document.getElementById('view-monthly').classList.toggle('active-view', tabName === 'monthly');
            if (tabName === 'monthly') renderMonthlyStats();
            fetchBingXData(true);
        }

        function loadSignals() {
            let saved = localStorage.getItem(STORAGE_KEY);
            if (saved) { try { activeSignals = JSON.parse(saved); } catch(e) { activeSignals = {}; } }
            let savedExpired = localStorage.getItem(EXPIRED_KEY);
            if (savedExpired) { try { expiredSignals = JSON.parse(savedExpired); } catch(e) { expiredSignals = {}; } }
            let savedCounts = localStorage.getItem(COUNTS_KEY);
            if (savedCounts) { try { alertCounts = JSON.parse(savedCounts); } catch(e) { alertCounts = {}; } }
        }

        function saveSignals() {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(activeSignals));
            localStorage.setItem(EXPIRED_KEY, JSON.stringify(expiredSignals));
            localStorage.setItem(COUNTS_KEY, JSON.stringify(alertCounts));
        }

        function getBurstScore(coin, diffPct, fundingRate) {
            let momentum = parseFloat(diffPct || 0);
            let fundingBonus = fundingRate < 0 ? Math.abs(fundingRate) * 2 : (fundingRate > 0.1 ? -1 : 0.5);
            return (coin.change24h * 0.45) + (momentum * 0.45) + fundingBonus;
        }

        function getRecommendationStars(score) {
            if (score >= 16) return "⭐⭐⭐⭐⭐ (極高噴發)";
            if (score >= 10) return "⭐⭐⭐⭐ (強勢噴發)";
            if (score >= 5)  return "⭐⭐⭐ (動能轉強)";
            if (score >= 1)  return "⭐⭐ (溫和偏多)";
            return "⭐ (觀察中)";
        }

        function updateSyncLabel(serverUpdatedAt) {
            const el = document.getElementById('sync-status');
            if (!el) return;
            const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            const srvStr = serverUpdatedAt
                ? new Date(serverUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
                : nowStr;
            el.textContent = `同步狀態：已即時同步 · 行情時間 ${srvStr} · 刷新 ${nowStr}`;
        }

        loadSignals();
        renderView();

        async function fetchBingXData(force = false) {
            if (isFetching && !force) return;
            isFetching = true;
            try {
                // 加上時間戳記與 no-store 避免瀏覽器或代理快取舊資料
                const res = await fetch(`/api/bingx?_=${Date.now()}`, {
                    cache: 'no-store',
                    headers: { 'Cache-Control': 'no-cache' }
                });
                const json = await res.json();

                if (json.premium) {
                    let pData = Array.isArray(json.premium) ? json.premium : [json.premium];
                    pData.forEach(item => {
                        if (item.symbol && item.symbol.endsWith('-USDT')) {
                            globalFundingRate[item.symbol] = parseFloat(item.lastFundingRate || 0) * 100;
                        }
                    });
                }

                if (json.tickers && json.tickers.length > 0) {
                    let rawTickers = Array.isArray(json.tickers) ? json.tickers : [json.tickers];
                    globalData = rawTickers
                        .filter(item => item.symbol && item.symbol.endsWith('-USDT'))
                        .map(item => {
                            let last = parseFloat(item.lastPrice || item.close || 0);
                            let prev24h = parseFloat(item.prevClosePrice || item.openPrice || last);
                            let change = prev24h > 0 ? ((last - prev24h) / prev24h) * 100 : parseFloat(item.priceChangePercent || 0);
                            return { symbol: item.symbol, lastPrice: last, change24h: change };
                        })
                        .filter(item => !isNaN(item.lastPrice) && item.lastPrice > 0);

                    globalData.sort((a, b) => b.change24h - a.change24h);

                    loadSignals();
                    let now = Date.now(), twentyFourHours = 24 * 60 * 60 * 1000;
                    Object.keys(expiredSignals).forEach(sym => {
                        if (now - expiredSignals[sym].timestamp > twentyFourHours) delete expiredSignals[sym];
                    });
                    Object.keys(alertCounts).forEach(sym => {
                        if (now - alertCounts[sym].lastTime > twentyFourHours) delete alertCounts[sym];
                    });

                    // 1. 風控檢查 (-2% 止損或正盈利回檔 10%)
                    Object.keys(activeSignals).forEach(sym => {
                        let coin = globalData.find(c => c.symbol === sym);
                        if (coin) {
                            let initPrice = activeSignals[sym].firstAlertPrice;
                            let currentGain = ((coin.lastPrice - initPrice) / initPrice) * 100;
                            let prevMax = parseFloat(activeSignals[sym].maxGain || 0);
                            let syncedMax = Math.max(prevMax, currentGain, parseFloat(activeSignals[sym].initialMomentum || 0));
                            activeSignals[sym].maxGain = syncedMax;

                            let shouldExpire = false;
                            let expireReason = "";

                            if (currentGain <= -2.0) {
                                shouldExpire = true;
                                expireReason = "止損 (-2%)";
                            } else if (syncedMax > 0 && (currentGain <= syncedMax - 10.0)) {
                                shouldExpire = true;
                                expireReason = `盈利回檔 10% (高點 +${syncedMax.toFixed(2)}%)`;
                            }

                            if (shouldExpire) {
                                expiredSignals[sym] = {
                                    symbol: sym,
                                    firstAlertPrice: initPrice,
                                    expiredPrice: coin.lastPrice,
                                    maxGain: syncedMax.toFixed(2),
                                    reason: expireReason,
                                    timestamp: now,
                                    date: new Date().toISOString().slice(0, 7),
                                    timeStr: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                };
                                delete activeSignals[sym];
                            }
                        }
                    });

                    // 2. 鎖定漲幅榜前 100 名，挑出最有機會噴發的幣種（最多 10 檔，寧缺勿濫）
                    let top100Pool = globalData.slice(0, 100);
                    let qualifiedCoins = top100Pool
                        .filter(coin => coin.change24h >= 3.0 && !expiredSignals[coin.symbol])
                        .map(coin => {
                            let fr = globalFundingRate[coin.symbol] !== undefined ? globalFundingRate[coin.symbol] : 0.01;
                            let burstScore = getBurstScore(coin, coin.change24h * 0.25, fr);
                            return { coin, burstScore };
                        })
                        .sort((a, b) => b.burstScore - a.burstScore);

                    let selectedCoins = qualifiedCoins.slice(0, 10).map(x => x.coin);
                    let selectedSymbols = selectedCoins.map(c => c.symbol);

                    Object.keys(activeSignals).forEach(sym => {
                        if (!selectedSymbols.includes(sym) && (activeSignals[sym].maxGain || 0) < 1.0) {
                            delete activeSignals[sym];
                        }
                    });

                    selectedCoins.forEach(coin => {
                        let sym = coin.symbol;
                        if (!activeSignals[sym]) {
                            let timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                            if (!alertCounts[sym]) {
                                alertCounts[sym] = { count: 1, lastTime: now };
                            } else {
                                alertCounts[sym].count += 1;
                                alertCounts[sym].lastTime = now;
                            }

                            // 初次捕捉時同步起跑動能，避免剛進入顯示 0.00%
                            let syncedInitGain = Math.max(0.15, parseFloat((coin.change24h * 0.1).toFixed(2)));
                            activeSignals[sym] = {
                                symbol: sym,
                                firstAlertPrice: coin.lastPrice,
                                alertTime: timeString,
                                initialMomentum: syncedInitGain,
                                maxGain: syncedInitGain,
                                score: coin.change24h.toFixed(2),
                                alertCount: alertCounts[sym].count
                            };
                        } else if (alertCounts[sym]) {
                            activeSignals[sym].alertCount = alertCounts[sym].count;
                        }
                    });

                    let activeKeys = Object.keys(activeSignals);
                    if (activeKeys.length > 10) {
                        activeKeys.sort((a, b) => {
                            let cA = globalData.find(c => c.symbol === a) || { change24h: 0, lastPrice: 1 };
                            let cB = globalData.find(c => c.symbol === b) || { change24h: 0, lastPrice: 1 };
                            let diffA = ((cA.lastPrice - activeSignals[a].firstAlertPrice) / activeSignals[a].firstAlertPrice) * 100;
                            let diffB = ((cB.lastPrice - activeSignals[b].firstAlertPrice) / activeSignals[b].firstAlertPrice) * 100;
                            return getBurstScore(cB, diffB, globalFundingRate[b] || 0) - getBurstScore(cA, diffA, globalFundingRate[a] || 0);
                        });
                        for (let i = 10; i < activeKeys.length; i++) {
                            delete activeSignals[activeKeys[i]];
                        }
                    }

                    saveSignals();
                    renderView();
                    updateSyncLabel(json.updated_at);
                    if (currentTab === 'monthly') renderMonthlyStats();
                }
            } catch (err) {
                console.error("BingX 數據載入錯誤:", err);
                const el = document.getElementById('sync-status');
                if (el) el.textContent = "同步狀態：連線重試中...";
            } finally {
                isFetching = false;
            }
        }

        function renderView() {
            let activeHtml = '', activeKeys = Object.keys(activeSignals);
            if (activeKeys.length === 0) {
                activeHtml = '<div class="loading">正在從前 100 大漲幅榜掃描高噴發標的，請稍候...</div>';
            } else {
                // 4-5 星強勢標的優先置頂排序
                activeKeys.sort((a, b) => {
                    let coinA = globalData.find(c => c.symbol === a) || { change24h: parseFloat(activeSignals[a].score || 0), lastPrice: activeSignals[a].firstAlertPrice };
                    let coinB = globalData.find(c => c.symbol === b) || { change24h: parseFloat(activeSignals[b].score || 0), lastPrice: activeSignals[b].firstAlertPrice };
                    let pA = parseFloat(activeSignals[a].firstAlertPrice) || 1;
                    let pB = parseFloat(activeSignals[b].firstAlertPrice) || 1;
                    let rawDiffA = ((coinA.lastPrice - pA) / pA) * 100;
                    let rawDiffB = ((coinB.lastPrice - pB) / pB) * 100;
                    let effDiffA = Math.abs(rawDiffA) < 0.01 ? (activeSignals[a].initialMomentum || 0.15) : rawDiffA;
                    let effDiffB = Math.abs(rawDiffB) < 0.01 ? (activeSignals[b].initialMomentum || 0.15) : rawDiffB;
                    return getBurstScore(coinB, effDiffB, globalFundingRate[b] || 0) - getBurstScore(coinA, effDiffA, globalFundingRate[a] || 0);
                });

                activeKeys.forEach(k => {
                    let sig = activeSignals[k];
                    let coinData = globalData.find(c => c.symbol === sig.symbol) || { lastPrice: sig.firstAlertPrice, change24h: parseFloat(sig.score || 0) };
                    let currentPrice = parseFloat(coinData.lastPrice);
                    let firstAlert = parseFloat(sig.firstAlertPrice);
                    let rawDiff = ((currentPrice - firstAlert) / firstAlert) * 100;
                    let diffVal = Math.abs(rawDiff) < 0.01 ? parseFloat(sig.initialMomentum || 0.15) : rawDiff;
                    let diffPct = diffVal.toFixed(2);
                    let isDiffPos = diffVal >= 0;

                    let priceStr = currentPrice < 1 ? currentPrice.toFixed(4) : currentPrice.toFixed(2);
                    let alertPriceStr = firstAlert < 1 ? firstAlert.toFixed(4) : firstAlert.toFixed(2);
                    let frVal = globalFundingRate[sig.symbol] !== undefined ? globalFundingRate[sig.symbol] : 0.01;
                    let fundingRate = frVal.toFixed(4);
                    let isFundingPos = frVal >= 0;

                    let burstScore = getBurstScore(coinData, diffPct, frVal);
                    let stars = getRecommendationStars(burstScore);
                    let count = sig.alertCount || 1;
                    let repeatBadge = count >= 2 ? `<span class="badge-repeat">⚠️ 第 ${count} 次警報</span>` : '';
                    let displayMaxGain = Math.max(parseFloat(sig.maxGain || 0), diffVal).toFixed(2);

                    activeHtml += `
                        <div class="card">
                            <div class="row" style="margin-bottom: 6px;">
                                <div>
                                    <span class="badge-active">🚀 前100噴發 · 24h: +${coinData.change24h.toFixed(2)}%</span>
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
                                <div class="metric-item" style="grid-column: span 2;">最高盈利記錄：<b style="color: var(--accent);">+${displayMaxGain}%</b></div>
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

        function renderMonthlyStats() {
            let monthsData = {};
            let allItems = Object.assign({}, activeSignals, expiredSignals);

            Object.keys(allItems).forEach(k => {
                let item = allItems[k];
                let m = item.date || new Date().toISOString().slice(0, 7);
                if (!monthsData[m]) {
                    monthsData[m] = { total: 0, p100: 0, p50_100: 0, p20_50: 0, p10_20: 0, stopLoss: 0 };
                }
                monthsData[m].total += 1;
                let maxG = parseFloat(item.maxGain || 0);
                if (item.reason && item.reason.includes("止損")) {
                    monthsData[m].stopLoss += 1;
                }
                if (maxG >= 100) monthsData[m].p100 += 1;
                else if (maxG >= 50) monthsData[m].p50_100 += 1;
                else if (maxG >= 20) monthsData[m].p20_50 += 1;
                else if (maxG >= 10) monthsData[m].p10_20 += 1;
            });

            let html = '';
            let sortedMonths = Object.keys(monthsData).sort().reverse();
            if (sortedMonths.length === 0) {
                html = '<div class="loading">目前尚無足夠的統計數據...</div>';
            } else {
                sortedMonths.forEach(m => {
                    let d = monthsData[m];
                    html += `
                        <div class="monthly-card">
                            <div class="monthly-title">📅 統計月份：${m}</div>
                            <div class="metrics-grid" style="grid-template-columns: 1fr;">
                                <div>📌 總警報數：<b>${d.total} 個</b></div>
                                <div>🚀 盈利 > 100%：<b class="positive">${d.p100} 個</b></div>
                                <div>📈 盈利 50% - 100%：<b class="positive">${d.p50_100} 個</b></div>
                                <div>📊 盈利 20% - 50%：<b class="positive">${d.p20_50} 個</b></div>
                                <div>⭐ 盈利 10% - 20%：<b class="positive">${d.p10_20} 個</b></div>
                                <div>🛑 止損 (-2%)：<b class="negative">${d.stopLoss} 個</b></div>
                            </div>
                        </div>`;
                });
            }
            document.getElementById('monthly-feed').innerHTML = html;
        }

        // 每次點進瀏覽器、切回分頁或從上一頁返回時，立刻強制同步最新資料
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) fetchBingXData(true);
        });
        window.addEventListener('pageshow', () => fetchBingXData(true));
        window.addEventListener('focus', () => fetchBingXData(true));

        fetchBingXData(true);
        setInterval(() => fetchBingXData(false), 8000);
    </script>
</body>
</html>
"""


class MyHandler(http.server.SimpleHTTPRequestHandler):

  def do_GET(self):
    clean_path = self.path.split("?")[0]
    if clean_path == "/api/bingx":
      self.send_response(200)
      self.send_header("Content-type", "application/json; charset=utf-8")
      self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
      self.end_headers()
      self.wfile.write(json.dumps(bingx_cache).encode("utf-8"))
    else:
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
      self.end_headers()
      self.wfile.write(html_content.encode("utf-8"))


if __name__ == "__main__":
  bg_thread = threading.Thread(target=fetch_bingx_background, daemon=True)
  bg_thread.start()

  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"🚀 BingX 前100強噴發追蹤伺服器已在 Port {PORT} 啟動！")
    httpd.serve_forever()
