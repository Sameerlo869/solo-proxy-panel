with open("app.py", "r") as f:
    lines = f.readlines()

print("--- ACTIVE (UNCOMMENTED) TRIPLE QUOTES ---")
count = 0
for idx, line in enumerate(lines):
    stripped = line.strip()
    # Check if line contains ''' or starts with ''' and is NOT a comment
    if "'''" in stripped and not stripped.startswith("#"):
        count += 1
        print(f"Line {idx+1}: {stripped}")

print(f"Total active triple-quote occurrences found: {count}")
