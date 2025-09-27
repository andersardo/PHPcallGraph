import os
import sys
import os
import subprocess
import re
from collections import defaultdict
import pydotplus

"""
TODO
Hantera flera klasser i en fil
fixa loop leta efter anrop med instansierade klasser; flera olika instansnamn
tooltip funkar inte i html browsers (svårlöst)
Hantera Kommentarer!!
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
InternalFunctions = []
publicFunctions = []
privateFunctions = []
definition = False
defFunc = ''
Functions = {}
funcId = 0
# Hitta functions
with open(file, 'r') as dbAPI:
    func_pattern = r'(public|private)?(\s+static)?\s+function\s+([^()]+)\('
    class_pattern = r'class\s+([^(\s{]+)\s+{'
    cls = filename
    definition = False
    for line in dbAPI.readlines():
        m = re.search(class_pattern, line)
        if m:
            cls = m.group(1) #HUR HITTA slut klass?
            # Hitta variabelnamn för klassinstanser
            klassVar = set()  #Alla instansnamn för denna klass
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
                        klassVar.add(match.group(1))
                if len(klassVar) == 1 and cls in klassVar:
                    pass
                else:
                    print(f"WARN: Klass {cls} kan ha många instansnamn {klassVar}")
        if definition:
            FunctionDefs[defFunc] += line
        m = re.search(func_pattern, line)
        if m:
            func = m.group(3)
            if func == '__construct':
                continue
            typ = m.group(1)
            definition = True
            defFunc = func
            funcId += 1
            #testa dubblett
            if func in Functions.keys():
                print(f"ERR 1 dubblett-funktion {func}: {line}\n  {Functions[func]}")
            Functions[func] = {'Id': funcId, 'Typ': typ, 'Klass': cls, 'Definition': line.rstrip()}
        m = re.search(r'\)', line)
        if m:
            definition = False
allFuncs = set(Functions.keys())

callGraph = defaultdict(set)
p = '|'.join(list(allFuncs))
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
                funcdef = m.group(1).rstrip()
            continue
        for m in pattern.finditer(line):
            if m:
                callGraph[funcdef].add(m.group(1).rstrip())
                    
graph = pydotplus.graphviz.Graph(graph_name=f"{filename.replace('.php', '')}", graph_type="digraph",
                                 overlap=False, rankdir = 'LR', ranksep = 0.25, nodesep=0.3)

noCallers = set()
defined = set()
externa_anrop = set()
calledFuncs = set()
for func in allFuncs:
    data = Functions[func]
    if data['Klass']:
        label = f"{data['Klass']}:{func}"
    else:
        label = func
    if data['Typ'] == 'private':
        graph.add_node(pydotplus.graphviz.Node(name=data['Id'], style='filled', fillcolor='green',
                                               label=f'"{label}"', tooltip=f"{data['Definition'].rstrip()}"))
    elif data['Typ'] == 'public':
        typ = 'public'
        graph.add_node(pydotplus.graphviz.Node(name=data['Id'], style='filled', fillcolor='gold', shape='box',
                                                label=f'"{label}"', tooltip=f"{data['Definition'].rstrip()}"))
    elif data['Typ'] == '':
        typ = ''
        graph.add_node(pydotplus.graphviz.Node(name=data['Id'], style='filled', fillcolor='green', shape='hexagon',
                                                label=f'"{label}"', tooltip=f"{data['Definition'].rstrip()}"))
    else:
        typ = '?'
        graph.add_node(pydotplus.graphviz.Node(name=data['Id'], style='filled', fillcolor='chartreuse', label=f'"{label}"'))

    if callGraph[func]:
        for f in callGraph[func]:
            graph.add_edge(pydotplus.graphviz.Edge(src=data['Id'], dst=Functions[f]['Id']))
            calledFuncs.add(func)
    # external callers
    # loopa över olika instansnamn FIX
    try:
        if data['Klass']:
            txt = f"{data['Klass']}->{func}"
        else:
            txt = func
        cmd = f'grep -lr -e "{txt}" {projDir}'
        ext = subprocess.check_output(cmd, shell=True)
        if func == 'Person':
            print(f"F={func} {Funktions[func]}")
            print('txt', txt)
            print('ext', ext)
            print()
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
                # Nytt anrop 'func_ext'
                #testa dubblett
                if f"{func}_Ext" in Functions.keys():
                    t = Functions[f"{func}_Ext"]
                    print(f"ERR 2 dubblett-funktion {func}_Ext: {line}\n  {t}")
                funcId += 1
                Functions[f"{func}_Ext"] = {'Id': funcId, 'Typ': 'extAnrop', 'Klass': '', 'Definition': ''}
                graph.add_node(pydotplus.graphviz.Node(name=funcId, style='filled', fillcolor='coral',
                                                       shape='box', label='Extern', tooltip=f"{tt}"))
                for t in tt.splitlines():
                    externa_anrop.add(t)
            else:
                extFunc = tt.rstrip().split('/')[-1].replace('.php', '').rstrip()
                # Nytt anrop externt
                #testa dubblett
                if extFunc not in Functions.keys():
                    funcId += 1
                    Functions[extFunc] = {'Id': funcId, 'Typ': 'extAnrop', 'Klass': '', 'Definition': ''}
                    graph.add_node(pydotplus.graphviz.Node(name=funcId, style='filled', fillcolor='coral', shape='box',
                                                       tooltip=f"{tt}", label=f'"{extFunc}"'))
                externa_anrop.add(tt)
            graph.add_edge(pydotplus.graphviz.Edge(src=funcId, dst=data['Id']))
            calledFuncs.add(func)

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
        html.write("<h2>Externa anrop från:</h2>\n")
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
