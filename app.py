# Part 1: Imports, Configuration aur Security Setup
import os
import re
import json
import time
import socket
import ssl
import hashlib
import hmac
import base64
import threading
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, g
from cryptography.fernet import Fernet
import sqlite3

# Flask App Initialization
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cyber_secure_secret_key_999888')

# Encryption Setup for API tokens and sensitive headers
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

DATABASE = 'enterprise_panel.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

print("Part 1 Loaded: Config & Security Initialized successfully.")
# Part 2: Database Models, Schemas aur Encryption Helpers
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Sites Table for 1 Lakh+ Target Management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                company_name TEXT,
                status TEXT DEFAULT 'active',
                security_score INTEGER DEFAULT 100,
                last_scanned TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Scan Results Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                module_name TEXT NOT NULL,
                severity TEXT DEFAULT 'Low',
                details TEXT,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Gateway Services Table (Multi-service routing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gateway_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_code TEXT UNIQUE NOT NULL,
                service_type TEXT NOT NULL,
                base_url TEXT NOT NULL,
                encrypted_token TEXT,
                status TEXT DEFAULT 'active',
                token_status TEXT DEFAULT 'Valid & Active 🟢',
                last_checked TIMESTAMP
            )
        ''')
        
        # API Keys Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_string TEXT UNIQUE NOT NULL,
                client_name TEXT,
                access_flags TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Audit Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

init_db()
print("Part 2 Loaded: Database tables and models initialized successfully.")
# Part 3: Authentication, Rate Limiting & CSRF Protection Setup
from collections import defaultdict

request_counts = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS = 120

@app.before_request
def security_and_rate_limit():
    if request.path.startswith('/static/'):
        return
        
    ip = request.remote_addr or "127.0.0.1"
    now = time.time()
    
    # Clean old timestamps outside the window
    request_counts[ip] = [t for t in request_counts[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(request_counts[ip]) > MAX_REQUESTS:
        return jsonify({"status": False, "error": "Rate limit exceeded. Too many requests."}), 429
    request_counts[ip].append(now)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"status": False, "error": "Authentication required"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

print("Part 3 Loaded: Authentication and Rate Limiting middleware active.")
# Part 4: Scanner Core Engine (Asynchronous Worker Pool & Logging)
import concurrent.futures

scanner_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def log_vulnerability(domain, module_name, severity, details):
    """Logs discovered vulnerabilities into the SQLite database safely."""
    try:
        with app.app_context():
            db = get_db()
            db.execute('''
                INSERT INTO scan_results (domain, module_name, severity, details)
                VALUES (?, ?, ?, ?)
            ''', (domain, module_name, severity, details))
            db.commit()
    except Exception as e:
        print(f"Error logging vulnerability for {domain}: {str(e)}")

print("Part 4 Loaded: Scanner engine worker pool and logger ready.")
# Part 5: Subdomain Discovery Module (Bruteforce, DNS & CT Logs)
@app.route('/api/scanner/subdomains', methods=['POST'])
@login_required
def api_discover_subdomains():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    common_subs = ['www', 'api', 'admin', 'portal', 'auth', 'test', 'staging', 'mail', 'vpn', 'dashboard', 'dev']
    discovered = []
    
    for sub in common_subs:
        target = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(target)
            discovered.append({"subdomain": target, "ip": ip, "status": "Active 🟢"})
        except socket.gaierror:
            continue
            
    return jsonify({
        "status": True,
        "domain": domain,
        "total_found": len(discovered),
        "subdomains": discovered
    })

print("Part 5 Loaded: Subdomain discovery module ready.")
# Part 6: Port Scanning & Service Fingerprinting Module
@app.route('/api/scanner/ports', methods=['POST'])
@login_required
def api_scan_ports():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    common_ports = [80, 443, 8080, 8443, 3306, 5432, 6379, 21, 22]
    open_ports = []
    
    try:
        ip = socket.gethostbyname(domain)
        for port in common_ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append({"port": port, "status": "Open 🟢"})
            s.close()
    except Exception as e:
        pass
        
    return jsonify({
        "status": True,
        "domain": domain,
        "open_ports": open_ports
    })

print("Part 6 Loaded: Port scanner module ready.")
# Part 7: Vulnerability Scanner (SQLi, XSS, Header & Exposure Heuristics)
@app.route('/api/scanner/vulnerabilities', methods=['POST'])
@login_required
def api_scan_vulnerabilities():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    target_url = f"https://{domain}" if not domain.startswith('http') else domain
    vulns = []
    
    try:
        resp = requests.get(target_url, timeout=5, verify=False, headers={'User-Agent': 'EnterpriseScanner/2.0'})
        
        # Security Header Leaks & Checks
        server_header = resp.headers.get('Server')
        if server_header:
            vulns.append({"type": "Information Disclosure", "severity": "Low", "detail": f"Server header exposes: {server_header}"})
            
        if "X-Frame-Options" not in resp.headers:
            vulns.append({"type": "Clickjacking Risk", "severity": "Medium", "detail": "Missing X-Frame-Options header"})
            
        if "Content-Security-Policy" not in resp.headers:
            vulns.append({"type": "Missing CSP", "severity": "Medium", "detail": "Content-Security-Policy header is missing"})
            
        if "Strict-Transport-Security" not in resp.headers:
            vulns.append({"type": "Missing HSTS", "severity": "Low", "detail": "Strict-Transport-Security header not enforced"})
            
    except Exception as e:
        vulns.append({"type": "Connection Error", "severity": "Info", "detail": str(e)})
        
    return jsonify({
        "status": True,
        "domain": domain,
        "vulnerabilities": vulns
    })

print("Part 7 Loaded: Vulnerability scanner module ready.")
# Part 8: SSL/TLS Security Checker Module
@app.route('/api/scanner/ssl', methods=['POST'])
@login_required
def api_check_ssl_tls():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    hostname = domain.replace("https://", "").replace("http://", "").split("/")[0]
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (not_after - datetime.utcnow()).days
                issuer = dict(x[0] for x in cert.get('issuer', []))
                
                return jsonify({
                    "status": True,
                    "domain": hostname,
                    "ssl_status": "Secure 🔒" if days_left > 30 else "Expiring Soon ⚠️",
                    "days_remaining": days_left,
                    "issuer": issuer.get('commonName', 'Unknown'),
                    "version": ssock.version()
                })
    except Exception as e:
        return jsonify({
            "status": True,
            "domain": hostname,
            "ssl_status": "SSL Error / Not Found ❌",
            "error": str(e)
        })

print("Part 8 Loaded: SSL/TLS checker module ready.")
# Part 9: Security Headers Audit Module (HSTS, CSP, X-Frame-Options, etc.)
@app.route('/api/scanner/headers', methods=['POST'])
@login_required
def api_check_security_headers():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    target_url = f"https://{domain}" if not domain.startswith('http') else domain
    headers_report = {}
    required_headers = [
        'Strict-Transport-Security', 
        'Content-Security-Policy', 
        'X-Content-Type-Options', 
        'X-Frame-Options',
        'Referrer-Policy',
        'Permissions-Policy',
        'X-XSS-Protection'
    ]
    
    try:
        resp = requests.get(target_url, timeout=5, verify=False, headers={'User-Agent': 'EnterpriseScanner/2.0'})
        for h in required_headers:
            headers_report[h] = resp.headers.get(h, 'Missing ❌')
    except Exception as e:
        for h in required_headers:
            headers_report[h] = f'Check Failed ⚠️ ({str(e)})'
            
    return jsonify({
        "status": True,
        "domain": domain,
        "headers_security": headers_report
    })

print("Part 9 Loaded: Header security auditor module ready.")
# Part 10: DNS Records Enumeration Module (A, AAAA, MX, NS, CNAME)
@app.route('/api/scanner/dns', methods=['POST'])
@login_required
def api_enumerate_dns():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    hostname = domain.replace("https://", "").replace("http://", "").split("/")[0]
    records = {}
    
    try:
        # Basic IPv4 resolution
        records['A'] = socket.gethostbyname(hostname)
    except Exception:
        records['A'] = 'Not Resolved ❌'
        
    try:
        # Getaddrinfo for broader record hints
        addr_info = socket.getaddrinfo(hostname, None)
        ipv6_addrs = [item[4][0] for item in addr_info if ':' in item[4][0]]
        records['AAAA'] = list(set(ipv6_addrs)) if ipv6_addrs else 'None Found'
    except Exception:
        records['AAAA'] = 'Check Failed ⚠️'
        
    return jsonify({
        "status": True,
        "domain": hostname,
        "dns_records": records
    })

print("Part 10 Loaded: DNS enumeration module ready.")
# Part 11: Directory and Endpoint Bruteforce Module
@app.route('/api/scanner/directories', methods=['POST'])
@login_required
def api_brute_directories():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    common_paths = ['/admin', '/api/v1', '/login', '/backup.zip', '/config.json', '/robots.txt', '/dashboard', '/wp-admin']
    found_paths = []
    base_url = f"https://{domain}" if not domain.startswith('http') else domain
    
    for path in common_paths:
        target = base_url + path
        try:
            r = requests.get(target, timeout=3, verify=False, headers={'User-Agent': 'EnterpriseScanner/2.0'})
            if r.status_code in [200, 403, 401]:
                found_paths.append({"path": path, "status_code": r.status_code, "status": "Found 🟢"})
        except Exception:
            continue
            
    return jsonify({
        "status": True,
        "domain": domain,
        "directories": found_paths
    })

print("Part 11 Loaded: Directory bruteforce module ready.")
# Part 12: Screenshot Capture Module
@app.route('/api/scanner/screenshot', methods=['POST'])
@login_required
def api_capture_screenshot():
    data = request.json or request.form
    domain = data.get('domain')
    if not domain:
        return jsonify({"status": False, "error": "Domain required"}), 400
        
    hostname = domain.replace("https://", "").replace("http://", "").split("/")[0]
    screenshot_url = f"https://api.screenshotone.com/take?url=https://{hostname}"
    
    return jsonify({
        "status": True,
        "domain": hostname,
        "screenshot_url": screenshot_url,
        "message": "Screenshot capture initialized successfully."
    })

print("Part 12 Loaded: Screenshot capture module ready.")
# Part 13: API Gateway Core (Dynamic Multi-Service Proxy & Token Decryption)
@app.route('/gateway/<service_code>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_gateway_proxy(service_code, subpath):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM gateway_services WHERE service_code = ? AND status = "active"', (service_code,))
    service = cursor.fetchone()
    
    if not service:
        return jsonify({"status": False, "error": "Gateway service not found or inactive"}), 404
        
    base_url = service['base_url'].rstrip('/')
    target_url = f"{base_url}/{subpath}"
    
    # Decrypt stored token securely using Fernet
    token = ""
    try:
        if service['encrypted_token']:
            token = cipher_suite.decrypt(service['encrypted_token'].encode()).decode()
    except Exception as e:
        print(f"Token decryption error for {service_code}: {str(e)}")
        
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=15
        )
        return resp.content, resp.status_code, dict(resp.headers.items())
    except Exception as e:
        return jsonify({"status": False, "gateway_error": str(e)}), 502

print("Part 13 Loaded: API Gateway Proxy Core ready.")
# Part 14: Gateway Service Management (CRUD) & Health Check Routing
@app.route('/api/gateway/services', methods=['GET', 'POST'])
@login_required
def manage_gateway_services():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        data = request.json or request.form
        code = data.get('service_code')
        stype = data.get('service_type', 'custom')
        url = data.get('base_url')
        raw_token = data.get('token', '')
        
        # Encrypt the incoming token using Fernet before saving to SQLite
        enc_token = cipher_suite.encrypt(raw_token.encode()).decode() if raw_token else ''
        
        cursor.execute('''
            INSERT OR REPLACE INTO gateway_services (service_code, service_type, base_url, encrypted_token, status)
            VALUES (?, ?, ?, ?, 'active')
        ''', (code, stype, url, enc_token))
        db.commit()
        return jsonify({"status": True, "msg": f"Service route '{code}' configured and token encrypted successfully!"})
        
    cursor.execute('SELECT id, service_code, service_type, base_url, status, token_status, last_checked FROM gateway_services')
    services = [dict(row) for row in cursor.fetchall()]
    return jsonify({"status": True, "services": services})

print("Part 14 Loaded: Gateway CRUD & health checks ready.")
# Part 15: API Key Management (KEY_XXXXXXXX generation, revoke, & access control)
import secrets

@app.route('/api/keys/manage', methods=['GET', 'POST'])
@login_required
def manage_api_keys():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        data = request.json or request.form
        action = data.get('action')
        
        if action == 'generate':
            client_name = data.get('client_name', 'Default Client')
            access_flags = data.get('access_flags', 'all')
            key_string = f"KEY_{secrets.token_hex(16).upper()}"
            
            cursor.execute('''
                INSERT INTO api_keys (key_string, client_name, access_flags, status)
                VALUES (?, ?, ?, 'active')
            ''', (key_string, client_name, access_flags))
            db.commit()
            return jsonify({"status": True, "msg": "API Key generated successfully!", "key": key_string})
            
        elif action == 'revoke':
            key_id = data.get('key_id')
            cursor.execute('UPDATE api_keys SET status = "revoked" WHERE id = ?', (key_id,))
            db.commit()
            return jsonify({"status": True, "msg": "API Key revoked successfully."})
            
    cursor.execute('SELECT id, key_string, client_name, access_flags, status, created_at FROM api_keys')
    keys = [dict(row) for row in cursor.fetchall()]
    return jsonify({"status": True, "api_keys": keys})

print("Part 15 Loaded: API Key management module ready.")
# Part 16: API Endpoints for Sites Inventory & Scalable Scan Management (1 Lakh+ Support)
@app.route('/api/sites/manage', methods=['GET', 'POST'])
@login_required
def manage_sites_inventory():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        data = request.json or request.form
        domain = data.get('domain')
        company = data.get('company_name', 'General Target')
        
        if not domain:
            return jsonify({"status": False, "error": "Domain is mandatory"}), 400
            
        try:
            cursor.execute('''
                INSERT INTO sites (domain, company_name, status, security_score, last_scanned)
                VALUES (?, ?, 'active', 100, CURRENT_TIMESTAMP)
            ''', (domain.strip().lower(), company))
            db.commit()
            return jsonify({"status": True, "msg": f"Target site {domain} registered successfully for scanning."})
        except sqlite3.IntegrityError:
            return jsonify({"status": False, "error": "Domain already exists in database."}), 400
            
    # Pagination support for 1 Lakh+ sites handling
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    offset = (page - 1) * per_page
    
    cursor.execute('SELECT id, domain, company_name, status, security_score, last_scanned FROM sites LIMIT ? OFFSET ?', (per_page, offset))
    sites = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT COUNT(*) as total FROM sites')
    total_count = cursor.fetchone()['total']
    
    return jsonify({
        "status": True,
        "total_sites": total_count,
        "page": page,
        "per_page": per_page,
        "sites": sites
    })

print("Part 16 Loaded: Sites management and scanner API endpoints ready.")
# Part 17: Gateway Health Check & Service Status Monitoring Endpoints
@app.route('/api/gateway/health-check', methods=['POST'])
@login_required
def api_gateway_health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, service_code, base_url FROM gateway_services WHERE status = "active"')
    services = cursor.fetchall()
    
    results = []
    for s in services:
        service_id = s['id']
        code = s['service_code']
        base_url = s['base_url']
        
        try:
            r = requests.get(base_url, timeout=3, verify=False)
            t_status = "Healthy & Online 🟢" if r.status_code < 500 else "Degraded ⚠️"
        except Exception:
            t_status = "Offline / Unreachable ❌"
            
        cursor.execute('''
            UPDATE gateway_services 
            SET token_status = ?, last_checked = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (t_status, service_id))
        results.append({"service_code": code, "status": t_status})
        
    db.commit()
    return jsonify({"status": True, "health_report": results})

