from http.server import HTTPServer, BaseHTTPRequestHandler
import json

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OKX 即時爆發與大戶資金追蹤系統</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }
        h1 { color: #00ffcc; text-align: center; font-size: 22px; margin-bottom: 20px; }
        .card { background: #1e1e1e; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #00ffcc; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 14px; margin-top: 10px; }
        .label { color: #888; }
        .value { color: #fff; font-weight: bold; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-long { background: #00cc66; color: #000; }
        .badge-stoploss { background: #ff4d4d; color: #fff; }
        .badge-profit { background: #ffaa00; color: #000; }
    </style>
</head>
<body>
    <h1>🚀 OKX 爆發與資金追蹤看板</h1>
    
    <div class="card">
        <div><strong>BTCUSDT</strong> <span class="badge badge-long">持續追蹤中 (未止損)</span></div>
        <div class="grid">
            <span class="label">警報日期:</span> <span class="value">10/28</span>
            <span class="label">當前價格:</span> <span class="value">$68,500</span>
            <span class="label">推薦止損位置:</span> <span class="value" style="color:#ff4d4d;">$67,200 (支撐下)</span>
            <span class="label">止損狀態:</span> <span class="value">未觸發 (持續留在看板)</span>
            <span class="label">12%up後轉弱高點:</span> <span class="value" style="color:#ffaa00;">$74,500 (+14.2%)</span>
        </div>
    </div>

    <div class="card">
        <div><strong>ETHUSDT</strong> <span class="badge badge-stoploss">已觸發止損 (準備移除)</span></div>
        <div class="grid">
            <span class="label">警報日期:</span> <span class="value">10/27</span>
            <span class="label">當前價格:</span> <span class="value">$2,440</span>
            <span class="label">推薦止損位置:</span> <span class="value" style="color:#ff4d4d;">$2,450 (支撐下)</span>
            <span class="label">止損狀態:</span> <span class="badge badge-stoploss">已觸發</span>
            <span class="label">12%up後轉弱高點:</span> <span class="value">-</span>
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
