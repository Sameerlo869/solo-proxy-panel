filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("--- BEFORE FIX (Lines 62 to 75) ---")
for idx in range(61, min(len(lines), 76)):
    print(f"Line {idx+1}: {repr(lines[idx])}")

# Let's clean up indentation for lines around 65-75 where GistDB save happens
for idx in range(len(lines)):
    if "requests.patch" in lines[idx] or ("GIST_URL" in lines[idx] and "patch" in lines[idx]):
        # Ensure it has exactly 4 spaces indentation (standard function body indent)
        lines[idx] = "    " + lines[idx].lstrip()
        # Also fix subsequent continuation lines of this request
        j = idx + 1
        while j < len(lines) and (not lines[j].strip().startswith("def ") and not lines[j].strip().startswith("class ") and not lines[j].strip().startswith("if ") and not lines[j].strip().startswith("try:")):
            if lines[j].strip() != "":
                lines[j] = "        " + lines[j].lstrip()
            j += 1

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("--- AFTER FIX ---")
for idx in range(61, min(len(lines), 76)):
    print(f"Line {idx+1}: {repr(lines[idx])}")

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly.")
except Exception as e:
    print(f"Compilation Error: {e}")
