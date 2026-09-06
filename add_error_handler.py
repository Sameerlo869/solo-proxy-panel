with open("app.py", "r") as f:
    content = f.read()

error_handler_code = """
@app.errorhandler(Exception)
def handle_server_exception(e):
    import traceback
    return f"<h3>🔥 Server Exception Traceback:</h3><pre>{traceback.format_exc()}</pre>", 500
"""

if "handle_server_exception" not in content:
    content = content + "\n" + error_handler_code
    with open("app.py", "w") as f:
        f.write(content)
    print("Error handler added successfully!")
else:
    print("Error handler already exists.")
