import ast
import tokenize
import io
import os
from io import BytesIO
import astpretty
maxLengthOfTokens = 100
def get_tokens(code):
    # try:
    #     tokens = []
    #     for token in tokenize.tokenize(BytesIO(code.encode('utf-8')).readline):
    #         tokens.append(token)
    #     return tokens
    # except Exception as e:
    #     pass
    l=[]
    for i in list(tokenize.generate_tokens(io.StringIO(code).readline)):
        l.append(i)
    return l

def getAST(code):
    return ast.parse(code)

def getASTPretty(code):
    return astpretty.pprint(getAST(code),show_offsets=False)

def getLines(code):
    lines=[]
    for i in code.split("\n"):
        lines.append(len(i))


def getNameOfASTNode(node):
    if isinstance(node, ast.Name):
        return "ID:" + node.id
    elif isinstance(node, ast.Call):
        return getNameOfASTNode(node.func)
    elif isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
        return getNameOfASTNode(node.value)
    elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
        return getNameOfASTNode(node.attr)
    elif isinstance(node, ast.Constant):
        return "LIT:" + str(node.value)
    elif isinstance(node, ast.Name) and node.id == 'self':
        return "LIT:this"
    else:
        return type(node).__name__

def getKindOfASTNode(node):
    if isinstance(node, ast.Name):
        return "ID"
    elif isinstance(node, ast.Call):
        return getKindOfASTNode(node.func)
    elif isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
        return getKindOfASTNode(node.value)
    elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
        return getKindOfASTNode(node.attr)
    elif isinstance(node, ast.Constant):
        return "LIT"
    elif isinstance(node, ast.Name) and node.id == 'self':
        return "LIT"
    else:
        return type(node).__name__

def getTypeOfASTNode(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "str"
        elif isinstance(node.value, int):
            return "int"
        elif isinstance(node.value, float):
            return "float"
        elif node.value is None:
            return "None"
        else:
            return type(node.value).__name__
    elif isinstance(node, ast.Name):
        if node.id == "None":
            return "None"
        else:
            return "unknown"
    elif isinstance(node, ast.NameConstant):
        return type(node.value).__name__
    else:
        return "unknown"

def getLocationOfASTNode(node,):
    pass

def computeLocationMap(tokens):
    lcLocationToCharLocation={}
    for t in tokens:
        lcStartLocation =  str(t.start[0]) + ":" + str(t.start[1])
        lcEndLocation = str(t.end[0]) + ":" + str(t.end[1])
        lcLocationToCharLocation[lcStartLocation] = t.start[1]
        lcLocationToCharLocation[lcEndLocation] = t.end[1]
    return lcLocationToCharLocation
    
def nbToPaddedStr(nb,length):
    return str(nb).zfill(length)

def add_edges(graph, node, parent=None):
    name = type(node).__name__
    graph.node(name, name)
    if parent is not None:
        graph.edge(parent, name)
    for child in ast.iter_child_nodes(node):
        add_edges(graph, child, parent=name)

def ast_to_dot(code):
    tree = ast.parse(code)
    graph = graphviz.Digraph()
    add_edges(graph, tree)
    return graph

def tokens_to_strings(tokens):
    return list(map(token_to_string, tokens))

# def token_to_string(token):
#     if isinstance(token, int):
#         return str(token)

#     result = ""
#     if token.type.label == identifier_token_type:
#         result = "ID:"
#     elif token.type.label in literal_token_types:
#         result = "LIT:"
#     else:
#         result = "STD:"

#     if token.value is None:
#         result += token.type.label
#     elif isinstance(token.value, str) or isinstance(token.value, int):
#         result += str(token.value)
#     elif token.type.label == "regexp":
#         result += str(token.value.value)
#     else:
#         print(f"Unexpected token:\n{token}")

#     return result[:max_length_of_tokens]

def token_to_string(t):
    identifier_token_type = tokenize.NAME
    literal_token_types = [tokenize.NUMBER, tokenize.STRING]
    result = ''

    if t.type == identifier_token_type:
        result = "ID:"
    elif t.type in literal_token_types:
        result = "LIT:"
    else:
        result = "STD:"

    if t.string is None:
        result += t.type
    elif isinstance(t.string, str) or isinstance(t.string, int):
        result += str(t.string)
    else:
        print(f"Unexpected token:\n{t}")

    return result[:maxLengthOfTokens]