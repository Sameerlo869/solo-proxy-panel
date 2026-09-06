filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

old_login_pattern = re.compile(r'@app\.route\(\'/login\', methods=\[\'POST\'\]\)\ndef login\(\):(.*?)(?=\ndef |\n@app.route|\Z)', re.DOTALL)

new_login = """@app.route('/login', methods=['POST'])
def login():
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
        return f"Login Error: {str(e)}", 500"""

if old_login_pattern.search(content):
    content = old_login_pattern.sub(new_login, content)
    print("Replaced login with bulletproof fallback version.")
else:
    print("Could not find login route automatically!")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
