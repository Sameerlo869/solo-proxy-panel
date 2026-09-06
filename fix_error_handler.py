with open("app.py", "r") as f:
    content = f.read()

# Remove any broken handlers if present
if "py_handle_exception" in content or "handle_server_exception" in content:
    import re
    content = re.sub(r"@app\.errorhandler\(Exception\).*?return.*?\n\n", "", content, flags=re.DOTALL)

# Add a 100% syntactically correct Flask error handler
valid_handler = """
@app.errorhandler(Exception)
def handle_server_exception(e):
    import traceback
    return f"<h3>💥 Runtime Error Traceback:</h3><pre>{traceback.format_exc()}</pre>", 500
"""

content = content + "\n" + valid_handler

with open("app.py", "w") as f:
    f.write(content)

print("Valid error handler injected!")
