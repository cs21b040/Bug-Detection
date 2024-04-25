import subprocess
import sys
import os
import time
import json
import pyExtractionUtil as util
import extractorOfCalls as ec

usage = "\
Two usage modes:\n\
  1) extractFromPy.py <what> --parallel N <fileList.txt> <dir>\n\
     Analyze all files in <dir> that are listed in <fileList.txt>, using N parallel instances.\n\
     If <fileList.txt> is \"all\", analyze all files in <dir>.\n\
  2) extractFromJS.js <what> --files <list of files> [--outfile <file>]:\n\
     Analyze the list of files.\n\
\n\
The <what> argument must be one of:\n\
  tokens\n\
  calls\n\
  callsMissingArg\n\
  assignments\n\
  binOps\n\
"
filesPerParallelInstance = 200

fileToIDFileName = "fileIDs.json"

""" def spawn_single_instance(worklist, what):
    print(f"Left in worklist: {len(worklist)}. Spawning an instance.")
    if worklist:
        py_files = worklist.pop()
        args_to_pass = ["python3", what, "--files "] + py_files
        cmd = subprocess.Popen(args_to_pass, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while True:
            output = cmd.stdout.readline()
            if output == '' and cmd.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = cmd.poll()

        print(f"Instance has finished with exit code {rc}")
        if worklist:
            spawn_single_instance(worklist, what)

 """
def getOrCreateFileToID(files, file_to_id_file_name):
    try:
        with open(file_to_id_file_name, 'r') as f:
            file_to_id = json.load(f)
    except FileNotFoundError:
        file_to_id = {}

    max_id = max(file_to_id.values(), default=1)

    have_added = False
    for file in files:
        if file not in file_to_id:
            max_id += 1
            file_to_id[file] = max_id
            have_added = True

    if have_added:
        with open(file_to_id_file_name, 'w') as f:
            json.dump(file_to_id, f, indent=2)

    return file_to_id
    

def visit_file(py_file, extractor, all_data, file_id):
    code = ""
    print(py_file)
    with open(py_file, 'r') as f:
        code = f.read()
    
    tokens = util.get_tokens(code)
    ast = util.getAST(code)
    if tokens and ast:
        #location_map = util.computeLocationMap(tokens)
        location_map = {}
        extractor.visitCode(ast, location_map, py_file, all_data, file_id)
    else :

        print(f"Error in file {py_file}")

    

fileName = ""
args = sys.argv[1:]
what = args[0]
if what not in ["tokens", "calls", "assignments", "callsMissingArg", "binOps"]:
    print(usage)
    sys.exit(1)
if(args[1] == "--parallel"):
    pass
elif(args[1] == "--files"):
    extractor = None
    if what == "tokens":
        extractor = __import__("extractorOfTokens")
    elif what == "calls":
        extractor = __import__("extractorOfCalls")
    elif what == "assignments":
        extractor = __import__("extractorOfAssignments2")
    elif what == "binOps":
        extractor = __import__("extractorOfBinOps")
    else:
        print(usage)
        sys.exit(1)
    allData = []
    args = args[2:]
    pyFiles = []
    for i in range(len(args)):
        if args[i] == "--outfile":
            fileName = args[i + 1]
            break
        pyFiles.append(args[i])
    fileToID = getOrCreateFileToID(pyFiles, fileToIDFileName)
    for pyFile in pyFiles:
        fileID = fileToID[pyFile]
        if(what == "tokens"):
            extractor.visitFile(pyFile, allData)
        else:
            visit_file(pyFile, extractor, allData, fileID)

    if not fileName:
        fileName = f"{what}_{int(time.time())}.json"

    print(f"Writing {len(allData)} items to file {fileName}")

    with open(fileName, 'w') as f:
        f.write(json.dumps(allData, indent=2))

else:
    print(usage)
    sys.exit(1)
    