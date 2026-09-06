filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if line.strip().startswith("def parse_raw_request("):
        start_idx = idx
        break

if start_idx != -1:
    print(f"Found parse_raw_request at line {start_idx+1}")
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].strip().startswith("def ") or lines[end_idx].strip().startswith("@app.route"):
            break
        end_idx += 1
    
    # Fix indentation for the entire function body
    for i in range(start_idx + 1, end_idx):
        if lines[i].strip() != "":
            # Keep original relative structure or force 4 spaces for body
            stripped = lines[i].lstrip(' ')
            # Check if it's inside an if/for block inside the function
            if lines[i-1].strip().endswith(':') and not lines[i].startswith('    '):
                # If previous line ends with :, indent deeper
                pass
            lines[i] = "    " + stripped

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
