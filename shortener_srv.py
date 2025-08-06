# shortener_srv.py
import os, json, time, sqlite3, string, random, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

DB_PATH   = os.getenv("SHORTENER_DB", "/tmp/shortener.sqlite3")
PORT      = int(os.getenv("SHORTENER_PORT", "8799"))
BASE_PATH = os.getenv("SHORTENER_BASE_PATH", "/u")  # 短链路径前缀
PUBLIC_BASE = os.getenv("SHORTENER_PUBLIC_BASE")     # 若设置，则返回对外可用的完整域名

def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS short_urls(
        code TEXT PRIMARY KEY,
        long_url TEXT NOT NULL,
        expire_at INTEGER NOT NULL
    );""")
    return conn

def _gen(n=8):
    import random
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))

def _now(): return int(time.time())

class Handler(BaseHTTPRequestHandler):
    server_version = "Shortener/1.0"
    
    def _json(self, status, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/shorten":
            self.send_error(404, "Not Found"); return
        
        ln = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(ln) or b"{}")
            long_url    = body["long_url"]
            expires_in  = int(body.get("expires_in", 3600))
        except Exception as e:
            self._json(400, {"error":"bad_request","detail":str(e)}); return
        
        code = _gen()
        expire_at = _now() + max(60, expires_in)
        with _conn() as c:
            try:
                c.execute("INSERT INTO short_urls(code,long_url,expire_at) VALUES(?,?,?)",
                          (code, long_url, expire_at))
            except sqlite3.IntegrityError:
                code = _gen()
                c.execute("INSERT INTO short_urls(code,long_url,expire_at) VALUES(?,?,?)",
                          (code, long_url, expire_at))
        
        # 计算短链：默认返回容器内可访问的 127.0.0.1:PORT
        if PUBLIC_BASE:
            short_url = PUBLIC_BASE.rstrip("/") + f"{BASE_PATH}/{code}"
        else:
            short_url = f"http://127.0.0.1:{PORT}{BASE_PATH}/{code}"
        
        self._json(200, {"code": code, "short_url": short_url})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith(BASE_PATH + "/"):
            self.send_error(404, "Not Found"); return
        
        code = parsed.path.split("/")[-1]
        with _conn() as c:
            row = c.execute("SELECT long_url,expire_at FROM short_urls WHERE code=?",(code,)).fetchone()
        
        if not row:
            self.send_error(404, "Short code not found"); return
        
        long_url, expire_at = row
        if _now() > expire_at:
            self.send_error(410, "Short URL expired"); return
        
        # 302 跳转（不代理、不改写、保留完整 query）
        self.send_response(302)
        self.send_header("Location", long_url)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

def start_shortener_in_background():
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print(f"🔗 Shortener service started on port {PORT}")
    return httpd