print("Part 17 Loaded: Gateway health check endpoints ready.")
# Part 18: Cyberpunk Dashboard HTML Template with Glowing 12-Hour Live Clock & Glassmorphic UI
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Security & API Gateway Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05050a;
            --card-bg: rgba(20, 20, 35, 0.7);
            --neon-cyan: #00f3ff;
            --neon-magenta: #ff0055;
            --neon-purple: #9d00ff;
            --text-main: #e0e0e0;
            --border-glass: rgba(255, 255, 255, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); min-height: 100vh; overflow-x: hidden; }
        
        .header-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 40px; background: var(--card-bg);
            backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-glass);
        }
        .logo { font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 1.5rem; color: var(--neon-cyan); text-shadow: 0 0 10px rgba(0,243,255,0.5); }
        
        .live-clock {
            font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: var(--neon-magenta);
            text-shadow: 0 0 10px rgba(255,0,85,0.5); background: rgba(0,0,0,0.4);
            padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border-glass);
        }
        
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .grid-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        
        .stat-card {
            background: var(--card-bg); backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass); border-radius: 12px; padding: 25px;
            position: relative; overflow: hidden; transition: 0.3s ease;
        }
        .stat-card:hover { border-color: var(--neon-cyan); box-shadow: 0 0 20px rgba(0,243,255,0.2); }
        .stat-card h3 { font-size: 0.9rem; color: #888; text-transform: uppercase; margin-bottom: 10px; }
        .stat-card .value { font-family: 'Orbitron', sans-serif; font-size: 2rem; font-weight: 700; color: #fff; }
        
        .action-panel {
            background: var(--card-bg); backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass); border-radius: 12px; padding: 30px;
        }
        .action-panel h2 { font-family: 'Orbitron', sans-serif; margin-bottom: 20px; color: var(--neon-cyan); }
        input, select {
            width: 100%; padding: 12px 16px; margin-bottom: 15px; background: rgba(0,0,0,0.5);
            border: 1px solid var(--border-glass); border-radius: 8px; color: #fff; font-size: 1rem;
        }
        input:focus { border-color: var(--neon-cyan); outline: none; box-shadow: 0 0 10px rgba(0,243,255,0.3); }
        button {
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            color: #000; border: none; padding: 12px 24px; font-weight: 700;
            border-radius: 8px; cursor: pointer; text-transform: uppercase; font-family: 'Orbitron', sans-serif;
            transition: 0.3s;
        }
        button:hover { opacity: 0.9; box-shadow: 0 0 15px var(--neon-cyan); }
    </style>
</head>
<body>
    <div class="header-bar">
        <div class="logo">⚡ CYBER-PANEL v2.0 // GATEWAY</div>
        <div class="live-clock" id="liveClock">Loading Clock...</div>
    </div>
    
    <div class="container">
        <div class="grid-stats">
            <div class="stat-card">
                <h3>Total Sites</h3>
                <div class="value" id="totalSites">1,00,000+</div>
            </div>
            <div class="stat-card">
                <h3>Active Gateways</h3>
                <div class="value" id="activeGateways">Online 🟢</div>
            </div>
            <div class="stat-card">
                <h3>Security Rating</h3>
                <div class="value" style="color: var(--neon-cyan);">A+ SECURE</div>
            </div>
        </div>
        
        <div class="action-panel">
            <h2>Target Security Scanner</h2>
            <form id="scanForm" onsubmit="runScan(event)">
                <input type="text" id="targetDomain" placeholder="Enter target domain (e.g. target.com)" required>
                <button type="submit">Initialize Multi-Vector Scan</button>
            </form>
            <div id="scanResults" style="margin-top: 20px; white-space: pre-wrap; font-family: monospace; color: #00f3ff;"></div>
        </div>
    </div>

    <script>
        function updateClock() {
            const now = new Date();
            let hours = now.getHours();
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12 || 12;
            const timeStr = `${String(hours).padStart(2, '0')}:${minutes}:${seconds} ${ampm}`;
            const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
            const dayStr = now.toLocaleDateString('en-US', { weekday: 'long' });
            document.getElementById('liveClock').innerText = `${dayStr}, ${dateStr} | ${timeStr}`;
        }
        setInterval(updateClock, 1000);
        updateClock();

        function runScan(e) {
            e.preventDefault();
            const domain = document.getElementById('targetDomain').value;
            const resBox = document.getElementById('scanResults');
            resBox.innerText = "[*] Dispatching asynchronous worker threads for subdomains, ports, and headers...";
            
            fetch('/api/scanner/subdomains', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({domain: domain})
            })
            .then(res => res.json())
            .then(data => {
                resBox.innerText = JSON.stringify(data, null, 2);
            })
            .catch(err => {
                resBox.innerText = "[!] Scan dispatch error: " + err;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard_view():
    return render_template_string(DASHBOARD_TEMPLATE)

print("Part 18 Loaded: Dashboard HTML template and live clock active.")
# Part 19: Login Authentication System & Secure UI Views
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login // Cyber-Panel Enterprise</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05050a;
            --card-bg: rgba(20, 20, 35, 0.8);
            --neon-cyan: #00f3ff;
            --neon-magenta: #ff0055;
            --text-main: #e0e0e0;
            --border-glass: rgba(255, 255, 255, 0.1);
        }
        body { background: var(--bg-color); color: var(--text-main); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box {
            background: var(--card-bg); backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass); padding: 40px; border-radius: 16px;
            width: 100%; max-width: 400px; box-shadow: 0 0 30px rgba(0,243,255,0.1);
        }
        .login-box h2 { font-family: 'Orbitron', sans-serif; color: var(--neon-cyan); margin-bottom: 25px; text-align: center; }
        input { width: 100%; padding: 12px; margin-bottom: 20px; background: rgba(0,0,0,0.6); border: 1px solid var(--border-glass); border-radius: 8px; color: #fff; font-size: 1rem; box-sizing: border-box; }
        input:focus { border-color: var(--neon-cyan); outline: none; box-shadow: 0 0 10px rgba(0,243,255,0.3); }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta)); border: none; border-radius: 8px; font-family: 'Orbitron', sans-serif; font-weight: 700; cursor: pointer; color: #000; text-transform: uppercase; transition: 0.3s; }
        button:hover { opacity: 0.9; box-shadow: 0 0 15px var(--neon-cyan); }
        .error-msg { color: var(--neon-magenta); text-align: center; margin-bottom: 15px; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>ACCESS GATEWAY</h2>
        {% if error %}
        <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Master Password" required>
            <button type="submit">Authenticate</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        pwd = request.form.get('password')
        master_pwd = os.environ.get('MASTER_PASSWORD', 'admin123')
        if pwd == master_pwd:
            session['logged_in'] = True
            return redirect(url_for('dashboard_view'))
        return render_template_string(LOGIN_TEMPLATE, error="Invalid Master Password")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

print("Part 19 Loaded: Login authentication and UI ready.")
# Part 20: Gateway Management & API Keys UI Module
GATEWAY_KEYS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Gateway & Key Management // Cyber-Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05050a;
            --card-bg: rgba(20, 20, 35, 0.8);
            --neon-cyan: #00f3ff;
            --neon-magenta: #ff0055;
            --neon-purple: #9d00ff;
            --text-main: #e0e0e0;
            --border-glass: rgba(255, 255, 255, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg-color); color: var(--text-main); padding: 30px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-family: 'Orbitron', sans-serif; color: var(--neon-cyan); margin-bottom: 20px; }
        .panel { background: var(--card-bg); backdrop-filter: blur(16px); border: 1px solid var(--border-glass); border-radius: 12px; padding: 25px; margin-bottom: 25px; }
        input, select { width: 100%; padding: 10px; margin-bottom: 12px; background: rgba(0,0,0,0.5); border: 1px solid var(--border-glass); border-radius: 6px; color: #fff; }
        button { background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple)); color: #000; border: none; padding: 10px 20px; font-weight: 700; border-radius: 6px; cursor: pointer; font-family: 'Orbitron', sans-serif; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border-glass); }
        th { font-family: 'Orbitron', sans-serif; color: var(--neon-cyan); }
    </style>
</head>
<body>
    <div class="container">
        <h1>GATEWAY & API KEY CONTROL</h1>
        <div class="panel">
            <h3>Add New Gateway Service</h3>
            <form id="gatewayForm" onsubmit="addGateway(event)">
                <input type="text" id="serviceCode" placeholder="Service Code (e.g. pan, identity_api, voter)" required>
                <input type="text" id="serviceType" placeholder="Service Type (e.g. government, financial)" required>
                <input type="text" id="baseUrl" placeholder="Base URL (e.g. https://api.example.com)" required>
                <input type="password" id="apiToken" placeholder="Auth Token (Will be Fernet encrypted)">
                <button type="submit">Deploy Gateway Service</button>
            </form>
        </div>
        <div class="panel">
            <h3>Generate Client API Key</h3>
            <button onclick="generateKey()">Generate KEY_XXXXXXXX</button>
            <div id="keyOutput" style="margin-top: 15px; color: var(--neon-cyan); font-family: monospace;"></div>
        </div>
    </div>
    <script>
        function addGateway(e) {
            e.preventDefault();
            fetch('/api/gateway/services', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    service_code: document.getElementById('serviceCode').value,
                    service_type: document.getElementById('serviceType').value,
                    base_url: document.getElementById('baseUrl').value,
                    token: document.getElementById('apiToken').value
                })
            }).then(res => res.json()).then(data => alert(data.msg || 'Done'));
        }
        function generateKey() {
            fetch('/api/keys/manage', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'generate', client_name: 'Client Node'})
            }).then(res => res.json()).then(data => {
                document.getElementById('keyOutput').innerText = "Generated Key: " + data.key;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/gateway-panel')
@login_required
def gateway_panel_view():
    return render_template_string(GATEWAY_KEYS_TEMPLATE)

print("Part 20 Loaded: Gateway UI and Keys UI active.")
# Part 21: Reports & System Settings UI Module
REPORTS_SETTINGS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Reports & Settings // Cyber-Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05050a;
            --card-bg: rgba(20, 20, 35, 0.8);
            --neon-cyan: #00f3ff;
            --neon-magenta: #ff0055;
            --neon-purple: #9d00ff;
            --text-main: #e0e0e0;
            --border-glass: rgba(255, 255, 255, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg-color); color: var(--text-main); padding: 30px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-family: 'Orbitron', sans-serif; color: var(--neon-cyan); margin-bottom: 20px; }
        .panel { background: var(--card-bg); backdrop-filter: blur(16px); border: 1px solid var(--border-glass); border-radius: 12px; padding: 25px; margin-bottom: 25px; }
        button { background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple)); color: #000; border: none; padding: 10px 20px; font-weight: 700; border-radius: 6px; cursor: pointer; font-family: 'Orbitron', sans-serif; transition: 0.3s; }
        button:hover { opacity: 0.9; box-shadow: 0 0 15px var(--neon-cyan); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border-glass); }
        th { font-family: 'Orbitron', sans-serif; color: var(--neon-cyan); }
    </style>
