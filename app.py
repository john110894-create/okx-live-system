from http.server import HTTPServer, BaseHTTPRequestHandler
import json

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OKX 即時爆發與大戶加倉追蹤系統 (雲端版)</title>
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
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 12px; }
        h1 { color: var(--accent); text-align: center; font-size: 1.3rem; margin: 10px 0 15px 0; }
        
        .status-bar { background: var(--card-bg); border: 1px solid var(--card-border); padding: 10px; border-radius: 10px; margin-bottom: 15px; font-size: 0.85rem; text-align: center; color: var(--text-sub); }
        
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
        .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; border-bottom: 1px solid var(--card-border); padding-bottom: 8px; }
        
        .coin-title { font-size: 1.15rem; font-weight: bold; color: #fff; display: flex; align-items: center; gap: 6px; }
        .coin-sub { font-size: 0.75rem; color: var(--text-sub); font-weight: normal; }
        .price-box { text-align: right; }
        .current-price { font-size: 1.2rem; font-weight: bold; color: #fff; }
        .price-change { font-size: 0.8rem; color: var(--green); }
        
        .badge-time { font-size: 0.75rem; background: rgba(14,203,129,0.15); color: var(--green); padding: 3px 8px; border-radius: 6px; margin-bottom: 8px; display: inline-block; font-weight: bold; }
        
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 8px; margin-top: 8px; }
        .label { color: var(--text-sub); font-size: 0.78rem; }
        .value { color: #fff; font-weight: 600; font-size: 0.85rem; }
        
        .tp-list { font-size: 0.8rem; color: var(--accent); line-height: 1.4; }
        .stoploss-val { color: var(--red); }
    </style>
</head>
<body>
    <h1>🚀 OKX 即時爆發與大戶加倉追蹤系統 (雲端版)</h1>
    
    <div class="status-bar">
        🟢 <strong>全市場掃描中</strong> • 警報發出後持續追蹤直到觸發止損
    </div>

    <!-- 卡片 1: BTW -->
    <div class="card">
        <div class="card-header">
            <div>
                <div class="coin-title">BTW <span class="coin-sub">OKX 永續</span></div>
                <div class="badge-time">⚡ 警報日期: 10/28 | 綜合分 +7.9分</div>
            </div>
            <div class="price-box">
                <div class="current-price">$1.74</div>
                <div class="price-change">追蹤動能: +28.49%</div>
            </div>
        </div>

        <div class="grid-2">
            <div>
                <span class="label">🛑 推薦止損位置</span><br>
                <span class="value stoploss-val">$1.28 (支撐下方)</span>
            </div>
            <div>
                <span class="label">⚠️ 止損觸發狀態</span><br>
                <span class="value" style="color:var(--green);">未觸發 (持續抱單)</span>
            </div>
        </div>

        <div class="grid-2" style="margin-top: 6px;">
            <div>
                <span class="label">🎯 推薦止盈點位</span><br>
                <div class="tp-list">
                    ① $1.50 (+10%)<br>
                    ② $1.70 (+25%)<br>
                    ③ $1.90 (+40%)
                </div>
            </div>
            <div>
                <span class="label">📈 12%up 後轉弱高點</span><br>
                <span class="value" style="color:var(--accent);">$1.82 (+33.8%)</span>
            </div>
        </div>

        <div style="margin-top: 8px; font-size: 0.8rem; color: var(--text-sub); background: rgba(255,170,0,0.08); padding: 6px 8px; border-radius: 6px;">
            💡 <strong>資金流向：</strong> 明確資金淨流入 (多頭主動加倉) | 狀態：動能正常，等待止盈或衰竭出場
        </div>
    </div>

    <!-- 卡片 2: BEAT -->
    <div class="card">
        <div class="card-header">
            <div>
                <div class="coin-title">BEAT <span class="coin-sub">OKX 永續</span></div>
                <div class="badge-time">⚡ 警報日期: 10/27 | 綜合分 +8.9分</div>
            </div>
            <div class="price-box">
                <div class="current-price">$0.0898</div>
                <div class="price-change" style="color:var(--red);">追蹤動能: +9.15%</div>
            </div>
        </div>

        <div class="grid-2">
            <div>
                <span class="label">🛑 推薦止損位置</span><br>
                <span class="value stoploss-val">$0.0790 (支撐下方)</span>
            </div>
            <div>
                <span class="label">⚠️ 止損觸發狀態</span><br>
                <span class="value stoploss-val">已觸發止損 (準備移除)</span>
            </div>
        </div>

        <div class="grid-2" style="margin-top: 6px;">
            <div>
                <span class="label">🎯 推薦止盈點位</span><br>
                <div class="tp-list">
                    ① $0.091 (+10%)<br>
                    ② $0.103 (+25%)<br>
                    ③ $0.115 (+40%)
                </div>
            </div>
            <div>
                <span class="label">📈 12%up 後轉弱高點</span><br>
                <span class="value">-</span>
            </div>
        </div>

        <div style="margin-top: 8px; font-size: 0.8rem; color: var(--text-sub); background: rgba(246,70,93,0.08); padding: 6px 8px; border-radius: 6px;">
            💡 <strong>資金流向：</strong> 價格推升但持倉減少 (空頭回補短多) | 狀態：已觸發止損出場
        </div>
    </div>

</body>
</html>
"""

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode("utf-8"))

def run():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, MyHandler)
    print("🚀 雲端伺服器已在 Port 8080 啟動...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
