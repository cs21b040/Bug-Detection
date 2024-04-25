import extractorOfCalls as ec
import pyExtractionUtil as en
import os
code="def f(x,a):\n\tp=a[0]\n\treturn p+x+1\na=[1]\nb=f(5,a)\n"
path = "/home/nikhil/Documents/Class Notes/SE Lab/SE Release 2/python conversion from js/test.py"
hi=[]
with open(py_file, 'r') as f:
    code = f.read()
    ec.visitCode(os.popen('./test.py').read(), {}, path, hi, 0)
    print(hi)