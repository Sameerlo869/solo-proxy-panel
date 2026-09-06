filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Ensure secret_key is present for sessions
if "secret_key" not in content:
    print("Adding missing app.secret_key...")
    content = content.replace("app = Flask(__name__)", "app = Flask(__name__)\napp.secret_key = os.environ.get('SECRET_KEY', 'default-secure-fallback-key')")

# 2. Clean up stray CSS comment tags in HTML templates
content = content.replace("# [Naked CSS Nuked]", "")
content = content.replace("# [Auto-Cleaned CSS]", "")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly.")
except Exception as e:
    print(f"Compilation Error: {e}")
