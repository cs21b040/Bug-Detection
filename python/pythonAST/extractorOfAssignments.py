import ast
import astor

def visitCode(py_ast, locationMap, path, allAssignments, fileID):
    totalAssignments = 0
    totalAssignmentsConsidered = 0
    assignments = []

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            nonlocal totalAssignments, totalAssignmentsConsidered
            totalAssignments += 1

            lhs = node.targets[0]
            rhs = node.value

            if isinstance(lhs, ast.Name) and isinstance(rhs, ast.Name):
                nameOfLHS = lhs.id
                nameOfRHS = rhs.id

                if nameOfLHS and nameOfRHS:
                    locString = f"{path} : {node.lineno} - {node.lineno}"
                    typeOfRHS = type(rhs).__name__
                    assignment = {
                        'lhs': nameOfLHS,
                        'rhs': nameOfRHS,
                        'rhsType': typeOfRHS,
                        'src': locString
                    }
                    totalAssignmentsConsidered += 1
                    assignments.append(assignment)

    Visitor().visit(py_ast)
    allAssignments.extend(assignments)

    print(f"Added assignments. Total now: {len(allAssignments)}")
    print(f"Considered assignments: {totalAssignmentsConsidered} out of {totalAssignments} ({round(100 * totalAssignmentsConsidered / totalAssignments)}%)")