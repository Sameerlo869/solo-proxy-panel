filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

import re

# Find and replace the entire parse_raw_request function cleanly
old_func_pattern = re.compile(r'def parse_raw_request\(raw_text\):(.*?)(?=\ndef |\n@app.route|\Z)', re.DOTALL)

new_func = """def parse_raw_request(raw_text):
    res = {"method": "GET", "base_url": "", "endpoint": "", "headers": {}, "body_template": {}, "query_params": {}, "auth_token": ""}
    url_m = re.search(r"(https?://[^\\s'\"\\\\]+)", raw_text)
    if url_m:
        parsed_u = urllib.parse.urlparse(url_m.group(1))
        res["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"
        res["endpoint"] = parsed_u.path
        res["query_params"] = {k: f"{{{{{k}}}}}" for k, v in urllib.parse.parse_qsl(parsed_u.query)}
    return res"""

if old_func_pattern.search(content):
    content = old_func_pattern.sub(new_func, content)
    print("Successfully replaced parse_raw_request function.")
else:
    print("Could not find parse_raw_request function automatically!")

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

try:
    compile(content, filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
