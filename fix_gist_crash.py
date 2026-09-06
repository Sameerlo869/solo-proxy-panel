with open("app.py", "r") as f:
    content = f.read()

# Let's see if GistDB.load is missing try-except
# We can wrap GistDB load/save methods or define a safe fallback
safe_gist_patch = """
# --- Safe GistDB Fallback Patch ---
try:
    _original_gist_load = GistDB.load
    def safe_gist_load():
        try:
            data = _original_gist_load()
            if not isinstance(data, dict):
                return {"services": [], "companies": []}
            return data
        except Exception:
            return {"services": [], "companies": []}
    GistDB.load = safe_gist_load
except Exception:
    pass
"""

if "Safe GistDB Fallback Patch" not in content:
    content = content + "\n" + safe_gist_patch
    with open("app.py", "w") as f:
        f.write(content)
    print("Safe fallback patch applied to app.py!")
else:
    print("Fallback patch already exists.")
