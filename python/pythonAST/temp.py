import ast
import tokenize
from io import BytesIO


def get_name_of_ast_node(node):
    if isinstance(node, ast.Name):
        return "ID:" + node.id
    elif isinstance(node, ast.Call):
        return get_name_of_ast_node(node.func)
    elif isinstance(node, ast.Attribute):
        return get_name_of_ast_node(node.value)
    elif isinstance(node, ast.Constant):
        return "LIT:" + str(node.value)
    elif isinstance(node, ast.UnaryOp):
        return get_name_of_ast_node(node.operand)

def get_kind_of_ast_node(node):
    return type(node).__name__

def get_type_of_ast_node(node):
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    elif isinstance(node, ast.Name):
        return "unknown"
    else:
        return "unknown"

def node_to_string(node):
    if isinstance(node, ast.Name):
        return "ID:" + node.id
    elif isinstance(node, ast.Constant):
        return "LIT:" + str(node.value)
    elif isinstance(node, list):
        return "Array"
    else:
        return type(node).__name__

def token_to_string(token):
    if token.type == tokenize.NAME:
        return "ID:" + token.string
    elif token.type in [tokenize.NUMBER, tokenize.STRING]:
        return "LIT:" + token.string
    else:
        return "STD:" + token.string

def tokens_to_strings(tokens):
    return [token_to_string(token) for token in tokens]

def compute_location_map(tokens):
    lc_location_to_char_location = {}
    for token in tokens:
        lc_start_location = str(token.start[0]) + ":" + str(token.start[1])
        lc_end_location = str(token.end[0]) + ":" + str(token.end[1])
        lc_location_to_char_location[lc_start_location] = token.startpos
        lc_location_to_char_location[lc_end_location] = token.endpos
    return lc_location_to_char_location

def get_location_of_ast_node(node, lc_location_to_char_location):
    lc_start_location = str(node.lineno) + ":" + str(node.col_offset)
    lc_end_location = str(node.end_lineno) + ":" + str(node.end_col_offset)
    start = lc_location_to_char_location[lc_start_location]
    end = lc_location_to_char_location[lc_end_location]
    diff = end - start
    return nb_to_padded_str(start, 6) + nb_to_padded_str(diff, 4)

def nb_to_padded_str(nb, length):
    return str(nb).zfill(length)

def get_name_of_function(function_node):
    if isinstance(function_node, ast.FunctionDef):
        return "ID:" + function_node.name



""" 
    getNameOfASTNode;
    getKindOfASTNode;
    getTypeOfASTNode;
    nodeToString;
    tokenToString;
    tokensToStrings;
    nbToPaddedStr;
    computeLocationMap;
    getLocationOfASTNode;
    getNameOfFunction;



 """