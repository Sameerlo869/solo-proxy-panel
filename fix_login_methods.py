filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Update @app.route('/login', methods=['POST']) to accept GET and POST
content = content.replace("@app.route('/login', methods=['POST'])", "@app.route('/login', methods=['GET', 'POST'])")
content = content.replace("@app.route('/login', methods=[\"POST\"])", "@app.route('/login', methods=['GET', 'POST'])")

# Inside login(), handle GET requests gracefully by redirecting to home
login_func_pattern = re.compile(r'def login\(\):(.*?)(?=\ndef |\n@app.route|\Z)', re.DOTALL)
match = login_func_pattern.search(content)
if match:
    old_body = match.group(1)
    if "request.method == 'GET'" not in old_body:
        new_body = "\n    if request.method == 'GET':\n        return redirect('/')\n" + old_body
        content = content.replace(old_body, new_body)
        print("Added GET handler to login route.")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
