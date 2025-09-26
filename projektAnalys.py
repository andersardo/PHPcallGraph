"""
Gör staisk callgraf för ett helt projekt
html innehållsförteckning filer,externa anrop, mm
"""
import sys
import os
import subprocess
from pathlib import Path
import pydotplus

try:
    projDir = sys.argv[1]
    print(f"Projektkatalog={projDir}")
    if not os.path.isdir(projDir):
        help(f"'{projDir}' är inte en katalog")
except Exception as e:
    sys.exit(f"{projDir} är inte en katalog {e}")

# Gå igenom alla PHP-filer i projdDir utom 'smarty' och 'Dis*'
done = []
totNotCalled = set()
totExt = set()
for f in Path(projDir).rglob('*.php'):
    phpFil = f"{f}"
    #if not 'MSPDO1' in phpFil: continue #DEB
    if 'smarty' not in phpFil and 'Web/Dis' not in phpFil:
        print('Analyserar', phpFil)
        filnamn = os.path.split(phpFil)[1]
        try:
            cmd = ' '.join(['python3', 'callGraph.py', projDir, phpFil, f"> ./data/{filnamn.replace('.php', '.log')}"])
            res = subprocess.check_output(cmd, shell=True)
            with open(f"./data/{filnamn.replace('.php', '.log')}", 'r') as lg:
                res = lg.read()
            print('Res=', res)
        except Exception as e:
            print('  Exception', e)
            res = ''
        #Anlys av output
        #samla inte anropade funktioner
        if res:
            for line in res.splitlines():
                if line.startswith('Inte anropade funktioner: '):
                    for func in line.replace('Inte anropade funktioner: ', '').split(', '):
                        totNotCalled.add(func)
                elif line.startswith('Externa anrop: '):
                    for fil in line.replace('Externa anrop: ', '').split(', '):
                        totExt.add(f"{fil};{phpFil}")  # (From, To)
                        print(f"External i {phpFil}: {fil} -> {phpFil}")
        done.append(phpFil)
    else:
        print("Skippar", phpFil)
#print(totNotCalled)
#print(totExt)
graph = pydotplus.graphviz.Graph(graph_name="projCallGraf", graph_type="digraph",
                                 overlap=False, rankdir = 'LR', ranksep = 0.25, nodesep=0.3)
with open('./data/top_index.html', 'w') as html:
    html.write(f"""<!DOCTYPE html>
    <html>
    <head>
    <title>Statiska call-grafer för {projDir}</title>
    </head>
    <body>
    <h1>Statiska call-grafer för {projDir}</h1>
    """)
    html.write("<table>\n")
    html.write("<tr><th>Katalog</th><th>Fil</th><th>Log-fil</th></tr>\n")
    for fil in sorted(done):
        (dir, filnamn) = os.path.split(fil)
        dir = f"{dir}/".replace(projDir, '')
        filnamn = filnamn.replace('.php', '')
        html.write(f"<tr><td>./{dir}</td><td><a href='{filnamn}.html'>{filnamn}</a></td>")
        html.write(f"<td><a href='{filnamn}.log'>Log</a></td></tr>\n")
    html.write("</table>\n")
    #Inte anropade
    #  totNotCalled
    html.write("<h2>Inte använda funktioner</h2>\n")
    html.write(', '.join(sorted(list(totNotCalled))))
    #Externa anrop
    # Gör graf av totExt vilka filer som anropar andra filer
    html.write("<h2>Projekt call-graf (filer)</h2>\n")
    nodeIds = {} #maps name to Id
    id = 0
    for ext in sorted(list(totExt)):
        (src, to) = ext.split(';')
        srcFil = os.path.split(src)[1]
        toFil = os.path.split(to)[1]
        try:
            srcId = nodeIds[srcFil]
        except:
            id += 1
            nodeIds[srcFil] = id
            srcId = id
            graph.add_node(pydotplus.graphviz.Node(name=srcId, shape='box', label=f'"{srcFil}"', tooltip=f"{src}"))
        try:
            toId = nodeIds[toFil]
        except:
            id += 1
            nodeIds[toFil] = id
            toId = id
            graph.add_node(pydotplus.graphviz.Node(name=toId, shape='box', label=f'"{toFil}"', tooltip=f"{to}"))
        graph.add_edge(pydotplus.graphviz.Edge(src=srcId, dst=toId))
    with open('./data/projCallGraf.dot', 'w') as f:
        f.write(graph.to_string())
    os.system(f"dot -Tsvg ./data/projCallGraf.dot > ./data/projCallGraf.svg")
    html.write("<img src='projCallGraf.svg'><p>\n")
    html.write("<a href='LOG'>Log för hela körningen</a>\n")
    html.write("</body>\n</html>\n")
