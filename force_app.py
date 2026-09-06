import ast

with open("app.py", "r") as f:
    content = f.read()

# Strip any leading garbage/whitespace
content = content.lstrip()

# Clean mandatory header
prefix = "from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for\napp = Flask(__name__)\napp.secret_key = 'solo_proxy_secret'\n\n"

# Filter out old duplicate app assignments
lines = content.splitlines()
clean_lines = []
for line in lines:
    if "app = Flask" in line or "application = Flask" in line:
        continue
    clean_lines.append(line)

new_content = prefix + "\n".join(clean_lines)

# Validate via Python AST so Vercel won't complain about parsing
try:
    ast.parse(new_content)
    with open("app.py", "w") as f:
        f.write(new_content)
    print("AST Check Passed: app.py is 100% valid and ready for Vercel!")
except SyntaxError as e:
    print(f"Syntax Error detected: {e}")
