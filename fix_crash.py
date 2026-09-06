import py_compile

# First, test if app.py currently compiles
try:
    py_compile.compile('app.py', doraise=True)
    print("Syntax is OK, checking logic...")
except Exception as e:
    print(f"Syntax Error found in app.py: {e}")

with open("app.py", "r") as f:
    lines = f.readlines()

# Let's clean up any broken tail or bad syntax introduced recently
# We can check if there are duplicate route definitions or syntax issues
print(f"Total lines in app.py: {len(lines)}")
