filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Remove any old conflicting import routes or alert scripts
content = re.sub(r'<script\b[^>]*>.*?(?:Token Auto-Encrypted|Check browser console).*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

# Universal Auto-Import Logic supporting both endpoints
universal_importer = r"""
def process_auto_import():
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
            return jsonify({"status": True, "msg": f"Company {company_code} auto-saved!", "data": db['companies'][company_code]})
        
        return redirect('/')
    except Exception as e:
        return f"Import Error: {str(e)}", 500

@app.route('/admin/service/import', methods=['POST'])
def admin_service_import():
    return process_auto_import()

@app.route('/api/auto-company-import', methods=['POST'])
def auto_company_import():
    return process_auto_import()
"""

# Clean up old route definitions if they exist
content = re.sub(r'@app\.route\(\'/(?:admin/service/import|api/auto-company-import)\', methods=\[\'POST\'\]\)\ndef.*?(?=\ndef |\n@app.route|\Z)', '', content, flags=re.DOTALL)

if "if __name__ == '__main__':" in content:
    content = content.replace("if __name__ == '__main__':", universal_importer + "\n\nif __name__ == '__main__':")
else:
    content += "\n" + universal_importer

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

compile(content, filename, 'exec')
print("SUCCESS! Dual import routes compiled cleanly.")
