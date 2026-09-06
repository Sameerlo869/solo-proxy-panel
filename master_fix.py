import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Remove all duplicate/broken auto-ingest routes and old widgets
content = re.sub(r"@app\.route\('/admin/auto-ingest'.*?return jsonify.*?\n\s*", "", content, flags=re.DOTALL)
content = re.sub(r"def auto_ingest_request\(.*?\n\s*return.*?\n", "", content, flags=re.DOTALL)
content = re.sub(r"\s*<!-- Smart Quick Auto-Ingest Widget -->.*?</script>", "", content, flags=re.DOTALL)

# 2. Balance any unclosed Jinja 'if' blocks before </body> in the HTML template
# Count how many {% if %} are opened vs {% endif %} closed
if_count = content.count("{% if")
endif_count = content.count("{% endif")
if if_count > endif_count:
    diff = if_count - endif_count
    print(f"Balancing template: adding {diff} missing 'endif' tags.")
    content = content.replace("</body>", ("\n{% endif %}\n" * diff) + "</body>")

# 3. Define the clean Auto-Ingest Route
auto_ingest_route = """
@app.route('/admin/auto-ingest', methods=['POST'])
def auto_ingest_request():
    try:
        req_data = request.get_json(silent=True) or {}
        raw_data = request.form.get('raw_text', '') or req_data.get('raw_text', '')
        if not raw_data:
            return jsonify({"status": False, "error": "No raw data provided"}), 400
        
        lines = [l.strip() for l in raw_data.strip().split('\\n') if l.strip()]
        if not lines:
            return jsonify({"status": False, "error": "Empty data"}), 400
        
        first_line_parts = lines[0].split()
        method = first_line_parts[0] if len(first_line_parts) > 0 else "GET"
        path = first_line_parts[1] if len(first_line_parts) > 1 else "/"
        
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                parts = line.split(':', 1)
                headers[parts[0].strip().lower()] = parts[1].strip()
                
        tenant = headers.get('x-tenant', headers.get('x-partner-id', 'turtlemint'))
        broker = headers.get('x-broker', 'turtlemint')
        auth = headers.get('authorization', '')
        
        db = GistDB.load()
        if not isinstance(db, dict):
            db = {"services": [], "companies": []}
        if 'services' not in db:
            db['services'] = []
            
        service_entry = {
            "code": path.strip('/').replace('/', '_')[:30],
            "path": path,
            "method": method,
            "tenant": tenant,
            "broker": broker,
            "auth": auth,
            "headers": headers,
            "active": True
        }
        
        db['services'].append(service_entry)
        GistDB.save(db)
        
        return jsonify({
            "status": True, 
            "message": "Successfully auto-parsed and saved to database!", 
            "extracted": {
                "path": path,
                "tenant": tenant,
                "broker": broker,
                "has_token": bool(auth)
            }
        })
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
"""

# 4. Define the UI Widget
proper_widget = """
    <!-- Smart Quick Auto-Ingest Widget -->
    <div class="glass card" style="margin-bottom: 25px; border-color: var(--neon); margin-top: 20px;">
        <div style="font-size:16px; color:var(--neon); margin-bottom:10px;"><i class="fa-solid fa-wand-magic-sparkles"></i> Instant Raw Request Auto-Catcher</div>
        <p style="font-size:12px; color:#a0a0a0; margin-bottom:10px;">Yahan apni raw cURL ya HTTP request paste karo. Tenant, Broker, Token aur Path sab apne aap extract hokar database mein save ho jayega!</p>
        <textarea id="rawRequestInput" rows="4" placeholder="Paste raw HTTP request or cURL here..." style="width:100%; padding:10px; background:rgba(0,0,0,0.4); border:1px solid var(--border); color:#fff; border-radius:6px; outline:none; margin-bottom:10px;"></textarea>
        <button class="btn" onclick="autoIngestRaw()"><i class="fa-solid fa-bolt"></i> Auto-Parse & Save Instantly</button>
        <div id="ingestResult" style="margin-top:10px; font-size:13px; font-family:monospace;"></div>
    </div>
    
    <script>
    async function autoIngestRaw() {
        const rawText = document.getElementById("rawRequestInput").value;
        const resDiv = document.getElementById("ingestResult");
        if(!rawText) {
            resDiv.innerHTML = "<span style='color:#d9534f;'>Please paste a request first!</span>";
            return;
        }
        resDiv.innerHTML = "<span style='color:var(--neon);'>Processing & extracting...</span>";
        
        try {
            let response = await fetch("/admin/auto-ingest", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ raw_text: rawText })
            });
            let data = await response.json();
            if(data.status) {
                resDiv.innerHTML = `<span style='color:#5cb85c;'>✓ Success! Saved path: <b>${data.extracted.path}</b> (Tenant: ${data.extracted.tenant}, Token: ${data.extracted.has_token ? "Captured" : "None"})</span>`;
                setTimeout(() => location.reload(), 1500);
            } else {
                resDiv.innerHTML = `<span style='color:#d9534f;'>Error: ${data.error}</span>`;
            }
        } catch(e) {
            resDiv.innerHTML = `<span style='color:#d9534f;'>Request failed: ${e}</span>`;
        }
    }
    </script>
"""

# Append route to python code and widget right before </body>
content = content + "\n" + auto_ingest_route
content = content.replace("</body>", proper_widget + "\n</body>")

with open("app.py", "w") as f:
    f.write(content)

print("Master cleanup completed successfully!")
