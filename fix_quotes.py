with open("app.py", "r") as f:
    content = f.read()

# Count triple quotes
tri_single = content.count("'''")
tri_double = content.count('"""')

print(f"Count of \"''': {tri_single}")
print(f"Count of \"\"\"\": {tri_double}")

if tri_single % 2 != 0:
    print("WARNING: Unclosed ''' found! An HTML template string is broken.")
if tri_double % 2 != 0:
    print("WARNING: Unclosed \"\"\" found!")

