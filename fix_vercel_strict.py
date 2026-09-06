with open("app.py", "r") as f:
    lines = f.readlines()

# Clean header required by Vercel
header = [
    "from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for\n",
    "app = Flask(__name__)\n",
    "app.secret_key = 'solo_proxy_secret'\n\n"
]

# Remove any old conflicting app definitions from the lines
filtered_lines = []
for line in lines:
    if "app = Flask" in line or "application = Flask" in line:
      continue
    filtered_lines.append(line)

with open("app.py", "w") as f:
    f.writelines(header + filtered_lines)

print("app.py restructured cleanly for Vercel!")
