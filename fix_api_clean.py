filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find api_verify function index
start_idx = -1
for idx, line in enumerate(lines):
    if "def api_verify():" in line:
        start_idx = idx
        break

if start_idx != -1:
    print(f"Found api_verify at line {start_idx+1}")
    # Find end of function (next def or @app.route)
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].strip().startswith("def ") or lines[end_idx].strip().startswith("@app.route"):
            break
        end_idx += 1
    
    # Re-indent every line in api_verify body to exactly 4 spaces
    for idx in range(start_idx + 1, end_idx):
        if lines[idx].strip() != "":
            lines[idx] = "    " + lines[idx].lstrip()
    print("Normalized api_verify indentation successfully.")

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
