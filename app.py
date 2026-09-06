import os, json, time, requests, secrets, re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, render_template_string, session, redirect, flash, Response
from cryptography.fernet import Fernet
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# --- ENCRYPTION SETUP ---
MASTER_KEY = os.environ.get("ENCRYPT_KEY", Fernet.generate_key().decode())
cipher = Fernet(MASTER_KEY.encode())

# --- CREDENTIALS & CONSTANTS ---
GIST_ID = "39a77b43b3254947743843a91bffec39"
GIST_TOKEN = "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"
GIST_URL = f"https://api.github.com/gists/{GIST_ID}"
BACKUP_FILE = "backup.json"

DEFAULT_DB = {
    "admin_u": "admin", "admin_p": generate_password_hash("admin"), 
     "companies": {"ramfin": {"name": "RamFincorp", "tenant": "MMMWO", "broker": "ramfin", "active": True}},
    "services": {
        "pan_ramfin": {
            "name": "PAN Verify", "company": "ramfin", "type": "pan",
            "base_url": "https://loans-api.ramfincorp.com", "endpoint": "/customer_onboarding/pan-verification",
             "method": "POST", "headers": {"authorization": "Bearer {{token}}", "x-tenant": "{{tenant}}"},
             "body_template": {"panNumber": "{{pan}}"}, "query_params": {},
            "auth_token": "", "timeout": 10, "active": True, "health_status": True, "health_last_check": 0
        }
    },
     "keys": {}, "logs": [], "audit_logs": []
}

class GistDB:
    _cache, _ts = None, 0
    @classmethod
    def load(cls):
        if cls._cache and (time.time() - cls._ts < 5): return cls._cache
        try:
            pass
        except Exception:
            pass
            pass
            r = requests.get(GIST_URL, headers={"Authorization": f"token {GIST_TOKEN}"}, timeout=5)
            if r.status_code == 200:
                cls._cache = json.loads(r.json()['files']['db.json']['content'])
                cls._ts = time.time()
                with open(BACKUP_FILE, 'w') as f: json.dump(cls._cache, f)
                return cls._cache
        except Exception: pass
        
        try:
            pass
        except: return dict(DEFAULT_DB)

    @classmethod
    def save(cls, data):
        cls._cache, cls._ts = data, time.time()
        with open(BACKUP_FILE, 'w') as f: json.dump(data, f)
        try:
            requests.patch(
                GIST_URL,
                headers={"Authorization": f"token {GIST_TOKEN}"},
                json={"files": {"db.json": {"content": json.dumps(data)}}},
                timeout=5
            )
        except Exception:
            pass

        # --- HELPER FUNCTIONS ---
def enc_token(txt): 
    return cipher.encrypt(txt.encode()).decode() if txt else ""
    
def dec_token(txt): 
    try:
        return cipher.decrypt(txt.encode()).decode() if txt else ""
    except Exception:
        return ""

def now_ts(): return int(time.time())
def fmt_time(ts): return datetime.fromtimestamp(ts).strftime('%d %b %Y %H:%M:%S')

# --- RATE LIMITER ---
 _limits = {} 
def is_rate_limited(ident, max_req=60, window=60):
    now = time.time()
    reqs = [t for t in _limits.get(ident, []) if now - t < window]
    if len(reqs) >= max_req: return True
    reqs.append(now)
    _limits[ident] = reqs
    return False

# --- AUTH DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged'): 
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['POST'])
def login():
    db = GistDB.load()
    u, p = request.form.get('u',''), request.form.get('p','')
    db_p = db.get('admin_p', 'admin')
    valid = bcrypt.checkpw(p.encode(), db_p.encode()) if db_p.startswith('$2') else (p == db_p)
    
    if u == db.get('admin_u', 'admin') and valid:
        session['admin_logged'] = True
        session.permanent = True
        app.permanent_session_lifetime = 7200
    else:
        flash("Invalid Credentials!")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- COMPANY CRUD ---
def add_company(code, name, tenant, broker, active=True):
    db = GistDB.load()
     db.setdefault('companies', {})
    if code in db['companies']: return False
     db['companies'][code] = {"name": name, "tenant": tenant, "broker": broker, "active": bool(active)}
    GistDB.save(db)
    return True

def delete_company(code):
    db = GistDB.load()
    if code in db.get('companies', {}):
        del db['companies'][code]
        GistDB.save(db)
        return True
    return False

@app.route('/admin/company/add', methods=['POST'])
@login_required
def api_add_company():
    code, name = request.form.get('code', '').strip(), request.form.get('name', '').strip()
    if not code or not name:
        flash("Code and Name required!")
        return redirect('/')
    add_company(code, name, request.form.get('tenant', ''), request.form.get('broker', ''), request.form.get('active') == 'on')
    flash("Company added!")
    return redirect('/')

@app.route('/admin/company/delete/<code>')
@login_required
def api_delete_company(code):
    delete_company(code)
    flash("Company deleted.")
    return redirect('/')

# --- AUTO-CATCHER PARSER ---
import urllib.parse

