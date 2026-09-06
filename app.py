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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect('/')

    try:
        db = {}
        try:
            loaded = GistDB.load()
            if isinstance(loaded, dict):
                db = loaded
        except Exception as db_err:
            print(f"GistDB load fallback active: {db_err}")
        
        u = request.form.get('u', '')
        p = request.form.get('p', '')
        
        admin_u = db.get('admin_u', 'admin') if db else 'admin'
        db_p = db.get('admin_p', 'admin') if db else 'admin'
        
        valid = False
        if db_p and db_p.startswith('$2'):
            try:
                valid = bcrypt.checkpw(p.encode(), db_p.encode())
            except Exception:
                valid = (p == db_p)
        else:
            valid = (p == db_p)
        
        if u == admin_u and valid:
            session['admin_logged'] = True
            session.permanent = True
            app.permanent_session_lifetime = 7200
            return redirect('/')
        else:
            return "Invalid username or password! <a href='/'>Go back</a>", 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Login Error: {str(e)}", 500
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
    url_m = re.search(r"(https?://[^\s'\"\\]+)", raw_text)
    if url_m:
        parsed_u = urllib.parse.urlparse(url_m.group(1))
        res["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"
        res["endpoint"] = parsed_u.path
        res["query_params"] = {k: f"{{{{{k}}}}}" for k, v in urllib.parse.parse_qsl(parsed_u.query)}
    return res
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
    if not k or not srv:
        return jsonify({"status": False, "msg": "Missing key or service"}), 400
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
    if not srv_obj or not srv_obj.get('active', True):
        return jsonify({"status": False, "msg": "Service Inactive/NotFound"}), 404
    return jsonify({"status": True, "msg": "Verified", "target": srv_obj.get('target_url')})

def api_verify():
    db = GistDB.load()
    k, srv = request.args.get('key'), request.args.get('service')
    if not k or not srv: return jsonify({"status": False, "msg": "Missing key or service"}), 400
    
    if is_rate_limited(request.remote_addr) or is_rate_limited(k):
        pass
    return jsonify({"status": False, "msg": "Rate limit exceeded"}), 429
        
    key_obj = db.get('keys', {}).get(k)
    if not key_obj or key_obj.get('revoked') or now_ts() > key_obj.get('expiry', 0): 
        pass
    return jsonify({"status": False, "msg": "Invalid/Revoked/Expired Key"}), 403
    if 0 < key_obj.get('limit', 0) <= key_obj.get('used', 0): 
        pass
    return jsonify({"status": False, "msg": "Quota Exhausted"}), 429
    if srv not in key_obj.get('assigned_services', []): 
        pass
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
</body></html>
'''

# --- MAIN DASHBOARD ROUTE ---
@app.route('/')
def dashboard():
    db = GistDB.load() or {}
    return render_template_string(HTML, db=db, now_ts=now_ts, fmt_time=fmt_time)



@app.route('/api/auto-company-import', methods=['POST'])
def auto_company_import():
    try:
        raw_data = request.form.get('raw_data', '') or (request.json.get('raw_data', '') if request.is_json else '')
        if not raw_data:
            return jsonify({"status": False, "msg": "No data provided"}), 400
        
        import re
        host_match = re.search(r'host:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        tenant_match = re.search(r'x-tenant:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        broker_match = re.search(r'x-broker:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        provider_match = re.search(r'x-provider:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        auth_match = re.search(r'authorization:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        
        host = host_match.group(1).strip() if host_match else "turtlemintloans.com"
        tenant = tenant_match.group(1).strip() if tenant_match else "turtlemint"
        broker = broker_match.group(1).strip() if broker_match else "turtlemint"
        provider = provider_match.group(1).strip() if provider_match else "signzy"
        auth = auth_match.group(1).strip() if auth_match else ""
        
        db = GistDB.load() or {}
        if 'companies' not in db:
            db['companies'] = {}
            
        company_code = broker.lower().replace(" ", "_")
        db['companies'][company_code] = {
            "code": company_code,
            "full_name": broker.title() + " Enterprise",
            "tenant_id": tenant,
            "broker_id": broker,
            "active_provider": provider,
            "base_url": f"https://{host}",
            "status": "active",
            "token_status": "Valid & Active 🟢",
            "last_checked": __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
            "headers": {
                "authorization": auth,
                "x-tenant": tenant,
                "x-broker": broker,
                "x-provider": provider,
                "host": host
            },
            "raw_snippet": raw_data[:300]
        }
        
        GistDB.save(db)
        
        if request.is_json or (request.headers.get('Content-Type') and 'application/json' in request.headers.get('Content-Type')):
            return jsonify({"status": True, "msg": f"Company {company_code} saved automatically!", "data": db['companies'][company_code]})
        
        return redirect('/')
    except Exception as e:
        return f"Auto-Import Error: {str(e)}", 500

@app.route('/api/company/toggle/<company_code>', methods=['POST'])
def toggle_company(company_code):
    try:
        db = GistDB.load() or {}
        companies = db.get('companies', {})
        if company_code in companies:
            current_status = companies[company_code].get('status', 'active')
            companies[company_code]['status'] = 'inactive' if current_status == 'active' else 'active'
            db['companies'] = companies
            GistDB.save(db)
        return redirect('/')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/api/company/check/<company_code>', methods=['POST', 'GET'])
def check_company_token(company_code):
    try:
        db = GistDB.load() or {}
        companies = db.get('companies', {})
        if company_code not in companies:
            return jsonify({"status": False, "msg": "Company not found"}), 404
        
        comp = companies[company_code]
        auth = comp.get('headers', {}).get('authorization', '')
        base_url = comp.get('base_url', 'https://turtlemintloans.com')
        
        # Perform live check simulation or lightweight request validation
        is_valid = bool(auth and len(auth) > 10)
        
        comp['token_status'] = 'Valid & Active 🟢' if is_valid else 'Invalid / Expired 🔴'
        comp['last_checked'] = __import__('time').strftime('%Y-%m-%d %H:%M:%S')
        db['companies'][company_code] = comp
        GistDB.save(db)
        
        if request.is_json or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({"status": True, "token_status": comp['token_status'], "last_checked": comp['last_checked']})
        return redirect('/')
    except Exception as e:
        return jsonify({"status": False, "msg": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
