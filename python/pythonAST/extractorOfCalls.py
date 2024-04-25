import ast
import os
import pyExtractionUtil as util

min_args=2
maxLenghtOfCalleeAndArgs=200

def token_to_string(t):
    if isinstance(t, str):
        print(f"Expected a token, but got a string: {t}")
        return t

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

def visitCode(ast_tree, locationMap, path, allCalls, fileID):
    print("Reading file: " + path)
    function_to_parameters={}
    function_counter=0
    class FirstPass(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            nonlocal function_counter
            function_counter += 1
            if len(node.args.args) > 1:
                function_name = node.name
                if function_name:
                    if function_name not in function_to_parameters:
                        parameter_names = ["ID:" + arg.arg for arg in node.args.args]
                        function_to_parameters[function_name] = parameter_names

    FirstPass().visit(ast_tree)

    '''
    calls = []
    parent_stack = []
    call_counter = 0
    '''
    call_with_parameter_name_counter = 0
    class CallExtractor(ast.NodeVisitor):
        def __init__(self, function_to_parameters):
            self.calls = []
            self.function_to_parameters = function_to_parameters  # string to array of strings

        def visit_Call(self, node):
            nonlocal call_with_parameter_name_counter
            if len(node.args) < min_args:
                return
            """ Visit again """
            callee_string = ""
            base_string = ""
            if isinstance(node.func, ast.Attribute):
                callee_string = "ID:" + node.func.attr
                if isinstance(node.func.value, ast.Name):
                    base_string = "ID:" + node.func.value.id
            elif isinstance(node.func, ast.Name):
                callee_string = "ID:" + node.func.id

            if not callee_string and not base_string:
                return

            argument_strings = []
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    argument_strings.append("ID:" + arg.id)
                elif isinstance(arg, ast.Str) or isinstance(arg, ast.Constant):
                    argument_strings.append("LIT:" + str(arg.value))
                else:
                    argument_strings.append(ast.dump(arg))

            argument_types = [type(arg).__name__ for arg in node.args]

            parameters = []
            found_parameter = False
            for i, arg in enumerate(argument_strings):
                parameter = ""  # use empty parameter name if nothing else known
                if callee_string in self.function_to_parameters:
                    if i < len(self.function_to_parameters[callee_string]):
                        parameter = self.function_to_parameters[callee_string][i]
                        found_parameter = True
                parameters.append(parameter)

            if found_parameter:
                call_with_parameter_name_counter += 1

            if len(argument_strings) >= min_args:
                self.calls.append({
                    "base": base_string,
                    "callee": callee_string,
                    "arguments": argument_strings,
                    "argumentTypes": argument_types,
                    "parameters": parameters,
                    "src": f"{path} : {node.lineno} - {node.end_lineno}",
                    "filename": path
                })

        def visit_FunctionDef(self, node):
            function_name = "ID:" + node.name
            parameter_names = [arg.arg for arg in node.args.args]
            self.function_to_parameters[function_name] = parameter_names
            self.generic_visit(node)

    def extract_calls_from_code(code):
        tree = ast.parse(code)
        extractor = CallExtractor(function_to_parameters)
        extractor.visit(tree)
        return extractor.calls
    
    allCalls.extend(extract_calls_from_code(open(path).read()))