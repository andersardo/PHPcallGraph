import os
import glob
import re
import sys
from collections import defaultdict
import pydotplus
import subprocess

projDir = sys.argv[1]
file = sys.argv[2]

FunctionDefs = {}
Functions = []
publicFunctions = []
privateFunctions = []
definition = False
defFunc = ''

"""
Ta hand om classer
utöka till att göra för ett helt projekt rekursivt var fil för sig plus förbindelser mellan filer
html innehållsförteckning fileer,externa anrop, mm
"""
#what functions
with open(file) as dbAPI:
    func_pattern = r'(public|private)?\s+function\s+([^()]+)\('
    class_pattern = r'class\s+([^(\s{]+)\s+{'
    definition = False
    for line in dbAPI.readlines():
        m = re.search(class_pattern, line)
        if m:
            cls = m.group(1)
            # Hitta variabelnamn för klassinstanser
            klassVar = set()
            try:
                cmd = ' '.join(['grep', '-r', f"'new {cls}'", projDir])
                find_cls = subprocess.check_output(cmd, shell=True)
            except Exception as e:
                print('Exception', e)
                find_cls = False
            pat = fr'\$([\w]+)\s*=\s*new\s*{cls}\s*\('
            if find_cls:
                for l in find_cls.splitlines():
                    lutf8 = l.decode('utf-8')
                    match = re.search(pat, lutf8)
                    if match:
                        klassVar.add( match.group(1))
            if len(klassVar) == 1 and cls in klassVar:
                pass
            else:
                print(f"WARN: Klass {cls} kan ha många instansnamn {klassVar}")
        if definition:
            FunctionDefs[defFunc] += line
        m = re.search(func_pattern, line)
        if m:
            func = f"{cls}:{m.group(2)}".rstrip()
            FunctionDefs[func] = line
            if m.group(1) == 'private':
                privateFunctions.append(func)
            elif m.group(1) == 'public':
                publicFunctions.append(func)
            else:
                Functions.append(func)
            definition = True
            defFunc = func
        m = re.search(r'\)', line)
        if m:
            definition = False

#print(privateFunctions)
allFuncs = set(privateFunctions + publicFunctions)
#print(allFuncs)
#print(FunctionDefs.keys())

callGraph = defaultdict(set)
used = set()
p = '|'.join(list(allFuncs)).replace(f"{cls}:", '')
pattern = re.compile(r'[\s\>](%s)\(' % p)
defpattern = r'\s+function\s+([^()]+)\('
#function calls
with open(file) as dbAPI:
    i = 0
    funcdef = '?'
    for line in dbAPI.readlines():
        i += 1
        if ' function' in line:   #definitions
            m = re.search(defpattern, line)
            if m:
                funcdef = f"{cls}:{m.group(1)}"
            continue
        for m in pattern.finditer(line):
            if m:
                #if m.group() == 'FileIDFromName': print(f"Found {m.group()} {line}")
                func = f"{cls}:{m.group(1)}".rstrip()
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

graph = pydotplus.graphviz.Graph(graph_name='MSDP01', graph_type="digraph", overlap=False, rankdir = 'LR', ranksep = 0.25, nodesep=0.3)

noCallers = set()
defined = set()
for func in allFuncs:
    if func in unusedFunctions: continue  #exclude unusedfunctions
    if func in privateFunctions:
        typ = 'private'
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='green'
                                               , tooltip=f"{FunctionDefs[func].rstrip()}")) #, obj_dict=None, **attrs)()
    elif func in publicFunctions:
        typ = 'public'
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='gold', shape='box'
                                               , tooltip=f"{FunctionDefs[func].rstrip()}")) #, obj_dict=None, **attrs)()
    else:
        typ = 'extern'
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='red')) #, obj_dict=None, **attrs)()
    #print(f"{typ} function {func}")
    if callGraph[func]:
        #print('  Used by:')
        for f in callGraph[func]:
            #print("    %s" % f)
            graph.add_edge(pydotplus.graphviz.Edge(src=func.replace(':', '_'), dst=f.replace(':', '_')))  #, obj_dict=None, **attrs)
    # external callers
    try:
        cmd = ' '.join(['grep', '-lr', '-e', '\"'+func.replace(':', '->')+'\"', projDir])
        ext = subprocess.check_output(cmd, shell=True)
        #print(f"Ext {ext}")
    except Exception as e:
        #print('Exception', e)
        ext = False
    if ext:
        tt = ''
        lentt = 0
        for l in ext.splitlines():
            lutf8 = l.decode('utf-8')
            if lutf8.endswith('.php') and lutf8 != file:
                tt += f"{lutf8}\n"
                lentt += 1
        if tt:
            if lentt > 1:
                nodeId = f"{func.replace(':', '_')}_ext"
                graph.add_node(pydotplus.graphviz.Node(name=nodeId.rstrip(), style='filled', fillcolor='coral',
                                                       shape='box', label='External', tooltip=f"{tt}"))
            else:
                nodeId = tt.rstrip().split('/')[-1].replace('.php', '').rstrip()
                if nodeId not in defined:
                    graph.add_node(pydotplus.graphviz.Node(name=nodeId, style='filled', fillcolor='coral', shape='box',
                                                   tooltip=f"{tt}"))
                    defined.add(nodeId)
            graph.add_edge(pydotplus.graphviz.Edge(src=nodeId.rstrip(), dst=func.replace(':', '_')))
calledFuncs = set()
for edge in graph.get_edge_list():
    #print(edge.get_source(), '->', edge.get_destination())
    calledFuncs.add(edge.get_destination().replace('_', ':'))
print('Not called', allFuncs.difference(calledFuncs))
#print('USED functions', used)
#print()
#print(f"UNUSED private functions {unusedFunctions}")
#print(f"??  {used.difference(allFuncs)}")
#print(graph)

#print(f"Ant allFuncs {len(allFuncs)} ; nodes {len(graph.get_node_list())}")
#nodes = []
#for node in graph.get_node_list():
#    nodes.append(node.get_name().replace('_', ':'))
#print('Ant nodes', len(nodes), 'set', len(set(nodes)))
#for n in sorted(nodes):
#    print(n)
#print('all-nodes', allFuncs.difference(set(nodes)))
#print('nodes-all', set(nodes).difference(set(allFuncs)))

#  Anv filnamn 
with open('t.dot', 'w') as f:
    f.write(graph.to_string())
os.system('dot -Tsvg t.dot > t.svg')
