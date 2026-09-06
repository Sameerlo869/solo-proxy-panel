filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for idx, line in enumerate(lines):
    if "def api_verify():" in line:
        start_idx = idx - 1 if idx > 0 and "@app.route" in lines[idx-1] else idx
        break

if start_idx != -1:
    end_idx = start_idx
    while end_idx < len(lines):
        if lines[end_idx].strip().startswith("def ") and end_idx != start_idx:
            break
        if lines[end_idx].strip().startswith("@app.route") and end_idx != start_idx:
            break
        end_idx += 1
    
    clean_verify = [
        "@app.route('/api/verify', methods=['GET', 'POST'])\n",
        "def api_verify():\n",
        "    db = GistDB.load()\n",
        "    k, srv = request.args.get('key'), request.args.get('service')\n",
        "    if not k or not srv:\n",
        "        return jsonify({\"status\": False, \"msg\": \"Missing key or service\"}), 400\n",
        "    if is_rate_limited(request.remote_addr) or is_rate_limited(k):\n",
        "        return jsonify({\"status\": False, \"msg\": \"Rate limit exceeded\"}), 429\n",
        "    key_obj = db.get('keys', {}).get(k)\n",
        "    if not key_obj or key_obj.get('revoked') or now_ts() > key_obj.get('expiry', 0):\n",
        "        return jsonify({\"status\": False, \"msg\": \"Invalid/Revoked/Expired Key\"}), 403\n",
        "    if 0 < key_obj.get('limit', 0) <= key_obj.get('used', 0):\n",
        "        return jsonify({\"status\": False, \"msg\": \"Quota Exhausted\"}), 429\n",
        "    if srv not in key_obj.get('assigned_services', []):\n",
        "        return jsonify({\"status\": False, \"msg\": \"Unauthorized Service\"}), 403\n",
        "    srv_obj = db.get('services', {}).get(srv)\n",
        "    if not srv_obj or not srv_obj.get('active', True):\n",
        "        return jsonify({\"status\": False, \"msg\": \"Service Inactive/NotFound\"}), 404\n",
        "    return jsonify({\"status\": True, \"msg\": \"Verified\", \"target\": srv_obj.get('target_url')})\n\n"
    ]
    lines[start_idx:end_idx] = clean_verify

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
