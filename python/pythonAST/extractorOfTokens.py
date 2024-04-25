import os
from pyExtractionUtil import get_tokens, tokens_to_strings

def visitFile(path, allTokenSequences):
    print(f"Reading {path}")

    if os.path.exists(path):
        with open(path, 'r') as file:
            code = file.read()
            tokens = get_tokens(code)
            if tokens is not None:
                allTokenSequences.append(tokens_to_strings(tokens))
            else:
                print(f"Ignoring file with parse errors: {path}")
    else:
        print(f"File does not exist: {path}")