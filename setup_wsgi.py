# 1. Create a clean WSGI wrapper file that Vercel can easily read
with open("wsgi.py", "w") as f:
    f.write("from app import app\napplication = app\n")

# 2. Create/Update vercel.json to explicitly point to wsgi.py
vercel_config = """{
  "builds": [
    {
      "src": "wsgi.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "wsgi.py"
    }
  ]
}
"""

with open("vercel.json", "w") as f:
    f.write(vercel_config)

print("WSGI wrapper and vercel.json configured successfully!")