def parse_raw_request(raw_text):
     res = {"method": "GET", "base_url": "", "endpoint": "", "headers": {}, "body_template": {}, "query_params": {}, "auth_token": ""}
    url_m = re.search(r"(https?://[^\s'\"\\\\]+)", raw_text)
    if url_m:
        parsed_u = urllib.parse.urlparse(url_m.group(1))
         res["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"
        res["endpoint"] = parsed_u.path
        res["query_params"] = {k: f"{{{{{k}}}}}" for k, v in urllib.parse.parse_qsl(parsed_u.query)} 

    meth_m = re.search(r"-X\s+([A-Z]+)", raw_text)
    if meth_m: res["method"] = meth_m.group(1)
    elif "-d " in raw_text or "--data" in raw_text: res["method"] = "POST"

    for h_m in re.finditer(r"-H\s+['\"]([^'\"]+)['\"]", raw_text):
        pts = h_m.group(1).split(":", 1)
        if len(pts) == 2:
            k, v = pts[0].strip().lower(), pts[1].strip()
            if k in ['cookie', 'user-agent'] or k.startswith('sec-'): continue
            if k == 'authorization' and v.lower().startswith('bearer '):
                res["auth_token"] = enc_token(v[7:].strip())
                 res["headers"][k] = "Bearer {{token}}"
            else: res["headers"][k] = v

    body_m = re.search(r"(?:--data-raw|-d|--data)\s+['\"](.*?)['\"]", raw_text, re.DOTALL)
    if body_m:
        try:
            pass
        except Exception:
            pass
            b_json = json.loads(body_m.group(1))
            for k, v in b_json.items():
                if isinstance(v, (str, int)): b_json[k] = f"{{{{{k}}}}}"
            res["body_template"] = b_json
        except: res["body_template"] = body_m.group(1)
    return res

# --- SERVICE CRUD ---
def add_service(code, service_data):
    db = GistDB.load()
     db.setdefault('services', {})
    if code in db['services']: return False
    service_data['health_status'], service_data['health_last_check'] = True, 0
    if 'auth_token' in service_data and not str(service_data['auth_token']).startswith('gAAAAA'):
        service_data['auth_token'] = enc_token(service_data['auth_token'])
    db['services'][code] = service_data
    GistDB.save(db)
    return True

def delete_service(code):
    db = GistDB.load()
    if code in db.get('services', {}):
        del db['services'][code]
        GistDB.save(db)
        return True
    return False

@app.route('/admin/service/add', methods=['POST'])
@login_required
def api_add_service():
    code = request.form.get('code', '').strip()
    data = {
        "name": request.form.get('name', ''), "company": request.form.get('company', ''),
        "type": request.form.get('type', 'pan'), "base_url": request.form.get('base_url', ''),
        "endpoint": request.form.get('endpoint', ''), "method": request.form.get('method', 'POST').upper(),
        "auth_token": request.form.get('auth_token', ''), "timeout": int(request.form.get('timeout', 10)),
        "active": request.form.get('active') == 'on'
    }
    for field in ['headers', 'body_template', 'query_params']:
        try:
            data[field] = json.loads(request.form.get(field, '{}'))
        except Exception:
            data[field] = {}
    add_service(code, data)
    flash("Service configured!")
    return redirect('/')

@app.route('/admin/service/delete/<code>')
@login_required
def api_delete_service(code):
    delete_service(code)
    flash("Service deleted.")
    return redirect('/')

@app.route('/admin/service/import', methods=['POST'])
@login_required
def api_import_service():
    raw_curl = request.form.get('curl_text', '')
    if not raw_curl: return jsonify({"status": False, "msg": "Blank request!"})
    try: return jsonify({"status": True, "data": parse_raw_request(raw_curl)})
    except Exception as e: return jsonify({"status": False, "msg": str(e)})

# --- KEY CRUD ---
def generate_key(owner, days, limit, assigned_services):
    db = GistDB.load()
     db.setdefault('keys', {})
     k = f"KEY_{secrets.token_hex(4).upper()}"
    db['keys'][k] = {
        'owner': owner, 'expiry': now_ts() + (int(days) * 86400), 'limit': int(limit),
        'used': 0, 'ok': 0, 'fail': 0, 'revoked': False,
        'assigned_services': assigned_services if isinstance(assigned_services, list) else [], 'daily_usage': {}
    }
    GistDB.save(db)
    return k

def toggle_key_revoke(key_id):
    db = GistDB.load()
    if key_id not in db.get('keys', {}): return False
    db['keys'][key_id]['revoked'] = not db['keys'][key_id].get('revoked', False)
    GistDB.save(db)
    return True

def delete_key(key_id):
    db = GistDB.load()
    if key_id in db.get('keys', {}):
        del db['keys'][key_id]
        GistDB.save(db)
        return True
    return False

@app.route('/admin/key/add', methods=['POST'])
@login_required
def api_add_key():
    generate_key(request.form.get('owner', '').strip(), request.form.get('days', 30), request.form.get('limit', 0), request.form.getlist('assigned_services'))
    flash("Key generated!")
    return redirect('/')

@app.route('/admin/key/toggle/<key_id>')
@login_required
def api_toggle_key(key_id):
    toggle_key_revoke(key_id)
    flash("Key status toggled!")
    return redirect('/')

@app.route('/admin/key/delete/<key_id>')
@login_required
def api_delete_key(key_id):
    delete_key(key_id)
    flash("Key deleted!")
    return redirect('/')

# --- PROXY ENDPOINT ---
def log_api(db, key, service, ok, msg):
    db['keys'][key]['used'] = db['keys'][key].get('used', 0) + 1
    db['keys'][key]['ok' if ok else 'fail'] = db['keys'][key].get('ok' if ok else 'fail', 0) + 1
     db.setdefault('logs', []).append({"ts": now_ts(), "key": key, "service": service, "ok": ok, "msg": msg})
    db['logs'] = db['logs'][-500:]
    GistDB.save(db)

@app.route('/api/verify', methods=['GET', 'POST'])
def api_verify():
    db = GistDB.load()
    k, srv = request.args.get('key'), request.args.get('service')
    if not k or not srv: return jsonify({"status": False, "msg": "Missing key or service"}), 400
    
    if is_rate_limited(request.remote_addr) or is_rate_limited(k):
        return jsonify({"status": False, "msg": "Rate limit exceeded"}), 429
        
     key_obj = db.get('keys', {}).get(k)
    if not key_obj or key_obj.get('revoked') or now_ts() > key_obj.get('expiry', 0): 
        return jsonify({"status": False, "msg": "Invalid/Revoked/Expired Key"}), 403
    if 0 < key_obj.get('limit', 0) <= key_obj.get('used', 0): 
        return jsonify({"status": False, "msg": "Quota Exhausted"}), 429
    if srv not in key_obj.get('assigned_services', []): 
        return jsonify({"status": False, "msg": "Unauthorized Service"}), 403
    
     srv_obj = db.get('services', {}).get(srv)
    if not srv_obj or not srv_obj.get('active'): return jsonify({"status": False, "msg": "Service Offline"}), 503
    
    req_data = request.args.to_dict()
    if request.is_json: req_data.update(request.json)
     cmp_obj = db.get('companies', {}).get(srv_obj.get('company', ''))
    
    def repl_vars(item):
        if isinstance(item, str):
            for p, v in req_data.items(): item = item.replace(f"{{{{{p}}}}}", str(v))
            if cmp_obj: item = item.replace("{{tenant}}", cmp_obj.get('tenant', ''))
            return item.replace("{{token}}", dec_token(srv_obj.get('auth_token', '')))
        elif isinstance(item, dict): return {k: repl_vars(v) for k, v in item.items()}
        elif isinstance(item, list): return [repl_vars(x) for x in item]
        return item
        
     url = f"{srv_obj['base_url'].rstrip('/')}/{srv_obj['endpoint'].lstrip('/')}"
    try:
        pass
    except Exception:
        pass
        r = requests.request(
            srv_obj['method'],
            url,
            headers=repl_vars(srv_obj.get('headers', {})),
            json=repl_vars(srv_obj.get('body_template', {})),
            params=repl_vars(srv_obj.get('query_params', {})),
            timeout=srv_obj.get('timeout', 10)
        )
        log_api(db, k, srv, r.ok, f"Upstream HTTP {r.status_code}")
        try: resp_data = r.json()
        except: resp_data = r.text
        return jsonify({"status": r.ok, "data": resp_data, "code": r.status_code})
    except Exception as e:
        log_api(db, k, srv, False, f"Error: {str(e)[:50]}")
        return jsonify({"status": False, "msg": "Upstream timeout/error"}), 502



# --- HTML TEMPLATE ---
HTML = '''<!DOCTYPE html>
<html lang="en"><head><title>Solo Proxy Panel</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
 :root{--bg:#0b0c10;--glass:rgba(31,40,51,0.6);--border:rgba(69,162,158,0.3);--neon:#66fcf1;--neon-dim:#45a29e;}
  body{background:var(--bg);color:#c5c6c7;font-family:'Segoe UI',sans-serif;margin:0;display:flex;height:100vh;overflow:hidden;}
  ::-webkit-scrollbar{width:6px;} ::-webkit-scrollbar-thumb{background:var(--neon-dim);border-radius:3px;}
  .glass{background:var(--glass);backdrop-filter:blur(12px);border:1px solid var(--border);border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.3);}
  .sidebar{width:260px;padding:20px;border-right:1px solid var(--border);display:flex;flex-direction:column;gap:10px;}
  .logo{font-size:24px;color:var(--neon);text-shadow:0 0 10px var(--neon);margin-bottom:20px;font-weight:bold;text-align:center;}
  .nav-item{padding:12px 15px;cursor:pointer;border-radius:8px;transition:0.3s;display:flex;align-items:center;gap:12px;}
  .nav-item:hover, .nav-item.active{background:rgba(102,252,241,0.1);color:var(--neon);box-shadow:inset 4px 0 0 var(--neon);}
  .main{flex:1;padding:25px;overflow-y:auto;position:relative;}
 # [Cleaned CSS] .topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:15px;border-bottom:1px solid var(--border);}
  .clock{font-size:18px;color:var(--neon);text-shadow:0 0 5px var(--neon);letter-spacing:1px;font-family:monospace;}
 # [Cleaned CSS] .grid-4{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:20px;}
  .card{padding:20px;transition:0.3s;} .card:hover{transform:translateY(-3px);box-shadow:0 0 15px rgba(102,252,241,0.2);border-color:var(--neon-dim);}
 # [Cleaned CSS] .tab{display:none;animation:fade 0.4s;} .tab.active{display:block;}
 @keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  .health-dot{width:12px;height:12px;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite;}
  .green{background:#5cb85c;box-shadow:0 0 10px #5cb85c;} .red{background:#d9534f;box-shadow:0 0 10px #d9534f;}
 @keyframes pulse{0%{transform:scale(0.95);opacity:0.8}50%{transform:scale(1.1);opacity:1}100%{transform:scale(0.95);opacity:0.8}}
  .table{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px;} .table th,.table td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05);}
  .btn{padding:8px 15px;border:none;border-radius:6px;cursor:pointer;color:#0b0c10;font-weight:bold;background:var(--neon);transition:0.3s;text-decoration:none;display:inline-block;}
  .btn:hover{box-shadow:0 0 12px var(--neon);} .btn-danger{background:rgba(217,83,79,0.2);color:#d9534f;border:1px solid #d9534f;} .btn-danger:hover{box-shadow:0 0 12px #d9534f;background:#d9534f;color:#fff;}
  input, select, textarea{width:100%;padding:10px;margin:8px 0 15px;background:rgba(0,0,0,0.4);border:1px solid var(--border);color:#fff;border-radius:6px;outline:none;}
  input:focus, textarea:focus{border-color:var(--neon);box-shadow:0 0 8px rgba(102,252,241,0.4);}
  .modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:99;justify-content:center;align-items:center;}
</style></head><body>
{% if not session.admin_logged %}
 <div style="margin:auto;width:350px;text-align:center;" class="glass card">
    <div class="logo"><i class="fa-solid fa-lock"></i> SYSTEM ADMIN</div>
    <form action="/login" method="POST">
        <input name="u" placeholder="Admin Username" required>
        <input type="password" name="p" placeholder="Master Password" required>
        <button class="btn" style="width:100%;">AUTHENTICATE</button>
    </form>
</div>
 {% else %}
<div class="sidebar glass">
    <div class="logo"><i class="fa-solid fa-microchip"></i> API CORE</div>
    <div class="nav-item active" onclick="showTab('dash', this)"><i class="fa-solid fa-chart-pie"></i> Dashboard</div>
    <div class="nav-item" onclick="showTab('comps', this)"><i class="fa-solid fa-building"></i> Companies</div>
    <div class="nav-item" onclick="showTab('srvs', this)"><i class="fa-solid fa-satellite-dish"></i> Services</div>
    <div class="nav-item" onclick="showTab('keys', this)"><i class="fa-solid fa-key"></i> Key Manager</div>
    <div class="nav-item" onclick="showTab('logs', this)"><i class="fa-solid fa-terminal"></i> Live Audit</div>
     <a href="/logout" class="nav-item" style="color:#d9534f;margin-top:auto;"><i class="fa-solid fa-power-off"></i> Disconnect</a>
</div>
<div class="main">
    <div class="topbar">
        <h2 id="page-title">Dashboard Overview</h2>
        <div class="clock" id="live-clock">--:--:--</div>
    </div>
    
    <div id="dash" class="tab active">
        <div class="grid-4">
              <div class="card glass"><h4><i class="fa-solid fa-building"></i> Partners</h4><h2 style="color:var(--neon)">{{ db.get('companies',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-network-wired"></i> Gateways</h4><h2 style="color:var(--neon)">{{ db.get('services',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-users"></i> Issued Keys</h4><h2 style="color:var(--neon)">{{ db.get('keys',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-bolt"></i> Logs Triggered</h4><h2 style="color:var(--neon)">{{ db.get('logs',[])|length }}</h2></div>
        </div>
         <h3 style="margin-top:20px;margin-bottom:15px;color:var(--neon-dim)"><i class="fa-solid fa-heart-pulse"></i> Service Health Monitor</h3>
        <div class="grid-4">
    @classmethod
    def load(cls):
        # 5 sec ka chota cache taaki GitHub rate limit hit na ho
        if cls._cache and (time.time() - cls._ts < 5): return cls._cache
        try:
            pass
        except Exception:
            pass
                 r = requests.get(GIST_URL, headers={"Authorization": f"token {GIST_TOKEN}"}, timeout=5)
            if r.status_code == 200:
                cls._cache = json.loads(r.json()['files']['db.json']['content'])
                cls._ts = time.time()
                with open(BACKUP_FILE, 'w') as f: json.dump(cls._cache, f)
                return cls._cache
        except Exception: pass
        
        try: # Network fail hone pe local file se fallback lenge
            with open(BACKUP_FILE, 'r') as f: return json.load(f)
        except: return dict(DEFAULT_DB)

    @classmethod
    def save(cls, data):
        cls._cache, cls._ts = data, time.time()
        with open(BACKUP_FILE, 'w') as f: json.dump(data, f) # Backup pehle
        try:
    requests.patch(GIST_URL, headers={"Authorization": f"token {GIST_TOKEN}"},
        json={"files": {"db.json": {"content": json.dumps(data)}}}, timeout=5)
        except Exception: pass

        # --- HELPER FUNCTIONS ---
def enc_token(txt): 
    # Token ko encrypt karne ke liye
    return cipher.encrypt(txt.encode()).decode() if txt else ""
    
def dec_token(txt): 
    try:
        return cipher.decrypt(txt.encode()).decode() if txt else ""
    except Exception:
        return ""

def now_ts(): return int(time.time())
def fmt_time(ts): return datetime.fromtimestamp(ts).strftime('%d %b %Y %H:%M:%S')

# --- RATE LIMITER (In-Memory) ---
 _limits = {} 
def is_rate_limited(ident, max_req=60, window=60):
    # Default 60 requests per minute ka limit check karta hai
    now = time.time()
    reqs = [t for t in _limits.get(ident, []) if now - t < window]
    if len(reqs) >= max_req: return True
    reqs.append(now)
    _limits[ident] = reqs
    return False

# --- AUTH DECORATOR ---
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged'): 
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ROUTES ---

@app.route('/login', methods=['POST'])
def login():
    db = GistDB.load()
    u, p = request.form.get('u',''), request.form.get('p','')
    db_p = db.get('admin_p', 'admin')
    
    # Bcrypt support with plain-text fallback for initial raw setup
    valid = bcrypt.checkpw(p.encode(), db_p.encode()) if db_p.startswith('$2') else (p == db_p)
    
    if u == db.get('admin_u', 'admin') and valid:
        session['admin_logged'] = True
        session.permanent = True
        app.permanent_session_lifetime = 7200 # 2 ghante ka session timeout
    else:
        flash("Invalid Credentials!")
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- COMPANY CRUD BACKEND ---
# Companies manage karne ke core functions. Ye sidha DB (Gist) se interact karte hain.

def get_companies():
    return GistDB.load().get('companies', {})

def get_company(code):
    return get_companies().get(code)

def add_company(code, name, tenant, broker, active=True):
    db = GistDB.load()
     db.setdefault('companies', {})
    if code in db['companies']: 
        return False # Code pehle se hai, duplicate nahi banayenge
    db['companies'][code] = {
        "name": name, "tenant": tenant, "broker": broker, "active": bool(active)
    }
    GistDB.save(db)
    return True

def edit_company(code, name, tenant, broker, active):
    db = GistDB.load()
    if code not in db.get('companies', {}): 
        return False # Company mili nahi
    db['companies'][code].update({
        "name": name, "tenant": tenant, "broker": broker, "active": bool(active)
    })
    GistDB.save(db)
    return True

def delete_company(code):
    db = GistDB.load()
    if code in db.get('companies', {}):
        del db['companies'][code]
        GistDB.save(db) # Delete karne ke baad Gist pe sync karega
        return True
    return False

# --- COMPANY CRUD API ROUTES ---
# Dashboard UI se aane wale company forms ko handle karne ke routes

@app.route('/admin/company/add', methods=['POST'])
@login_required
def api_add_company():
    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    tenant = request.form.get('tenant', '').strip()
    broker = request.form.get('broker', '').strip()
    active = request.form.get('active') == 'on'
    
    if not code or not name:
        flash("Code and Name are required!")
        return redirect('/')
        
    if add_company(code, name, tenant, broker, active):
         flash(f"Company '{name}' added successfully!")
    else:
        flash("Company code already exists!")
    return redirect('/')

@app.route('/admin/company/edit/<code>', methods=['POST'])
@login_required
def api_edit_company(code):
    name = request.form.get('name', '').strip()
    tenant = request.form.get('tenant', '').strip()
    broker = request.form.get('broker', '').strip()
    active = request.form.get('active') == 'on'
    
    if edit_company(code, name, tenant, broker, active):
         flash(f"Company '{code}' updated successfully!")
    else:
        flash("Failed to update. Company not found.")
    return redirect('/')

@app.route('/admin/company/delete/<code>')
@login_required
def api_delete_company(code):
    # Ek click me delete karne ka route
    if delete_company(code):
         flash(f"Company '{code}' deleted.")
    else:
        flash("Company not found.")
    return redirect('/')

# --- AUTO-CATCHER PARSER (STAR FEATURE) ---
import urllib.parse

def parse_raw_request(raw_text):
    # cURL command ko parse karke Gateway service format me convert karne ke liye
     res = {"method": "GET", "base_url": "", "endpoint": "", "headers": {}, "body_template": {}, "query_params": {}, "auth_token": ""}
    
    # 1. URL extract karo (Base URL, Endpoint, Query Params)
    url_m = re.search(r"(https?://[^\s'\"\\\\]+)", raw_text)
    if url_m:
        parsed_u = urllib.parse.urlparse(url_m.group(1))
         res["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"
        res["endpoint"] = parsed_u.path
        qs = urllib.parse.parse_qsl(parsed_u.query)
         # Query values ko smart dynamically replace kar do (e.g. ?pan=ABC -> ?pan={{pan}})
        res["query_params"] = {k: f"{{{{{k}}}}}" for k, v in qs} 

    # 2. HTTP Method dhoondo
    meth_m = re.search(r"-X\s+([A-Z]+)", raw_text)
    if meth_m: res["method"] = meth_m.group(1)
    elif "-d " in raw_text or "--data" in raw_text: res["method"] = "POST"

    # 3. Headers parse karo aur faltu (cookie/sec) ignore karo
    for h_m in re.finditer(r"-H\s+['\"]([^'\"]+)['\"]", raw_text):
        pts = h_m.group(1).split(":", 1)
        if len(pts) == 2:
            k, v = pts[0].strip().lower(), pts[1].strip()
            if k in ['cookie', 'user-agent'] or k.startswith('sec-'): continue
            
             # Token mila toh encrypt karke save karlo, payload me {{token}} daal do
            if k == 'authorization' and v.lower().startswith('bearer '):
                res["auth_token"] = enc_token(v[7:].strip())
                 res["headers"][k] = "Bearer {{token}}"
            else:
                res["headers"][k] = v

    # 4. Body JSON extract karo aur smart variables setup karo
    body_m = re.search(r"(?:--data-raw|-d|--data)\s+['\"](.*?)['\"]", raw_text, re.DOTALL)
    if body_m:
        try:
            pass
        except Exception:
            pass
            b_json = json.loads(body_m.group(1))
            for k, v in b_json.items():
                if isinstance(v, (str, int)): b_json[k] = f"{{{{{k}}}}}"
            res["body_template"] = b_json
        except: res["body_template"] = body_m.group(1)
        
    return res

# --- SERVICE CRUD BACKEND ---
# Upstream APIs (Services) ko manage karne ki logic

def get_services():
    return GistDB.load().get('services', {})

def get_service(code):
    return get_services().get(code)

def add_service(code, service_data):
    db = GistDB.load()
     db.setdefault('services', {})
    if code in db['services']: 
        return False # Service code pehle se hai
    
    # Default health monitoring details daal rahe hain
    service_data['health_status'] = True
    service_data['health_last_check'] = 0
    
    # Raw token aya hai toh usko Fernet se encrypt kar do (gAAAAA se pehchan hoti hai)
    if 'auth_token' in service_data and not str(service_data['auth_token']).startswith('gAAAAA'):
        service_data['auth_token'] = enc_token(service_data['auth_token'])
        
    db['services'][code] = service_data
    GistDB.save(db)
    return True

def edit_service(code, service_data):
    db = GistDB.load()
    if code not in db.get('services', {}): return False
    
    # Naya token mila toh encrypt karo, warna database ka purana token hi rehne do
    if service_data.get('auth_token') and not str(service_data['auth_token']).startswith('gAAAAA'):
        service_data['auth_token'] = enc_token(service_data['auth_token'])
    else:
        service_data['auth_token'] = db['services'][code].get('auth_token', '')
        
    # Monitoring variables wahi purane retain karenge
    service_data['health_status'] = db['services'][code].get('health_status', True)
    service_data['health_last_check'] = db['services'][code].get('health_last_check', 0)
    
    db['services'][code].update(service_data)
    GistDB.save(db)
    return True

def delete_service(code):
    db = GistDB.load()
    if code in db.get('services', {}):
        del db['services'][code]
        GistDB.save(db)
        return True
    return False

# --- SERVICE CRUD API ROUTES ---

@app.route('/admin/service/add', methods=['POST'])
@login_required
def api_add_service():
    code = request.form.get('code', '').strip()
    data = {
        "name": request.form.get('name', ''),
        "company": request.form.get('company', ''),
        "type": request.form.get('type', 'pan'),
        "base_url": request.form.get('base_url', ''),
        "endpoint": request.form.get('endpoint', ''),
        "method": request.form.get('method', 'POST').upper(),
        "auth_token": request.form.get('auth_token', ''),
        "timeout": int(request.form.get('timeout', 10)),
        "active": request.form.get('active') == 'on'
    }
    
    # JSON strings ko dict me convert kar rahe hain UI form se aate waqt
    for field in ['headers', 'body_template', 'query_params']:
        try:
            data[field] = json.loads(request.form.get(field, '{}'))
        except Exception:
            data[field] = {}
    if add_service(code, data):
         flash(f"Service '{code}' configured successfully!")
    else:
        flash("Service code already exists!")
    return redirect('/')

@app.route('/admin/service/delete/<code>')
@login_required
def api_delete_service(code):
    if delete_service(code):
         flash(f"Service '{code}' deleted.")
    else:
        flash("Service not found.")
    return redirect('/')

# --- AUTO-CATCHER API ENDPOINT ---
@app.route('/admin/service/import', methods=['POST'])
@login_required
def api_import_service():
    # cURL paste modal se UI directly is endpoint ko hit karega
    raw_curl = request.form.get('curl_text', '')
    if not raw_curl: 
        return jsonify({"status": False, "msg": "Blank request!"})
    
    try:
        parsed_data = parse_raw_request(raw_curl)
        return jsonify({"status": True, "data": parsed_data})
    except Exception as e:
        return jsonify({"status": False, "msg": f"Parsing Failed: {str(e)}"})

# --- KEY CRUD BACKEND ---
# Client API Keys ko manage karne ki functions (generate, edit, assign, revoke)

def get_keys():
    return GistDB.load().get('keys', {})

def generate_key(owner, days, limit, assigned_services):
    db = GistDB.load()
     db.setdefault('keys', {})
    
    # 8 character ka secure random key generate kar rahe hain
     k = f"KEY_{secrets.token_hex(4).upper()}"
    expiry = now_ts() + (int(days) * 86400)
    
    db['keys'][k] = {
        'owner': owner, 'expiry': expiry, 'limit': int(limit),
        'used': 0, 'ok': 0, 'fail': 0, 'revoked': False,
        'assigned_services': assigned_services if isinstance(assigned_services, list) else [],
         'daily_usage': {}
    }
    GistDB.save(db)
    return k

def edit_key(key_id, owner, limit, assigned_services):
    db = GistDB.load()
    if key_id not in db.get('keys', {}): return False
    
    db['keys'][key_id]['owner'] = owner
    db['keys'][key_id]['limit'] = int(limit)
    db['keys'][key_id]['assigned_services'] = assigned_services if isinstance(assigned_services, list) else []
    GistDB.save(db)
    return True

def toggle_key_revoke(key_id):
    db = GistDB.load()
    if key_id not in db.get('keys', {}): return False
    
    # Revoke hai toh Active karo, Active hai toh Revoke karo
    db['keys'][key_id]['revoked'] = not db['keys'][key_id].get('revoked', False)
    GistDB.save(db)
    return True

def extend_key(key_id, extra_days):
    db = GistDB.load()
    if key_id not in db.get('keys', {}): return False
    
    curr_exp = db['keys'][key_id].get('expiry', now_ts())
    # Agar pehle hi expire ho chuka hai, toh aaj ke din se extend karenge
    if curr_exp < now_ts(): curr_exp = now_ts()
        
    db['keys'][key_id]['expiry'] = curr_exp + (int(extra_days) * 86400)
    GistDB.save(db)
    return True

def delete_key(key_id):
    db = GistDB.load()
    if key_id in db.get('keys', {}):
        del db['keys'][key_id]
        GistDB.save(db)
        return True
    return False

# --- KEY CRUD API ROUTES ---
# Dashboard se Client Keys ko control karne ke routes

@app.route('/admin/key/add', methods=['POST'])
@login_required
def api_add_key():
    owner = request.form.get('owner', '').strip()
    days = request.form.get('days', 30)
    limit = request.form.get('limit', 0)
    # Form se multi-select checkboxes (assigned services) aayenge
    assigned = request.form.getlist('assigned_services') 
    
    if not owner:
        flash("Client name is required!")
    else:
        k = generate_key(owner, days, limit, assigned)
         flash(f"New Key Generated Successfully: {k}")
    return redirect('/')

@app.route('/admin/key/edit/<key_id>', methods=['POST'])
@login_required
def api_edit_key(key_id):
    owner = request.form.get('owner', '').strip()
    limit = request.form.get('limit', 0)
    assigned = request.form.getlist('assigned_services')
    
    if edit_key(key_id, owner, limit, assigned):
         flash(f"Key {key_id} config updated!")
    else:
        flash("Failed to update key!")
    return redirect('/')

@app.route('/admin/key/extend/<key_id>', methods=['POST'])
@login_required
def api_extend_key(key_id):
    extra_days = request.form.get('extra_days', 30)
    if extend_key(key_id, extra_days):
         flash(f"Key {key_id} validity extended by {extra_days} days!")
    else:
        flash("Key not found!")
    return redirect('/')

@app.route('/admin/key/toggle/<key_id>')
@login_required
def api_toggle_key(key_id):
    # Ek click me Revoke/Unrevoke karne ke liye
    if toggle_key_revoke(key_id):
        flash(f"Status toggled for {key_id}!")
    return redirect('/')

@app.route('/admin/key/delete/<key_id>')
@login_required
def api_delete_key(key_id):
    if delete_key(key_id):
         flash(f"Key {key_id} deleted permanently!")
    return redirect('/')

# --- MAIN PROXY ENDPOINT (API GATEWAY) ---

def log_api(db, key, service, ok, msg):
    # Stats aur logs update karne ke liye
    db['keys'][key]['used'] = db['keys'][key].get('used', 0) + 1
    db['keys'][key]['ok' if ok else 'fail'] = db['keys'][key].get('ok' if ok else 'fail', 0) + 1
    today = datetime.fromtimestamp(now_ts()).strftime('%Y-%m-%d')
     db['keys'][key].setdefault('daily_usage', {})
    db['keys'][key]['daily_usage'][today] = db['keys'][key]['daily_usage'].get(today, 0) + 1
    
     db.setdefault('logs', []).append({"ts": now_ts(), "key": key, "service": service, "ok": ok, "msg": msg})
    db['logs'] = db['logs'][-500:] # Aakhri 500 logs hi rakhenge memory save karne ke liye
    GistDB.save(db)

@app.route('/api/verify', methods=['GET', 'POST'])
def api_verify():
    db = GistDB.load()
    k, srv = request.args.get('key'), request.args.get('service')
    if not k or not srv: return jsonify({"status": False, "msg": "Missing key or service"}), 400
    
    # Rate Limiting: 60 req/min per IP aur per Key
    if is_rate_limited(request.remote_addr) or is_rate_limited(k):
        return jsonify({"status": False, "msg": "Rate limit exceeded (60/min)"}), 429
        
     key_obj = db.get('keys', {}).get(k)
    if not key_obj: return jsonify({"status": False, "msg": "Invalid Key"}), 401
    if key_obj.get('revoked'): return jsonify({"status": False, "msg": "Key Revoked"}), 403
    if now_ts() > key_obj.get('expiry', 0): return jsonify({"status": False, "msg": "Key Expired"}), 403
    if 0 < key_obj.get('limit', 0) <= key_obj.get('used', 0): return jsonify({"status": False, "msg": "Quota Exhausted"}), 429
    if srv not in key_obj.get('assigned_services', []): return jsonify({"status": False, "msg": "Unauthorized Service for this Key"}), 403
    
     srv_obj = db.get('services', {}).get(srv)
    if not srv_obj or not srv_obj.get('active'): return jsonify({"status": False, "msg": "Service Offline"}), 503
    
    # User input arguments + JSON body
    req_data = request.args.to_dict()
    if request.is_json: req_data.update(request.json)
     cmp_obj = db.get('companies', {}).get(srv_obj.get('company', ''))
    
    # Dynamic Template Builder
    def repl_vars(item):
        if isinstance(item, str):
            for p, v in req_data.items(): item = item.replace(f"{{{{{p}}}}}", str(v))
            if cmp_obj: item = item.replace("{{tenant}}", cmp_obj.get('tenant', ''))
            return item.replace("{{token}}", dec_token(srv_obj.get('auth_token', '')))
        elif isinstance(item, dict): return {k: repl_vars(v) for k, v in item.items()}
        elif isinstance(item, list): return [repl_vars(x) for x in item]
        return item
        
     url = f"{srv_obj['base_url'].rstrip('/')}/{srv_obj['endpoint'].lstrip('/')}"
    try:
        pass
    except Exception:
        pass
             r = requests.request(srv_obj['method'], url, headers=repl_vars(srv_obj.get('headers', {})),
                              json=repl_vars(srv_obj.get('body_template', {})), params=repl_vars(srv_obj.get('query_params', {})), 
                             timeout=srv_obj.get('timeout', 10))
         log_api(db, k, srv, r.ok, f"Upstream HTTP {r.status_code}")
        try: resp_data = r.json()
        except: resp_data = r.text
        return jsonify({"status": r.ok, "data": resp_data, "code": r.status_code})
    except Exception as e:
         log_api(db, k, srv, False, f"Error: {str(e)[:50]}")
        return jsonify({"status": False, "msg": "Upstream error or timeout"}), 502

# --- HEALTH CHECK SCHEDULER ---
# Har 30 second me active services ko ping karke unki health (Green/Red) check karne ka system
from apscheduler.schedulers.background import BackgroundScheduler

def ping_services():
    db = GistDB.load()
     services = db.get('services', {})
    updated = False
    now = now_ts()
    
    for code, srv in services.items():
        if not srv.get('active'): 
            continue # Inactive services ko faltu ping nahi karenge
        
        url = srv.get('base_url', '')
        if not url: continue
        
        try:
            pass
        except Exception:
            pass
            # Sirf base_url pe lightweight GET request (5 sec timeout) taaki thread hang na ho
            r = requests.get(url, timeout=5)
            # Agar 500+ status code aaya matlab upstream server crash hai
            is_healthy = r.status_code < 500 
        except Exception:
            is_healthy = False
            
        # Agar status change hua hai, ya 5 minute se update nahi hua, toh save karo
        if srv.get('health_status') != is_healthy or (now - srv.get('health_last_check', 0) > 300):
            srv['health_status'] = is_healthy
            srv['health_last_check'] = now
            updated = True
            
    if updated:
        GistDB.save(db)

# Scheduler setup karo (Background me chalega bina main server ko slow kiye)
scheduler = BackgroundScheduler()
scheduler.add_job(func=ping_services, trigger="interval", seconds=30)
scheduler.start()

'''
# --- HTML TEMPLATE (PART 12: Base UI & Dashboard) ---
HTML = '''<!DOCTYPE html>
<html lang="en"><head><title>Solo Proxy Panel</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
 :root{--bg:#0b0c10;--glass:rgba(31,40,51,0.6);--border:rgba(69,162,158,0.3);--neon:#66fcf1;--neon-dim:#45a29e;}
  body{background:var(--bg);color:#c5c6c7;font-family:'Segoe UI',sans-serif;margin:0;display:flex;height:100vh;overflow:hidden;}
  ::-webkit-scrollbar{width:6px;} ::-webkit-scrollbar-thumb{background:var(--neon-dim);border-radius:3px;}
  .glass{background:var(--glass);backdrop-filter:blur(12px);border:1px solid var(--border);border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.3);}
  .sidebar{width:260px;padding:20px;border-right:1px solid var(--border);display:flex;flex-direction:column;gap:10px;}
  .logo{font-size:24px;color:var(--neon);text-shadow:0 0 10px var(--neon);margin-bottom:20px;font-weight:bold;text-align:center;}
  .nav-item{padding:12px 15px;cursor:pointer;border-radius:8px;transition:0.3s;display:flex;align-items:center;gap:12px;}
  .nav-item:hover, .nav-item.active{background:rgba(102,252,241,0.1);color:var(--neon);box-shadow:inset 4px 0 0 var(--neon);}
  .main{flex:1;padding:25px;overflow-y:auto;position:relative;}
 # [Cleaned CSS] .topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:15px;border-bottom:1px solid var(--border);}
  .clock{font-size:18px;color:var(--neon);text-shadow:0 0 5px var(--neon);letter-spacing:1px;font-family:monospace;}
 # [Cleaned CSS] .grid-4{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:20px;}
  .card{padding:20px;transition:0.3s;} .card:hover{transform:translateY(-3px);box-shadow:0 0 15px rgba(102,252,241,0.2);border-color:var(--neon-dim);}
 # [Cleaned CSS] .tab{display:none;animation:fade 0.4s;} .tab.active{display:block;}
 @keyframes fade{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  .health-dot{width:12px;height:12px;border-radius:50%;display:inline-block;animation:pulse 1.5s infinite;}
  .green{background:#5cb85c;box-shadow:0 0 10px #5cb85c;} .red{background:#d9534f;box-shadow:0 0 10px #d9534f;}
 @keyframes pulse{0%{transform:scale(0.95);opacity:0.8}50%{transform:scale(1.1);opacity:1}100%{transform:scale(0.95);opacity:0.8}}
  .table{width:100%;border-collapse:collapse;margin-top:10px;font-size:14px;} .table th,.table td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05);}
  .btn{padding:8px 15px;border:none;border-radius:6px;cursor:pointer;color:#0b0c10;font-weight:bold;background:var(--neon);transition:0.3s;text-decoration:none;display:inline-block;}
  .btn:hover{box-shadow:0 0 12px var(--neon);} .btn-danger{background:rgba(217,83,79,0.2);color:#d9534f;border:1px solid #d9534f;} .btn-danger:hover{box-shadow:0 0 12px #d9534f;background:#d9534f;color:#fff;}
  input, select, textarea{width:100%;padding:10px;margin:8px 0 15px;background:rgba(0,0,0,0.4);border:1px solid var(--border);color:#fff;border-radius:6px;outline:none;}
  input:focus, textarea:focus{border-color:var(--neon);box-shadow:0 0 8px rgba(102,252,241,0.4);}
  .modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:99;justify-content:center;align-items:center;}
</style></head><body>
{% if not session.admin_logged %}
 <div style="margin:auto;width:350px;text-align:center;" class="glass card">
    <div class="logo"><i class="fa-solid fa-lock"></i> SYSTEM ADMIN</div>
    <form action="/login" method="POST">
        <input name="u" placeholder="Admin Username" required>
        <input type="password" name="p" placeholder="Master Password" required>
        <button class="btn" style="width:100%;">AUTHENTICATE</button>
    </form>
</div>
 {% else %}
<div class="sidebar glass">
    <div class="logo"><i class="fa-solid fa-microchip"></i> API CORE</div>
    <div class="nav-item active" onclick="showTab('dash', this)"><i class="fa-solid fa-chart-pie"></i> Dashboard</div>
    <div class="nav-item" onclick="showTab('comps', this)"><i class="fa-solid fa-building"></i> Companies</div>
    <div class="nav-item" onclick="showTab('srvs', this)"><i class="fa-solid fa-satellite-dish"></i> Services</div>
    <div class="nav-item" onclick="showTab('keys', this)"><i class="fa-solid fa-key"></i> Key Manager</div>
    <div class="nav-item" onclick="showTab('logs', this)"><i class="fa-solid fa-terminal"></i> Live Audit</div>
     <a href="/logout" class="nav-item" style="color:#d9534f;margin-top:auto;"><i class="fa-solid fa-power-off"></i> Disconnect</a>
</div>
<div class="main">
    <div class="topbar">
        <h2 id="page-title">Dashboard Overview</h2>
        <div class="clock" id="live-clock">--:--:--</div>
    </div>
    
    <div id="dash" class="tab active">
        <div class="grid-4">
              <div class="card glass"><h4><i class="fa-solid fa-building"></i> Partners</h4><h2 style="color:var(--neon)">{{ db.get('companies',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-network-wired"></i> Gateways</h4><h2 style="color:var(--neon)">{{ db.get('services',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-users"></i> Issued Keys</h4><h2 style="color:var(--neon)">{{ db.get('keys',{})|length }}</h2></div>
              <div class="card glass"><h4><i class="fa-solid fa-bolt"></i> Logs Triggered</h4><h2 style="color:var(--neon)">{{ db.get('logs',[])|length }}</h2></div>
        </div>
         <h3 style="margin-top:20px;margin-bottom:15px;color:var(--neon-dim)"><i class="fa-solid fa-heart-pulse"></i> Service Health Monitor</h3>
        <div class="grid-4">
            {% for code, srv in db.get('services', {}).items() %}
            <div class="card glass" style="border-left:4px solid {% if srv.health_status %}#5cb85c{% else %}#d9534f{% endif %};">
                 <h4 style="margin:0;">{{ srv.name }} <span class="health-dot {% if srv.health_status %}green{% else %}red{% endif %}" style="float:right"></span></h4>
                 <p style="font-size:11px;opacity:0.6;margin-top:8px;">Pinged: {{ fmt_time(srv.health_last_check) }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
'''

# --- HTML TEMPLATE (PART 13: Management Tabs & Modals) ---
HTML += '''
    <div id="comps" class="tab">
         <h3 style="color:var(--neon)">Company Management</h3>
# [Cleaned CSS]         <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div class="card glass" style="flex:1;min-width:250px;">
                <h4>Add New Company</h4>
                <form action="/admin/company/add" method="POST">
                    <input name="code" placeholder="Code (e.g., ramfin)" required>
                    <input name="name" placeholder="Full Name" required>
                    <input name="tenant" placeholder="Tenant ID">
                    <input name="broker" placeholder="Broker ID">
                    <label><input type="checkbox" name="active" checked> Active Provider</label>
                    <button class="btn" style="width:100%;margin-top:10px;">Save Company</button>
                </form>
            </div>
            <div class="card glass" style="flex:2;min-width:400px;overflow-x:auto;">
                <table class="table">
                    <tr><th>Code</th><th>Name</th><th>Tenant/Broker</th><th>Status</th><th>Action</th></tr>
                    {% for c_id, c in db.get('companies', {}).items() %}
                     <tr><td>{{ c_id }}</td><td>{{ c.name }}</td><td>{{ c.tenant }} / {{ c.broker }}</td>
                        <td><span class="health-dot {% if c.active %}green{% else %}red{% endif %}"></span></td>
                          <td><a href="/admin/company/delete/{{ c_id }}" class="btn btn-danger" style="padding:4px 8px;font-size:12px;">Del</a></td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>

    <div id="srvs" class="tab">
# [Cleaned CSS]         <div style="display:flex;justify-content:space-between;align-items:center;">
             <h3 style="color:var(--neon)">Dynamic Services</h3>
            <button class="btn" onclick="document.getElementById('curlModal').style.display='flex'"><i class="fa-solid fa-wand-magic-sparkles"></i> Auto-Catcher (cURL)</button>
        </div>
        <div class="card glass" style="margin-top:15px;overflow-x:auto;">
            <table class="table">
                <tr><th>Code</th><th>Name</th><th>Endpoint</th><th>Auth Token</th><th>Action</th></tr>
                {% for s_id, s in db.get('services', {}).items() %}
                 <tr><td>{{ s_id }}</td><td>{{ s.name }} ({{ s.company }})</td>
                     <td><span style="font-size:11px;opacity:0.8">{{ s.method }}</span> {{ s.endpoint }}</td>
                     <td>{% if s.auth_token %}<span style="color:var(--neon)"><i class="fa-solid fa-lock"></i> Encrypted</span>{% else %}None{% endif %}</td>
                      <td><a href="/admin/service/delete/{{ s_id }}" class="btn btn-danger" style="padding:4px 8px;font-size:12px;">Del</a></td></tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div id="keys" class="tab">
         <h3 style="color:var(--neon)">Key Control</h3>
# [Cleaned CSS]         <div style="display:flex;gap:20px;flex-wrap:wrap;">
            <div class="card glass" style="flex:1;min-width:250px;">
                <h4>Generate Key</h4>
                <form action="/admin/key/add" method="POST">
                    <input name="owner" placeholder="Client Name" required>
                    <input type="number" name="days" placeholder="Validity (Days)" value="30" required>
                    <input type="number" name="limit" placeholder="Max Hits (0=Unlimited)" value="1000" required>
# [Cleaned CSS]                     <label style="display:block;margin-bottom:5px;font-size:13px;">Assign Services:</label>
                     <div style="max-height:100px;overflow-y:auto;background:rgba(0,0,0,0.3);padding:10px;border-radius:6px;margin-bottom:15px;">
# [Cleaned CSS]                         {% for s_id, s in db.get('services', {}).items() %}<label style="display:block;font-size:12px;"><input type="checkbox" name="assigned_services" value="{{ s_id }}"> {{ s.name }}</label>{% endfor %}
                    </div>
                    <button class="btn" style="width:100%;">Create Key</button>
                </form>
            </div>
            <div class="card glass" style="flex:2;min-width:400px;overflow-x:auto;">
                <table class="table">
                    <tr><th>Key</th><th>Owner</th><th>Usage (Hit/Limit)</th><th>Status</th><th>Actions</th></tr>
                    {% for k_id, k in db.get('keys', {}).items() %}
                      <tr><td style="font-family:monospace;color:var(--neon);font-size:13px;">{{ k_id }}<br><span style="font-size:10px;color:#aaa;">Exp: {{ fmt_time(k.expiry) }}</span></td>
                         <td>{{ k.owner }}</td>
                        <td><div style="font-size:11px;margin-bottom:2px;">{{ k.used }} / {% if k.limit==0 %}&infin;{% else %}{{ k.limit }}{% endif %} (S:{{k.ok}} F:{{k.fail}})</div>
                             {% if k.limit > 0 %}<div style="width:100%;background:rgba(255,255,255,0.1);height:4px;border-radius:2px;"><div style="width:{{ (k.used/k.limit*100)|round }}%;background:var(--neon);height:100%;border-radius:2px;max-width:100%;"></div></div>{% endif %}
                        </td>
                         <td>{% if k.revoked %}<span style="color:#d9534f;font-weight:bold;font-size:12px;">REVOKED</span>{% elif k.expiry < now_ts() %}<span style="color:#f0ad4e;font-weight:bold;font-size:12px;">EXPIRED</span>{% else %}<span style="color:#5cb85c;font-weight:bold;font-size:12px;">ACTIVE</span>{% endif %}</td>
                         <td><a href="/admin/key/toggle/{{ k_id }}" class="btn" style="padding:4px 8px;font-size:12px;">{% if k.revoked %}Undo{% else %}Revoke{% endif %}</a>
                              <a href="/admin/key/delete/{{ k_id }}" class="btn btn-danger" style="padding:4px 8px;font-size:12px;">Del</a></td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>

    <!-- cURL Modal -->
    <div id="curlModal" class="modal">
        <div class="card glass" style="width:500px;position:relative;">
             <button onclick="document.getElementById('curlModal').style.display='none'" style="position:absolute;top:15px;right:15px;background:none;border:none;color:#fff;cursor:pointer;font-size:20px;">&times;</button>
             <h3 style="margin-top:0;color:var(--neon)"><i class="fa-solid fa-code"></i> Smart Auto-Catcher</h3>
            <p style="font-size:12px;opacity:0.8;margin-bottom:15px;">Paste cURL. Headers, token, body, and endpoints will be auto-extracted.</p>
             <textarea id="curlInput" rows="7" placeholder="curl -X POST https://api... -H 'Authorization: Bearer xyz' -d '{...}'"></textarea>
            <button class="btn" style="width:100%;" onclick="processCurl()">Parse & Create Service</button>
        </div>
    </div>

<div id="logs" class="tab">
         <h3 style="color:var(--neon)">Live Audit Logs</h3>
        <div class="card glass" style="max-height:400px;overflow-y:auto;">
            <table class="table">
                <tr><th>Time</th><th>Key</th><th>Service</th><th>Status</th><th>Message</th></tr>
                {% for log in db.get('logs', [])|reverse %}
                  <tr><td>{{ fmt_time(log.ts) }}</td><td style="font-family:monospace;color:var(--neon)">{{ log.key }}</td>
                    <td>{{ log.service }}</td><td><span class="health-dot {% if log.ok %}green{% else %}red{% endif %}"></span></td>
                     <td style="font-size:12px;opacity:0.8">{{ log.msg }}</td></tr>
                {% endfor %}
            </table>
        </div>
    </div>
</div>
{% endif %}
<script>
// JS for UI interactions aur Auto-Catcher AJAX call
function showTab(t, el) {
    document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
    document.getElementById(t).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
    if(el) el.classList.add('active');
}

setInterval(() => {
    let d = new Date();
    let clock = document.getElementById('live-clock');
     if(clock) clock.innerText = d.toLocaleTimeString('en-US', {hour12:true});
}, 1000);

async function processCurl() {
    let curl = document.getElementById('curlInput').value;
    let res = await fetch('/admin/service/import', {
         method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'},
        body: 'curl_text='+encodeURIComponent(curl)
    });
    let data = await res.json();
    if(data.status) {
        alert("Success! Check browser console to see the extracted dynamic template (Token Auto-Encrypted). You can now manually add it via the Add form.");
        console.log("Parsed Configuration:", data.data);
        document.getElementById('curlModal').style.display='none';
    } else alert("Error: " + data.msg);
}
</script></body></html>
'''

# --- MAIN DASHBOARD ROUTE ---
@app.route('/')
def dashboard():
    db = GistDB.load()
    return render_template_string(HTML, db=db, now_ts=now_ts, fmt_time=fmt_time)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
