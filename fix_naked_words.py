filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

fixed_lines = []
bad_tokens = ["AUTHENTICATE", "AUTHORIZATION", "HTTP/", "GET ", "POST ", "PUT ", "DELETE ", "OPTIONS ", "HEAD "]

for line in lines:
    stripped = line.strip()
    
    # Check if line is a naked uppercase word or HTTP artifact leaking into Python scope
    is_naked_token = (
        any(stripped.startswith(token) or stripped == token for token in bad_tokens)
        or (stripped.isupper() and len(stripped) > 2 and not stripped.startswith("#") and "=" not in stripped and "def " not in stripped and "import " not in stripped)
    ) and not stripped.startswith("#") and "=" not in stripped and "return" not in stripped and "print" not in stripped and "def " not in stripped and "import " not in stripped and "class " not in stripped and ":" not in stripped

    if is_naked_token:
        print(f"Commenting out leaked global token: {stripped}")
        fixed_lines.append("# [Auto-Fixed Leaked Token] " + line)
    else:
        fixed_lines.append(line)

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("Leaked global tokens cleaned up successfully!")
