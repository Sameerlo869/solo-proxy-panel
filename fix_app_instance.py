with open("app.py", "r") as f:
    content = f.read()

# Check if Flask app instance is missing
if "app = Flask" not in content and "application = Flask" not in content:
    app_init = "from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for\napp = Flask(__name__)\napp.secret_key = 'solo_proxy_secret'\n"
    content = app_init + content
    print("Restored missing Flask app instance at the top.")

with open("app.py", "w") as f:
    f.write(content)

print("App instance verified!")
