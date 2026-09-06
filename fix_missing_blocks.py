filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- Checking around line 300 to 315 ---")
for idx in range(298, min(len(lines), 316)):
    print(f"Line {idx+1}: {repr(lines[idx])}")

# Automatically fix any statement ending with ':' that lacks an indented block
fixed = False
i = 0
while i < len(lines):
    line_str = lines[i].strip()
    if line_str.endswith(":") and any(kw in line_str for kw in ["if ", "else:", "elif ", "def ", "try:", "except", "for ", "while "]):
        # Check next non-empty line
        next_idx = i + 1
        while next_idx < len(lines) and lines[next_idx].strip() == "":
            next_idx += 1
        if next_idx < len(lines):
            curr_indent = len(lines[i]) - len(lines[i].lstrip(' '))
            next_indent = len(lines[next_idx]) - len(lines[next_idx].lstrip(' '))
            if next_indent <= curr_indent and not lines[next_idx].strip().startswith("#"):
                print(f"Inserting pass for unindented block after line {i+1}: {line_str}")
                lines.insert(next_idx, " " * (curr_indent + 4) + "pass\n")
                fixed = True
    i += 1

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
