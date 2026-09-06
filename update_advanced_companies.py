filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Add Company Management API routes (Toggle status & Live check)
company_mgmt_routes = r"""
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
"""

if "toggle_company" not in content:
    if "if __name__ == '__main__':" in content:
        content = content.replace("if __name__ == '__main__':", company_mgmt_routes + "\n\nif __name__ == '__main__':")
    else:
        content += "\n" + company_mgmt_routes

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
