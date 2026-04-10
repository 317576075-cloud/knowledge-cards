"""
沟通基本功 · 数据后台
用法：python server.py
访问：http://localhost:8899          → 卡片主页（用户看到的）
访问：http://localhost:8899/admin    → 点击数据后台（只有你知道）
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse

DATA_FILE = os.path.join(os.path.dirname(__file__), "clicks.json")
PORT = 8899

CATEGORY_LABELS = {"relation": "建立关系", "upward": "向上沟通", "lateral": "横向沟通"}
CATEGORY_COLORS = {"relation": "#ffd100", "upward": "#ff6b35", "lateral": "#4ecdc4"}


def load_clicks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_click(payload):
    clicks = load_clicks()
    clicks.append(payload)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(clicks, f, ensure_ascii=False, indent=2)


def build_admin_html():
    clicks = load_clicks()
    total = len(clicks)

    # 按卡片聚合
    card_map = defaultdict(lambda: {"count": 0, "title": "", "num": "", "category": "", "last": ""})
    cat_map = defaultdict(int)
    daily_map = defaultdict(int)

    for c in clicks:
        key = c.get("card", "")
        card_map[key]["count"] += 1
        card_map[key]["title"] = c.get("title", key)
        card_map[key]["num"] = c.get("num", "")
        card_map[key]["category"] = c.get("category", "")
        card_map[key]["last"] = c.get("ts", "")[:10]
        cat_map[c.get("category", "unknown")] += 1
        daily_map[c.get("ts", "")[:10]] += 1

    sorted_cards = sorted(card_map.values(), key=lambda x: -x["count"])
    sorted_days = sorted(daily_map.items())
    max_day = max((v for _, v in sorted_days), default=1)
    max_card = sorted_cards[0]["count"] if sorted_cards else 1

    # 分类统计块
    cat_blocks = ""
    for cat, cnt in cat_map.items():
        label = CATEGORY_LABELS.get(cat, cat)
        color = CATEGORY_COLORS.get(cat, "#ccc")
        cat_blocks += f"""
        <div class="stat-card" style="border-top:3px solid {color}">
          <div class="stat-num">{cnt}</div>
          <div class="stat-label">{label}</div>
        </div>"""

    # 卡片排行
    card_rows = ""
    for e in sorted_cards[:18]:
        color = CATEGORY_COLORS.get(e["category"], "#ccc")
        pct = round(e["count"] / max_card * 100)
        label = CATEGORY_LABELS.get(e["category"], e["category"])
        card_rows += f"""
        <div class="bar-row">
          <div class="bar-meta">
            <span class="bar-num">{e['num']}</span>
            <span class="bar-title">{e['title']}</span>
            <span class="bar-cat" style="color:{color}">{label}</span>
          </div>
          <div class="bar-wrap">
            <div class="bar-fill" style="width:{pct}%;background:{color}"></div>
            <span class="bar-count">{e['count']}</span>
          </div>
        </div>"""

    # 每日趋势
    day_rows = ""
    for day, cnt in sorted_days[-14:]:
        pct = round(cnt / max_day * 100)
        day_rows += f"""
        <div class="day-row">
          <div class="day-label">{day}</div>
          <div class="bar-wrap">
            <div class="bar-fill" style="width:{pct}%;background:#ffd100"></div>
            <span class="bar-count">{cnt}</span>
          </div>
        </div>"""

    if not day_rows:
        day_rows = '<div style="color:#666;font-size:13px;padding:16px 0">暂无数据</div>'
    if not card_rows:
        card_rows = '<div style="color:#666;font-size:13px;padding:16px 0">暂无数据</div>'

    unique_cards = len(card_map)
    unique_users_approx = total  # 每次点击算一次，无法区分用户

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>后台数据 · 沟通基本功</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #0d0d0d; color: #e0e0e0; min-height: 100vh; }}
  .header {{ background: #111; border-bottom: 1px solid #222; padding: 20px 40px; display: flex; align-items: center; justify-content: space-between; }}
  .header-title {{ font-size: 18px; font-weight: 700; color: #ffd100; letter-spacing: 0.05em; }}
  .header-sub {{ font-size: 12px; color: #555; margin-top: 4px; }}
  .refresh-btn {{ padding: 8px 16px; background: #1a1a1a; border: 1px solid #333; color: #888; font-size: 12px; cursor: pointer; border-radius: 4px; text-decoration: none; }}
  .refresh-btn:hover {{ border-color: #ffd100; color: #ffd100; }}
  .main {{ padding: 32px 40px; max-width: 1100px; }}
  .section-title {{ font-size: 11px; letter-spacing: 0.15em; text-transform: uppercase; color: #555; margin-bottom: 16px; margin-top: 40px; }}
  .stats-row {{ display: flex; gap: 12px; flex-wrap: wrap; }}
  .stat-card {{ background: #111; border: 1px solid #222; border-top: 3px solid #ffd100; padding: 20px 24px; min-width: 120px; flex: 1; }}
  .stat-num {{ font-size: 32px; font-weight: 900; color: #fff; line-height: 1; }}
  .stat-label {{ font-size: 11px; color: #555; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.08em; }}
  .panel {{ background: #111; border: 1px solid #222; padding: 24px; margin-top: 12px; }}
  .bar-row, .day-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }}
  .bar-meta {{ display: flex; align-items: center; gap: 8px; width: 260px; flex-shrink: 0; }}
  .bar-num {{ font-size: 11px; color: #555; width: 24px; }}
  .bar-title {{ font-size: 13px; color: #ccc; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .bar-cat {{ font-size: 11px; white-space: nowrap; }}
  .bar-wrap {{ flex: 1; background: #1a1a1a; height: 22px; position: relative; display: flex; align-items: center; }}
  .bar-fill {{ height: 100%; min-width: 2px; transition: width 0.3s; }}
  .bar-count {{ position: absolute; right: 8px; font-size: 12px; font-weight: 700; color: #fff; }}
  .day-label {{ font-size: 12px; color: #666; width: 100px; flex-shrink: 0; }}
  .empty {{ color: #444; font-size: 13px; padding: 20px 0; }}
  .ts {{ font-size: 11px; color: #444; margin-top: 4px; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="header-title">📊 沟通基本功 · 点击数据后台</div>
    <div class="header-sub">数据文件：clicks.json &nbsp;·&nbsp; 仅限内部查看</div>
  </div>
  <a class="refresh-btn" href="/admin">刷新</a>
</div>
<div class="main">

  <div class="section-title">总览</div>
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-num">{total}</div>
      <div class="stat-label">总点击次数</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{unique_cards}</div>
      <div class="stat-label">被点击卡片数</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{len(daily_map)}</div>
      <div class="stat-label">活跃天数</div>
    </div>
    {cat_blocks}
  </div>

  <div class="section-title">卡片点击排行</div>
  <div class="panel">{card_rows}</div>

  <div class="section-title">近 14 天每日趋势</div>
  <div class="panel">{day_rows}</div>

</div>
</body>
</html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_POST(self):
        if self.path == "/track":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                save_click(payload)
            except Exception:
                pass
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/admin":
            html = build_admin_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # 过滤掉 /track 的日志，避免刷屏
        if "/track" not in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"[OK] 服务已启动: http://localhost:{PORT}")
    print(f"[Admin] 后台数据: http://localhost:{PORT}/admin")
    print("按 Ctrl+C 停止\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