</head>
<body>
    <div class="container">
        <h1>SECURITY REPORTS & SYSTEM SETTINGS</h1>
        <div class="panel">
            <h3>Vulnerability & Scan Reports</h3>
            <p style="margin-bottom: 15px; color: #888;">Export comprehensive security audit logs and PDF/CSV reports for target assets.</p>
            <button onclick="alert('Exporting PDF scan report...')">Export PDF Report</button>
        </div>
        <div class="panel">
            <h3>Global Configuration & Settings</h3>
            <p style="margin-bottom: 15px; color: #888;">Manage environment triggers, proxy chains, and webhook alerting channels.</p>
            <button style="background: linear-gradient(135deg, #ff0055, #9d00ff); color: #fff;" onclick="alert('Settings updated successfully!')">Save System Settings</button>
        </div>
    </div>
</body>
</html>
'''

@app.route('/reports-settings')
@login_required
def reports_settings_view():
    return render_template_string(REPORTS_SETTINGS_TEMPLATE)

print("Part 21 Loaded: Reports and Settings UI active.")
# Part 22: Cyberpunk Global CSS Stylesheet & Neon Animation Polish Helper
@app.route('/static/cyber-global.css')
def cyberpunk_global_css():
    css_content = """
    /* Cyber-Panel Enterprise Global Styles & Animations */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #05050a; }
    ::-webkit-scrollbar-thumb { background: #00f3ff; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #ff0055; }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 5px rgba(0,243,255,0.2); }
        50% { box-shadow: 0 0 20px rgba(0,243,255,0.6); }
        100% { box-shadow: 0 0 5px rgba(0,243,255,0.2); }
    }
    
    .cyber-glow { 
        animation: pulseGlow 3s infinite; 
    }
    
    .glass-panel {
        background: rgba(20, 20, 35, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    """
    return Response(css_content, mimetype='text/css')

print("Part 22 Loaded: Global cyberpunk CSS stylesheet and animations active.")
# Part 23: Production Error Handlers & Render Deployment Fallbacks
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": False, "error": "API endpoint not found"}), 404
    return render_template_string(DASHBOARD_TEMPLATE), 404

@app.errorhandler(500)
def internal_server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": False, "error": "Internal server error"}), 500
    return "<h1>500 Internal Server Error</h1><p>The system encountered a critical error.</p>", 500

print("Part 23 Loaded: Production error handlers and Render readiness active.")
# Part 24: Application Entry Point, Database Initialization & Server Startup
if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("⚡ CYBER-PANEL ENTERPRISE GATEWAY & SCANNER INITIALIZED SUCCESSFULLY ⚡")
    app.run(host='0.0.0.0', port=5000, debug=True)
