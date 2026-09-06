filename = "app.py"
with open(filename, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's cleanly rewrite lines 60 to 71 where the Gist save block lives
for idx in range(len(lines)):
    if "json.dump(data, f)" in lines[idx]:
        # Clean up the try-except block right after json.dump
        # We will replace lines from here until '--- HELPER FUNCTIONS ---'
        end_idx = idx + 1
        while end_idx < len(lines) and "# --- HELPER FUNCTIONS ---" not in lines[end_idx]:
            end_idx += 1
        
        clean_block = [
            "        try:\n",
            "            requests.patch(\n",
            "                GIST_URL,\n",
            "                headers={\"Authorization\": f\"token {GIST_TOKEN}\"},\n",
            "                json={\"files\": {\"db.json\": {\"content\": json.dumps(data)}}},\n",
            "                timeout=5\n",
            "            )\n",
            "        except Exception:\n",
            "            pass\n",
            "\n"
        ]
        lines[idx+1:end_idx] = clean_block
        break

with open(filename, "w", encoding="utf-8") as f:
    f.writelines(lines)

try:
    compile("".join(lines), filename, 'exec')
    print("SUCCESS! app.py compiled cleanly with zero errors.")
except Exception as e:
    print(f"Compilation Error: {e}")
