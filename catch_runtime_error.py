with open("app.py", "r") as f:
    content = f.read()

# Wrap dashboard return or exception nicely
# Let's see if we can inject a try-except inside the dashboard function
target = "def dashboard():"
replacement = """def dashboard():
    try:"""

if target in content and "try:" not in content.split("def dashboard():")[1].split("\n    ")[1]:
    content = content.replace(target, replacement)
    # Find the end of dashboard function or add an except block before return
    # Alternatively, let's add a global exception handler that catches everything cleanly
    error_wrapper = """
@app.errorhandler(Exception)
py_handle_exception(e):
"""
    print("Dashboard wrapped or checking alternative...")

# Let's add a clean Flask error handler that renders the exact traceback on the page
traceback_handler = """
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    return f"<h3>💥 Runtime Exception Caught:</h3><pre>{traceback.format_exc()}</pre>", 500
"""

if "def handle_exception(e):" not in content:
    content = content + "\n" + traceback_handler
    with open("app.py", "w") as f:
        f.write(content)
    print("Traceback error handler added!")

