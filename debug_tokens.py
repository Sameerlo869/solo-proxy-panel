import tokenize

with open("app.py", "rb") as f:
    try:
        for tok in tokenize.tokenize(f.readline):
            if tok.start[0] >= 1020 and tok.start[0] <= 1165:
                if tok.type == tokenize.STRING:
                    print(f"STRING: {tok.start} to {tok.end}")
    except Exception as e:
        print(f"Tokenizer Error Caught: {e}")
