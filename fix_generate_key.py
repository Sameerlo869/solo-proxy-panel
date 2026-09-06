filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

start = -1
for i, line in enumerate(lines):
    if line.strip().startswith("def generate_key("):
        start = i
        break

if start != -1:
    print(f"Found generate_key at line {start+1}")
    end = start + 1
    while end < len(lines):
        if lines[end].strip().startswith("def ") or lines[end].strip().startswith("@app.route") or lines[end].strip().startswith("# ---"):
            break
        end += 1
    
    # Normalize indentation of the function body lines to strictly 4 spaces base
    for i in range(start + 1, end):
        if lines[i].strip() != "":
            stripped = lines[i].lstrip(' ')
            # If the line is part of the dictionary definition inside, keep inner indentation (8 spaces), else 4 spaces
            if lines[i].startswith("        ") or lines[i].startswith("         ") or lines[i].startswith("      "):
                # Check if it's inside the dict continuation
                if stripped.startswith("'") or stripped.startswith("\"") or stripped.startswith("}"):
                    lines[i] = "        " + stripped
                else:
                    lines[i] = "    " + stripped
            else:
                lines[i] = "    " + stripped

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
