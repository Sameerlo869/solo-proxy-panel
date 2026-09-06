filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# We will add an auto-import helper route and update the HTML dashboard template to include a Smart Paste box
auto_import_route = """
@app.route('/api/auto-company-import', methods=['POST'])
def auto_company_import():
    try:
        raw_data = request.form.get('raw_data', '') or request.json.get('raw_data', '')
        if not raw_data:
            return jsonify({"status": False, "msg": "No data provided"}), 400
        
        import re
        # Extract headers or parameters using regex
        tenant_match = re.search(r'x-tenant:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        broker_match = re.search(r'x-broker:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        provider_match = re.search(r'x-provider:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        host_match = re.search(r'host:\s*([^\r\n]+)', raw_data, re.IGNORECASE)
        
        tenant = tenant_match.group(1).strip() if tenant_match else "default_tenant"
        broker = broker_match.group(1).strip() if broker_match else "default_broker"
        provider = provider_match.group(1).strip() if provider_match else "default_provider"
        
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
            "raw_snippet": raw_data[:200]
        }
        
        GistDB.save(db)
        if request.is_json:
            return jsonify({"status": True, "msg": f"Company {company_code} saved successfully!", "data": db['companies'][company_code]})
        return redirect('/')
    except Exception as e:
        return jsonify({"status": False, "msg": str(e)}), 500
"""

if "auto_company_import" not in content:
    # Append the route before if __name__ == '__main__':
    if "if __name__ == '__main__':" in content:
        content = content.replace("if __name__ == '__main__':", auto_import_route + "\n\nif __name__ == '__main__':")
    else:
        content += "\n" + auto_import_route
    print("Added auto_company_import route.")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
