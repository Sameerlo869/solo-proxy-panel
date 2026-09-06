filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

start = -1
for i, line in enumerate(lines):
    if line.strip().startswith("def parse_raw_request("):
        start = i
        break

if start != -1:
    print(f"Found parse_raw_request at line {start+1}")
    end = start + 1
    while end < len(lines):
        if lines[end].strip().startswith("def ") or lines[end].strip().startswith("@app.route"):
            break
        end += 1
    
    clean_func = [
        "def parse_raw_request(raw_text):\n",
        '    res = {"method": "GET", "base_url": "", "endpoint": "", "headers": {}, "body_template": {}, "query_params": {}, "auth_token": ""}\n',
        '    url_m = re.search(r"(https?://[^\\s\'\\"\\\\]+)", raw_text)\n',
        "    if url_m:\n",
        '        parsed_u = urllib.parse.urlparse(url_m.group(1))\n',
        '        res["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"\n',
        '        res["endpoint"] = parsed_u.path\n',
        '        res["query_params"] = {k: f"{{{{{k}}}}}" for k, v in urllib.parse.parse_qsl(parsed_u.query)}\n',
        "    return res\n"
    ]
    lines[start:end] = clean_func

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
