filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Find dashboard function and ensure db is never None
old_dash_pattern = re.compile(r'def dashboard\(\):(.*?)(?=\ndef |\n@app.route|\Z)', re.DOTALL)

def replace_dash(match):
    body = match.group(1)
    # Ensure any GistDB.load() or db assignment handles None safely
    body = re.sub(r'db\s*=\s*GistDB\.load\(\)', 'db = GistDB.load() or {}', body)
    if 'db = GistDB.load() or {}' not in body:
        body = '\n    db = GistDB.load() or {}' + body
    return 'def dashboard():' + body

content, count = old_dash_pattern.subn(replace_dash, content)
print(f"Replaced dashboard function, count: {count}")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
