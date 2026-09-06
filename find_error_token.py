import tokenize

tokens = []
try:
    with open("app.py", "rb") as f:
        for tok in tokenize.tokenize(f.readline):
            tokens.append(tok)
    print("No token error found!")
except Exception as e:
    print(f"ERROR CAUGHT: {e}")
    print("\n--- LAST 5 TOKENS BEFORE ERROR ---")
    for t in tokens[-5:]:
        print(f"{tokenize.tok_name[t.type]:<12} {repr(t.string):<30} at {t.start}")
