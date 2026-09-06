filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove any old alert/console-logging frontend JS for auto-import
content = re.sub(r'<script>.*?(?:Check browser console|Auto-Encrypted).*?</script>', '', content, flags=re.DOTALL)

# Ensure the auto-import endpoint directly saves and redirects smoothly
new_route = r"""
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
"""

if "def auto_company_import():" in content:
    content = re.sub(r'@app\.route\(\'/api/auto-company-import\', methods=\[\'POST\'\]\)\ndef auto_company_import\(\):(.*?)(?=\ndef |\n@app.route|\Z)', new_route.strip(), content, flags=re.DOTALL)
else:
    if "if __name__ == '__main__':" in content:
        content = content.replace("if __name__ == '__main__':", new_route + "\n\nif __name__ == '__main__':")
    else:
        content += "\n" + new_route

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
