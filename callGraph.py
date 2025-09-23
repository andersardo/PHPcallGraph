import os
import glob
import re
import sys
from collections import defaultdict

#dir = "./trunk/Web/disbyt/cmn/prg"
dir = "./trunk/Web/disbyt"
publicFunctions = []
publicFunctionsDefs = {}
privateFunctions = []
privateFunctionsDefs = {}
definition = False
defFunc = ''

Slå ihop de 2 looparna och plocka ut vanliga function också
Lista på externa filer som anropar rutiner - grep -lr <func> subprocess.check_output(['ls', '-l'])
utöka till att göra för ett helt projekt rekursivt var fil för sig plus förbindelser mellan filer
html innehållsförteckning fileer,externa anrop, mm

with open('./MSPDO1.php') as dbAPI:
    #pattern = r'public\s+function\s+([^()]+)\('
    pattern = r'private\s+function\s+([^()]+)\('
    for line in dbAPI.readlines():
        if definition:
            privateFunctionsDefs[defFunc] += line
        m = re.search(pattern, line)
        if m:
            privateFunctions.append(m.group(1))
            privateFunctionsDefs[m.group(1)] = line
            definition = True
            defFunc = m.group(1)
        m = re.search(r'\)', line)
        if m:
            definition = False
with open('./MSPDO1.php') as dbAPI:
    pattern = r'public\s+function\s+([^()]+)\('
    #pattern = r'private\s+function\s+([^()]+)\('
    for line in dbAPI.readlines():
        if definition:
            publicFunctionsDefs[defFunc] += line
        m = re.search(pattern, line)
        if m:
            publicFunctions.append(m.group(1))
            publicFunctionsDefs[m.group(1)] = line
            definition = True
            defFunc = m.group(1)
        m = re.search(r'\)', line)
        if m:
            definition = False

allFuncs = set(privateFunctions + publicFunctions)
#print(allFuncs)
#print( '|'.join(list(allFuncs)))

pattern = re.compile(r'[\s\>](%s)\(' % '|'.join(list(allFuncs)))
#print(r'->(%s)\(' % '|'.join(list(allFuncs)))

defpattern = r'\s+function\s+([^()]+)\('

callGraph = defaultdict(set)

used = set()

with open('./MSPDO1.php') as dbAPI:
    i = 0
    funcdef = '?'
    for line in dbAPI.readlines():
        i += 1
        if ' function' in line:   #definitions
            m = re.search(defpattern, line)
            if m:
                funcdef = m.group(1)
            continue
        for m in pattern.finditer(line):
            if m:
                #if m.group() == 'FileIDFromName': print(f"Found {m.group()} {line}")
                func = m.group(1)
                if func in privateFunctions:
                    typ = 'private'
                elif func in publicFunctions:
                    typ = 'public'
                else:
                    typ = 'extern'
                #if funcdef == 'FileIDs': print(f"Call to {func} ({typ}) found in {funcdef} on line {i}")
                callGraph[funcdef].add(func)
                used.add(func)
unusedFunctions = allFuncs.difference(used).difference(set(publicFunctions))

import pydotplus
graph = pydotplus.graphviz.Graph(graph_name='MSDP01', graph_type="digraph", overlap=False, rankdir = 'LR', ranksep = 0.75)

for func in allFuncs:
    if func in unusedFunctions: continue  #exclude unusedfunctions
    if func in privateFunctions:
        typ = 'private'
        graph.add_node(pydotplus.graphviz.Node(name=func, style='filled', fillcolor='green',
                                               tooltip=f"{privateFunctionsDefs[func].rstrip()}")) #, obj_dict=None, **attrs)()
    elif func in publicFunctions:
        typ = 'public'
        graph.add_node(pydotplus.graphviz.Node(name=func, style='filled', fillcolor='gold', shape='box',
                                               tooltip=f"{publicFunctionsDefs[func].rstrip()}")) #, obj_dict=None, **attrs)()
    else:
        typ = 'extern'
        graph.add_node(pydotplus.graphviz.Node(name=func, style='filled', fillcolor='red')) #, obj_dict=None, **attrs)()
    #print(f"{typ} function {func}")
    #graph.append({'data': {'id': func, 'label': func, 'typ': typ }})
    if callGraph[func]:
        #print(func, callGraph[func])
        #print('  Used by:')
        for f in callGraph[func]:
            #print("    %s" % f)
            #graph.append({'data': {'source': f, 'target': func }})
            graph.add_edge(pydotplus.graphviz.Edge(src=func, dst=f))  #, obj_dict=None, **attrs)
            
    #print("=====================================")

#print('USED functions', used)
#print()
print(f"UNUSED private functions {unusedFunctions}")
#print(f"??  {used.difference(allFuncs)}")
#print(graph)

#head = 'digraph G {charset=utf8; overlap=false; rankdir = LR; ratio = compress; ranksep = 0.25; nodesep = 0.03;fontname=Helvetica; fontsize=16; fontcolor=black; label="'+title+'"; labelloc=t;'

with open('t.dot', 'w') as f:
    f.write(graph.to_string())
os.system('dot -Tsvg t.dot > t.svg')
