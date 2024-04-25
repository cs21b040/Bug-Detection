import ast

def visitCode(py_ast, locationMap, path, allBinOps, fileIDStr):
    print("Reading " + path)

    totalBinOps = 0
    totalBinOpsConsidered = 0
    parentStack = []
    binOps = []

    valid_types = {"Module", "FunctionDef", "Assign", "Expr", "Call", "If", "For", "While", "Return", "Import", "ImportFrom", "ClassDef", "Try", "ExceptHandler", "Raise", "With", "List", "Tuple", "Dict", "Set", "Str", "Bytes", "Num", "NameConstant", "Yield", "YieldFrom", "Compare", "BoolOp", "BinOp", "UnaryOp", "Lambda"}

    class Visitor(ast.NodeVisitor):
        def visit(self, node):
            nonlocal totalBinOps, totalBinOpsConsidered

            parentStack.append(node)  # Add current node to parent stack

            if isinstance(node, ast.BinOp):
                totalBinOps += 1
                leftName = 'ID:' + node.left.id if isinstance(node.left, ast.Name) else ('LIT:' + str(node.left.value) if isinstance(node.left, ast.Constant) else None)
                rightName = 'ID:' + node.right.id if isinstance(node.right, ast.Name) else ('LIT:' + str(node.right.value) if isinstance(node.right, ast.Constant) else None)
                leftType = type(node.left).__name__
                rightType = type(node.right).__name__
                parentName = type(parentStack[-2]).__name__ if len(parentStack) > 1 and type(parentStack[-2]).__name__ in valid_types else "Default"  # Get parent name
                grandParentName = type(parentStack[-3]).__name__ if len(parentStack) > 2 and type(parentStack[-3]).__name__ in valid_types else "Default"  # Get grandparent name

                if leftName is not None and rightName is not None:
                    locString = f"{path} : {node.lineno} - {node.lineno}"
                    binOp = {
                        'left': leftName,
                        'right': rightName,
                        'op': type(node.op).__name__,
                        'leftType': leftType,
                        'rightType': rightType,
                        'parent': parentName,
                        'grandParent': grandParentName,
                        'src': locString
                    }
                    binOps.append(binOp)
                    totalBinOpsConsidered += 1

            super().visit(node)

            parentStack.pop()  # Remove current node from parent stack after visiting its children

    Visitor().visit(py_ast)
    allBinOps.extend(binOps)

    print(f"Added binary operations. Total now: {len(allBinOps)}")
    print(f"Considered binary operations: {totalBinOpsConsidered} out of {totalBinOps} ")