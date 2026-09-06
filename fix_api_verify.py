filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

start = -1
for i, line in enumerate(lines):
    if line.strip().startswith("def api_verify():"):
        start = i
        break

if start != -1:
    print(f"Found api_verify at line {start+1}")
    end = start + 1
    while end < len(lines):
        if lines[end].strip().startswith("def ") or lines[end].strip().startswith("@app.route") or lines[end].strip().startswith("# ---"):
            break
        end += 1
    
    # Clean, perfectly indented api_verify function body
    clean_verify = [
        "@app.route('/api/verify', methods=['GET', 'POST'])\n",
        "def api_verify():\n",
        "    db = GistDB.load()\n",
        "    k, srv = request.args.get('key'), request.args.get('service')\n",
        "    if not k or not srv: return jsonify({\"status\": False, \"msg\": \"Missing key or service\"}), 400\n",
        "    if is_rate_limited(request.remote_addr) or is_rate_limited(k):\n",
        "        return jsonify({\"status": False, \"msg\": \"Rate limit exceeded\"}), 429\n",
        "    key_obj = db.get('keys', {}).get(k)\n",
        "    if not key_obj or key_obj.get('revoked') or now_ts() > key_obj.get('expiry', 0):\n",
        "        return jsonify({\"status": False, \"msg\": \"Invalid/Revoked/Expired Key\"}), 403\n",
        "    if 0 < key_obj.get('limit', 0) <= key_obj.get('used', 0):\n",
        "        return jsonify({\"status": False, \"msg\": \"Quota Exhausted\"}), 429\n",
        "    if srv not in key_obj.get('assigned_services', []):\n",
        "        return jsonify({\"status": False, \"msg\": \"Unauthorized Service\"}), 403\n",
        "    srv_obj = db.get('services', {}).get(srv)\n",
        "    if not srv_obj or not srv_obj.get('active', True):\n",
        "        return jsonify({\"status": False, \"msg\": \"Service Inactive/NotFound\"}), 404\n",
        "    return jsonify({\"status\": True, \"msg\": \"Verified\", \"target\": srv_obj.get('target_url')})\n\n"
    ]
    # Replace from the route decorator if present right before start, else just start
    dec_idx = start - 1 if start > 0 and "@app.route" in lines[start-1] else start
    lines[dec_idx:end] = clean_verify

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
