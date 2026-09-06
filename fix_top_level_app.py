with open("app.py", "r") as f:
    content = f.read()

# Make sure 'app = Flask' or 'application = Flask' exists at module level
if "app = Flask" not in content and "application = Flask" not in content:
    header = "from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for\napp = Flask(__name__)\napp.secret_key = 'solo_proxy_secret'\n"
    content = header + content
    print("Injected missing top-level Flask app definition.")
else:
    print("Flask app definition already exists.")

with open("app.py", "w") as f:
    f.write(content)

print("Done!")
