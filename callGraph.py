import os
import sys
import os
import subprocess
import re
from collections import defaultdict
import pydotplus

"""
TODO
Lös typningen av funktioner 'private', public', ''
Hantering funktioner utanför klasser
id på klasser stf namn + sätt label
datastruktur för klass: Namn, Id, Typ, Klass
fixa loop leta efter anrop med instansierade klassr; flera olika instansnamn
tooltip funkar inte i html browsers (svårlöst)

"""

def help(msg=''):
    print("python3 callGraph.py <Path_till_projektkatalog> <Path_till_PHP-fil>")
    print()
    print("Skapar HTML-fil med en statisk call-graf för angiven PHP-fil, inkluderande anrop från andra PHP-filer i projektkatalogen.")
    print("""Pilarna anger att en fuktion använder en annan funktion.
Röd anger anrop från en annan fil.
Gul anger public functions.
Grön anger private functions.
    """)
    sys.exit(msg)

try:
    projDir = sys.argv[1]
    if not os.path.isdir(projDir):
        help(f"'{projDir}' är inte en katalog")
    file = sys.argv[2]
    if not os.path.isfile(file):
        help(f"'{file}' är inte en fil")
    if not file.endswith('.php'):
        help(f"'{file}' är inte en en PHP-fil")
except Exception as e:
    help(f'Fel i parametrarna till anropet ({e})')

filename = os.path.split(file)[1]
print(f"Analyserar {filename}")
FunctionDefs = {}
Functions = []
publicFunctions = []
privateFunctions = []
definition = False
defFunc = ''

#what functions
with open(file, 'r') as dbAPI:
    func_pattern = r'(public|private)?\s+[\w]+\s+function\s+([^()]+)\('
    class_pattern = r'class\s+([^(\s{]+)\s+{'
    cls = filename
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
                print('Inga resultat:', e)
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
allFuncs = set(privateFunctions + publicFunctions + Functions) # Hantera funktioner utanför klass

callGraph = defaultdict(set)
p = '|'.join(list(allFuncs)).replace(f"{cls}:", '')
pattern = re.compile(r'[\s\>](%s)\(' % p)
defpattern = r'\s+function\s+([^()]+)\('
#function calls
with open(file, 'r') as dbAPI:
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

graph = pydotplus.graphviz.Graph(graph_name=f"{filename.replace('.php', '')}", graph_type="digraph",
                                 overlap=False, rankdir = 'LR', ranksep = 0.25, nodesep=0.3)

noCallers = set()
defined = set()
externa_anrop = set()
for func in allFuncs:
    #if func in unusedFunctions: continue  #exclude unusedfunctions
    if func in privateFunctions:
        typ = 'private'
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='green',
                                               label=f'"{func}"', tooltip=f"{FunctionDefs[func].rstrip()}"))
    elif func in publicFunctions:
        typ = 'public'
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='gold', shape='box',
                                                label=f'"{func}"', tooltip=f"{FunctionDefs[func].rstrip()}"))
    elif func in Functions:
        typ = ''
        graph.add_node(pydotplus.graphviz.Node(name=func.replace(':', '_'), style='filled', fillcolor='green', shape='hexagon',
                                                label=f'"{func}"', tooltip=f"{FunctionDefs[func].rstrip()}"))
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
        #prova grep utan ':'
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
                                                       shape='box', label='Extern', tooltip=f"{tt}"))
                for t in tt.splitlines():
                    externa_anrop.add(t)
            else:
                nodeId = tt.rstrip().split('/')[-1].replace('.php', '').rstrip()
                if nodeId not in defined:
                    graph.add_node(pydotplus.graphviz.Node(name=nodeId, style='filled', fillcolor='coral', shape='box',
                                                   tooltip=f"{tt}"))
                    externa_anrop.add(tt)
                    defined.add(nodeId)
            graph.add_edge(pydotplus.graphviz.Edge(src=nodeId.rstrip(), dst=func.replace(':', '_')))
calledFuncs = set()
for edge in graph.get_edge_list():
    #print(edge.get_source(), '->', edge.get_destination())
    calledFuncs.add(edge.get_destination().replace('_', ':'))

with open(f"./data/{filename.replace('.php', '.dot')}", 'w') as f:
    f.write(graph.to_string())
os.system(f"dot -Tsvg ./data/{filename.replace('.php', '.dot')} > ./data/{filename.replace('.php', '.svg')}")
with open(f"./data/{filename.replace('.php', '.html')}", 'w') as html:
    html.write(f"""<!DOCTYPE html>
    <html>
    <head>
    <title>Statisk call-graf för {filename}</title>
    </head>
    <body>
    <h1>Statisk call-graf för {filename}</h1>
    """)
    if allFuncs.difference(calledFuncs):
        html.write("<h2>Inte anropade funktioner</h2>\n")
        html.write(', '.join(sorted(list(allFuncs.difference(calledFuncs)))))
        print("Inte anropade funktioner:", ', '.join(sorted(list(allFuncs.difference(calledFuncs)))))
        html.write("<p>\n")
    #printa externa_anrop
    if externa_anrop:
        html.write("<h2>Externa anrop</h2>\n")
        html.write(', '.join(sorted(externa_anrop)))
        print("Externa anrop:", ', '.join(sorted(list(externa_anrop))))
    # FIX KOLLA OM det finns graf!
    html.write("<h2>Call-graf</h2>\n")
    html.write("""Röd anger anrop från en annan fil.<br>
Gul anger "public functions".<br>
Grön anger "private functions".<br>
    <p>\n""")
    html.write(f"<img src='{filename.replace('.php', '.svg')}'>\n")
    
    html.write("</body>\n</html>\n")
