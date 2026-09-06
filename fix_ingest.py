with open("app.py", "r") as f:
    content = f.read()

# Remove old auto-ingest route if it exists to avoid duplication
if "def auto_ingest_request" in content:
    import re
    content = re.sub(r"@app\.route\('/admin/auto-ingest'.*?return jsonify\(\{\"status\": False.*?500\n", "", content, flags=re.DOTALL)

# Clean, robust auto-ingest route without login block breaking JSON response
new_route = """
@app.route('/admin/auto-ingest', methods=['POST'])
def auto_ingest_request():
    try:
        req_data = request.get_json(silent=True) or {}
        raw_data = request.form.get('raw_text', '') or req_data.get('raw_text', '')
        if not raw_data:
            return jsonify({"status": False, "error": "No raw data provided"}), 400
        
        lines = [l.strip() for l in raw_data.strip().split('\\n') if l.strip()]
        if not lines:
            return jsonify({"status": False, "error": "Empty data"}), 400
        
        first_line_parts = lines[0].split()
        method = first_line_parts[0] if len(first_line_parts) > 0 else "GET"
        path = first_line_parts[1] if len(first_line_parts) > 1 else "/"
        
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                parts = line.split(':', 1)
                headers[parts[0].strip().lower()] = parts[1].strip()
                
        tenant = headers.get('x-tenant', headers.get('x-partner-id', 'turtlemint'))
        broker = headers.get('x-broker', 'turtlemint')
        auth = headers.get('authorization', '')
        
        db = GistDB.load()
        if 'services' not in db:
            db['services'] = []
            
        service_entry = {
            "code": path.strip('/').replace('/', '_')[:30],
            "path": path,
            "method": method,
            "tenant": tenant,
            "broker": broker,
            "auth": auth,
            "headers": headers,
            "active": True
        }
        
        db['services'].append(service_entry)
        GistDB.save(db)
        
        return jsonify({
            "status": True, 
            "message": "Successfully auto-parsed and saved to database!", 
            "extracted": {
                "path": path,
                "tenant": tenant,
                "broker": broker,
                "has_token": bool(auth)
            }
        })
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
"""

content = content + "\n" + new_route

with open("app.py", "w") as f:
    f.write(content)

print("Backend fixed successfully!")
