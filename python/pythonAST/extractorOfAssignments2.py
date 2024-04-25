import ast
from pyExtractionUtil import getNameOfASTNode, getTypeOfASTNode

identifierContextWindowSize = 20  # assumption: even number

def visitCode(py_ast, locationMap, path, allAssignments, fileID):
    print("Reading " + path)

    totalAssignments = 0
    totalAssignmentsConsidered = 0

    pastIdentifiers = []
    unfinishedAssignments = []
    parentStack = []
    assignments = []

    class Visitor(ast.NodeVisitor):
        def visit(self, node):
            nonlocal totalAssignments, totalAssignmentsConsidered, unfinishedAssignments

            parentStack.append(node)  # Add current node to parent stack

            if isinstance(node, ast.Name):
                pastIdentifiers.append("ID:" + node.id)

                # finalize assignments with now-available postIdentifierContext
                nbFinished = 0
                for i in range(len(unfinishedAssignments)):
                    unfinishedAssignment = unfinishedAssignments[i]
                    if len(pastIdentifiers) >= unfinishedAssignment['identifierIndex'] + identifierContextWindowSize // 2:
                        postIdentifierContext = pastIdentifiers[unfinishedAssignment['identifierIndex']:unfinishedAssignment['identifierIndex'] + identifierContextWindowSize // 2]
                        unfinishedAssignment['assignment']['context'].extend(postIdentifierContext)
                        totalAssignmentsConsidered += 1
                        assignments.append(unfinishedAssignment['assignment'])
                        nbFinished += 1
                    else:
                        break
                unfinishedAssignments = unfinishedAssignments[nbFinished:]

            if isinstance(node, ast.Assign):
                totalAssignments += 1
                lhs = node.targets[0]
                rhs = node.value

                nameOfLHS = getNameOfASTNode(lhs)
                nameOfRHS = getNameOfASTNode(rhs)
                parentName = type(parentStack[-2]).__name__ if len(parentStack) > 1 else "Default"  # Get parent name
                grandParentName = type(parentStack[-3]).__name__ if len(parentStack) > 2 else "Default"  # Get grandparent name
                preIdentifierContext = pastIdentifiers[max(0, len(pastIdentifiers) - identifierContextWindowSize // 2):]

                if nameOfLHS and nameOfRHS:
                    locString = f"{path} : {node.lineno} - {node.lineno}"
                    typeOfRHS = getTypeOfASTNode(rhs)
                    assignment = {
                        'lhs': nameOfLHS,
                        'rhs': nameOfRHS,
                        'rhsType': typeOfRHS,
                        'parent': parentName,
                        'grandParent': grandParentName,
                        'context': preIdentifierContext,  # postIdentifierContext will get appended later
                        'src': locString
                    }
                    unfinishedAssignments.append({'assignment': assignment, 'identifierIndex': len(pastIdentifiers)})

            super().visit(node)

            parentStack.pop()  # Remove current node from parent stack after visiting its children

    Visitor().visit(py_ast)

    for unfinishedAssignment in unfinishedAssignments:
        postIdentifierContext = pastIdentifiers[unfinishedAssignment['identifierIndex']:unfinishedAssignment['identifierIndex'] + identifierContextWindowSize // 2]
        while len(postIdentifierContext) < identifierContextWindowSize // 2:
            postIdentifierContext.append("")
        unfinishedAssignment['assignment']['context'].extend(postIdentifierContext)
        totalAssignmentsConsidered += 1
        assignments.append(unfinishedAssignment['assignment'])

    allAssignments.extend(assignments)
    print("Added assignments. Total now: " + str(len(allAssignments)))
    print("Considered assignments: " + str(totalAssignmentsConsidered) + " out of " + str(totalAssignments))