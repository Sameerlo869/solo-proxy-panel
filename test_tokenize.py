import tokenize

with open("app.py", "rb") as f:
    try:
        for tok in tokenize.tokenize(f.readline):
            # Print token type, string, and start/end coordinates
            print(f"{tokenize.tok_name[tok.type]:<12} {repr(tok.string):<30} at {tok.start}")
    except tokenize.TokenError as e:
        print(f"\nTOKENIZER ERROR: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
