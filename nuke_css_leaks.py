filename = "app.py"
with open(filename, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

clean_lines = []
css_keywords = ["-webkit-", "background:", "border-radius:", "margin:", "padding:", "color:", "font-family:", "box-shadow:"]

for line in lines:
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    # If indentation is 0 or low, and it contains CSS styles without python string wrappers
    is_naked_css = any(kw in stripped for kw in css_keywords) and not stripped.startswith(("#", "f\"", "f'", "\"", "'", "print", "return"))
    
    if is_naked_css or "::-webkit" in stripped:
        print(f"Nuking leaked CSS: {stripped}")
        clean_lines.append("# [Naked CSS Nuked] " + line)
    else:
        clean_lines.append(line)

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(clean_lines)

try:
    compile("".join(clean_lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly after nuking CSS leaks.")
except Exception as e:
    print(f"Compilation error remaining: {e}")
