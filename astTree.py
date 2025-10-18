import sys
import os
import re
import subprocess
from pathlib import Path
import json
from collections import defaultdict
import traceback

# Globala variabler
uid = 0
name2Id = {}  #Använda funktioner
defFunk = set()  #id of defined functions (Funk)

#Read list of standard funktions in PHP
stdFunctions = set()
with open('allaPHPstdFunktioner.txt', 'r') as f:
    for line in f.readlines():
        if not ' - ' in line: continue
        if '::' in line: continue
        if '\\' in line: continue
        line = line.strip()
        (name, desc) = line.split(' - ', 1)
        if len(name) <=1: continue
        stdFunctions.add(name.strip())

try:
    projDir = sys.argv[1]
    print(f"Projektkatalog={projDir}")
    if not os.path.isdir(projDir):
        help(f"'{projDir}' är inte en katalog")
except Exception as e:
    sys.exit(f"{projDir} är inte en katalog {e}")

#REMOVE all resultfiles
os.system('rm data/*')

class Node:
    def __init__(self, name, typ, data=''):
        self.name = name.replace(projDir, '')  #Remove start-path
        #FIX? case handling PHP insensitive for case
        self.nameLower = name.replace(projDir, '').lower()  #Remove start-path; case-insensitive 
        self.id = '?'
        if typ in ('Fil', 'Klass', 'Funk', 'Anrop'):
            self.typ = typ
        else:
            sys.exit(f"Okänd typ {typ} för {name}")
        self.data = data
        self.nodes = []
        self.graph = None
        self.varMap = None #??? kolla användning!!!

    def insert(self, nod):
        self.nodes.append(nod)
        return nod
    
    def printTree(self, prefix=''):
        print(f"{prefix}{self.id}: {self.typ} {self.name} {self.data}")
        for typ in ('Klass', 'Funk', 'Anrop'):
            for n in [x for x in self.nodes if x.typ == typ]:
                n.printTree(prefix + '  ')

    def mkGraph(self, graph=None, id=None, prefix=''):
        #Graphviz colors: cornflowerblue, deepskyblue, red, chartreuse, gold, coral, green, yellow
        if not graph:
            self.graph = '' #"digraph testmk {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25; \n"
            graph = self.graph
            ##??done = set()
        if self.typ in ('Fil', 'Klass', 'Funk'):
            #DEB label = f"{self.id} {self.data} {self.name}"
            #label = f"{self.data} {self.name}" #Extended
            label = f"{self.name}"  #Minimal
            color = 'firebrick1'
            if self.typ == 'Fil':
                graph += f'{self.id} [fillcolor="cornflowerblue", label="{label}", style=filled, shape="box"];\n'                
            elif self.typ == 'Klass':
                color = 'coral'
                graph += f'subgraph cluster{self.name} {{graph [style=rounded]  label="KLASS: {label}"\n'
            elif self.typ == 'Funk' and self.data == 'public':
                graph += f'{self.id} [fillcolor="gold", label="{label}", style=filled, shape="box"];\n'
            elif (self.typ == 'Funk') and (self.data == 'private'):
                graph += f'{self.id} [fillcolor="green", label="{label}", style=filled];\n'
            elif self.typ == 'Funk':
                graph += f'{self.id} [fillcolor="yellow", label="{label}", style=filled];\n'
            else:
                graph += f'{self.id} [fillcolor="{color}", label="{label}", style=filled];\n'
            for n in self.nodes:
                graph += n.mkGraph(graph=' ', id=self.id, prefix='  '+prefix)
            if self.typ == 'Klass':
                graph += "}\n"
        elif self.typ == 'Anrop':
            if self.id in defFunk: #Bara länka till använda funktioner
                graph += f"{id} -> {self.id};\n" #Link local function to external function
            #else:
            #    print(f"Inte i defFunk: {self.name}, {self.id}")
        else:
            sys.exit(f"Okänd typ {self.id}: {self.typ} {self.name} {self.data}")
        return graph

    def assignIds(self):  #Alla namn
        global uid
        global name2Id
        if f"{self.name}" in name2Id:
            self.id = name2Id[f"{self.name}"]
        if self.id == '?':
            uid += 1
            self.id = uid
            name2Id[f"{self.name}"] = uid
        for n in self.nodes:
            n.assignIds()

    def usedFunctions(self):  # Alla definierade funktioner i denna fil
        global defFunk
        if self.typ == 'Funk':
            defFunk.add(self.id)
        for n in self.nodes:
            n.usedFunctions()

    def getBeroende(self):
        global AnroparPerFil, DefinieradePerFil
        if self.typ == 'Funk':  #Definierade
            DefinieradePerFil.add(self.name)
        elif self.typ == 'Anrop':  #Anropade
            AnroparPerFil.add(self.name)
        for n in self.nodes:
            n.getBeroende()

class ast():
    def __init__(self, file):
        self.tree = Node(file, 'Fil')
        self.current = [self.tree]
        #get ast
        cmd = f"php parse2data.php {file}"  #get ast as datastruct - Walk recursively
        res = subprocess.check_output(cmd, shell=True)
        self.astData = json.loads(res)
        self.varMap = {}

    def doClass(self, ast):
        name = ast['name'].replace('"', '')
        #print(f"Klass {name} start")
        nod = self.current[-1].insert(Node(name, typ='Klass'))
        self.current.append(nod)
        for key,val in ast.items():
            self.process(val)
        #print(f"Klass {name} end")
        self.current.pop()

    def doMethod(self, ast):
        #??name = f"{clsName}_" + ast['name'].replace('"', '')
        name = ast['name'].replace('"', '')
        if ast.get('flags'):
            flags = ast.get('flags').replace('MODIFIER_', '').split()[0]
        else:
            flags = ''
        #print(f"{flags} function {name} start")
        nod = self.current[-1].insert(Node(name, 'Funk', data=flags.lower()))
        self.current.append(nod)
        for key,val in ast.items():
            self.process(val)
        #print(f"{flags} function {name} end")
        self.current.pop()

    def doAST_Function(self, ast):
        #{'name': '"VersionFile"', 'params': [],
        # 'stmts': {'AST_STMT_LIST': ...
        #print('doAST_Function', ast, "\n")
        name = ast['name'].replace('"', '')
        nod = self.current[-1].insert(Node(name, 'Funk', data='function'))
        for key,val in ast.items():
            self.process(val)

    def doMethodCall(self, ast):
        try:
            if ast.get('method'):
                name = ast['method'].replace('"', '')
            if ast.get('expr'):
                if ast['expr'].get('AST_PROP'):
                    #{'expr': {'AST_PROP': {'expr': {'AST_VAR': {'name': '"this"'}}, 'prop': '"PDO"'}}, 'method': '"prepare"',
                    ast_var = ast['expr']['AST_PROP']['expr']['AST_VAR']
                    prop = ast['expr']['AST_PROP']['prop'].replace('"', '') + "->"
                    var = ast_var['name'].replace('"', '')
                    #print(f" A: Anrop {var}->{prop}{name}")
                    nod = self.current[-1].insert(Node(name, 'Anrop', data=f"{var}->{prop}"))
                elif ast['expr'].get('AST_VAR'):
                    #{'expr': {'AST_VAR': {'name': '"this"'}}, 'method': '"Children"', ...
                    ast_var = ast['expr']['AST_VAR']
                    prop = ''
                    var = ast_var['name'].replace('"', '')
                    if var in self.varMap.keys():
                        var = self.varMap[var]
                    #print(f" B: Anrop {var}->{prop}{name}")
                    nod = self.current[-1].insert(Node(name, 'Anrop', data=f"{var}->{prop}"))
            else:
                print(f" ? {ast}")
                sys.exit()
            for key,val in ast.items():
                self.process(val)
        except Exception as e:
            #print(' ERR: doMethodCall' , e)
            #print('  ', ast)
            pass

    def doAST_Call(self, ast):
        """
        {'AST_CALL':
            {'expr': {'AST_NAME': {'name': '"testPriv"', 'flags': 'NAME_NOT_FQ (1)'}},
             'args': {'AST_ARG_LIST': [{'AST_VAR': {'name': '"aa"'}}]}
        }}
        {'AST_CALL': {'expr': {'AST_VAR': {'name': '"function"'}}, 'args': []}}
        """
        #print('I', ast)
        try:
            name = ast['expr']['AST_NAME']['name'].replace('"', '')
        except:
            name = '?_' + ast['expr']['AST_VAR']['name'].replace('"', '')
        #print(f"  Call {name}")
        nod = self.current[-1].insert(Node(name, 'Anrop'))
        for key,val in ast.items():
            self.process(val)

    def doAST_Static_Call(self, ast):
        #'class': {'AST_NAME': {'name': '"DB"', 'flags': 'NAME_NOT_FQ (1)'}}, 'method': '"getPassiveDBname"', 'args': []}
        #print('doAST_Static_Call', ast)
        clsName = ast['class']['AST_NAME']['name'].replace('"', '')
        #print(ast['method'])
        method =  ast['method'].replace('"', '')
        #print(f"  Call {clsName}::{method}")
        nod = self.current[-1].insert(Node(method, 'Anrop', data=clsName))
        for key,val in ast.items():
            self.process(val)


    def doNew(self, ast):
        #{'AST_ASSIGN': {'var': {'AST_VAR': {'name': '"MSa"'}},
        #                'expr': {'AST_NEW': {'class': {'AST_NAME': {'name': '"MS"', ...
        try:
            var = ast['var']['AST_VAR']['name'].replace('"', '')
            cls = ast['expr']['AST_NEW']['class']['AST_NAME']['name'].replace('"', '')
            self.varMap[var] = cls
            #print(f"NEW {var} == {cls}")
        except:
            #print(f"ERR doNew {ast}")  #Blir många av dessa felen !
            pass
        for key,val in ast.items():
            self.process(val)

    def process(self, ast):
        if type(ast) is dict:
            if ast.get('AST_CLASS'):
                self.doClass(ast['AST_CLASS'])
            elif ast.get('AST_METHOD'):
                self.doMethod(ast['AST_METHOD'])
            elif ast.get('AST_METHOD_CALL'):
                self.doMethodCall(ast['AST_METHOD_CALL'])
            elif ast.get('AST_CALL'):
                #print('P', ast)
                self.doAST_Call(ast['AST_CALL'])
            elif ast.get('AST_STATIC_CALL'):
                self.doAST_Static_Call(ast['AST_STATIC_CALL'])
            elif ast.get('AST_ASSIGN'):
                self.doNew(ast['AST_ASSIGN'])
            elif ast.get('AST_FUNC_DECL'):
                self.doAST_Function(ast['AST_FUNC_DECL'])
            else:
                for key,val in ast.items():
                    self.process(val)
        elif type(ast) is list:
            i = 0
            for t in ast:
                self.process(t)
                i += 1
        else:
            pass

    def getTree(self):
        self.process(self.astData)
        #print(self.varMap)
        return self.tree

allData = {}  #all data per file
fileData = {}  #ast per file
# Gå igenom alla PHP-filer i projdDir recursivt utom
skipDir = ['/smarty/'] #['/smarty/', '/Disuppd/', '/Disconv/'] #
for filPath in Path(projDir).rglob('*.php'):
    f = str(filPath)
    if skipDir:
        p = '|'.join(skipDir)
        pattern = re.compile(r'%s' % p)
        m = re.search(pattern, f)
        if m: continue
    try:
        #if 'pushJsonData' not in f: continue
        #if 'MSPDO1' not in f: continue
        #if not( 'MSPDO1' in f or 'MedDB' in f): continue
        print(f"Analyserar '{f}'")
        allData[f] = {'ast': None, 'graphDot': ''}
        fileData[f] = None
        fileAST = ast(f)
        fileData[f] = fileAST.getTree()  #Fyll på globala variabler
        allData[f]['ast'] = fileData[f]
        fileData[f].assignIds()
        fileData[f].usedFunctions() #Fyll på defFunk
        # data per fil
        allData[f]['graphDot'] = allData[f]['ast'].mkGraph() # UTAN externa anrop - för att kunna hitta anropade
        #compress graph - remove duplicate links
        compressedGraph = ''
        doneLink = set()
        for line in allData[f]['graphDot'].splitlines():
            line = line.strip()
            if ' -> ' in line and line in doneLink:
                continue
            else:
                compressedGraph += line + "\n"
                doneLink.add(line)
        allData[f]['graphDot'] = compressedGraph
    except Exception as e:
        #print(traceback.print_exception(e))
        print(f"MISSLYCKADES med {f} se logfil\n")
        #print(type(e))
        #print(e.args)
        #print(traceback.format_exc())
        logfil = 'data/' + os.path.split(f)[1].replace('php', 'log')
        with open(logfil, 'w') as log:
            log.write(f"MISSLYCKADES med {f}\n")
            log.write(str(type(e)) + "\n")
            log.write("".join(traceback.format_exception(e)))

id2Name = {v: k for k, v in name2Id.items()}

##Generera resultatfiler

Anropade = set() #name
Definierade = set()
##Gör callgraf mellan filer
filBeroende = {} #filnamn -> set av anropade filnamn
for fil,astTree in fileData.items():
    AnroparPerFil = set()
    DefinieradePerFil = set()
    try:
        astTree.getBeroende()  #Extraherar alla Anropade och Definierade till globala variabler
    except:
        #Misslyckade filer
        pass
    filBeroende[fil] = {'Anropar': AnroparPerFil - stdFunctions, 'Definierade': DefinieradePerFil}
    Anropade.update(AnroparPerFil - stdFunctions)
    Definierade.update(DefinieradePerFil)
function2fil = {}  #I vilken fil är en funktion definierad
filGraph = defaultdict(set)  
for fil, data in filBeroende.items():
    for func in data['Definierade']:
        function2fil[func] = fil
for fil, data in filBeroende.items():
    for anrop in data['Anropar']:
        try: 
            filGraph[fil].add(function2fil[anrop])
        except:
            #print(f"ERR {anrop} i {fil}")
            pass

done = set()
with open('data/filGraph.dot', 'w') as gr:
    gr.write("digraph filGraph {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25;\n")
    for fil, data in filGraph.items():
        fil = fil.replace(projDir, '')
        f = fil.replace('.php', '').replace('/', '_')
        if fil not in done:
            gr.write(f'{f} [fillcolor="cornflowerblue", label="{fil}", style=filled, shape="box"];\n')
            done.add(fil)
        for beroenden in data:
            ff = beroenden.replace(projDir, '').replace('.php', '').replace('/', '_')
            gr.write(f"{f} -> {ff}\n")
    gr.write("}\n")
os.system(f"dot -Tsvg data/filGraph.dot > data/filGraph.svg")

# Generera HTML för varje PHP-fil
for f,data in allData.items():
    #if not 'MSPDO1' in str(f): continue  #DEB
    dotfil = './data/' + os.path.split(f)[1].replace('php', 'dot')
    lokalaFunkExterntAnropade = filBeroende[f]['Definierade'] & Anropade
    if data['graphDot']:
        dotAdd = 'Extern  [fillcolor="coral", style=filled, shape="box"];\n'
        for id in {name2Id[i] for i in lokalaFunkExterntAnropade}:
            dotAdd += f"Extern -> {id};\n"
        graph = allData[f]['graphDot'] + dotAdd
        with open(f"{dotfil}", 'w') as fil:
            fil.write("digraph testmk {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25; \n")
            fil.write(graph)  #graph.to_string())
            fil.write("}\n")
        os.system(f"dot -Tsvg {dotfil} > {dotfil.replace('.dot', '.svg')}")
    with open(f"{dotfil.replace('.dot', '.html')}", 'w') as html:
        (dir, filnamn) = os.path.split(f)
        dir = f"{dir}/".replace(projDir, '')
        filnamn = filnamn.replace('.php', '')
        html.write(f"""<!DOCTYPE html>
        <html>
        <head><title>Statisk call-graf för {filnamn}</title></head>
        <body>
        <h1>Statisk call-graf för {filnamn}</h1>
        <a href='./top_index.html'>Tillbaka till top index</a>
        """)
        
        if ' -> ' in graph:
            html.write("<h2>Call-graf</h2>\n")
            html.write("""Blå är den analyserade filen.<br>
            Röd anger anrop från en annan fil.<br>
            Gul anger "public functions".<br>
            Grön anger "private functions".<br>
            Vit är okända funktioner - möjligen från någon av de filer som inte har analyserats.<br>\n""")
            html.write(f"<img src='{dotfil.replace('data/', '').replace('.dot', '.svg')}' width='100%'>\n")
        html.write("</body>\n</html>\n")

## Dubblettnamn för funktioner
dublDef = {}
dubl = defaultdict(int) #tmp var
for f, data in allData.items():
    for nm in filBeroende[f]['Definierade']:
        if nm == '__construct': continue
        dubl[nm] += 1
for nm,ant in dubl.items():
    if ant > 1:
        files = []
        for f, data in allData.items():
            if nm in filBeroende[f]['Definierade']:
                files.append(f.replace(projDir, './'))
        dublDef[nm] = files

#Graf för alla filer i hela projekt
pgrfil = './data/projektGraph.dot'
with open(pgrfil, 'w') as fil:
    graph = ''
    k = 1
    for f,data in allData.items():
        graph += f'subgraph cluster{k} {{graph [style=rounded]  label="FIL: {f}"\n'
        graph += data['graphDot']
        graph += "}\n"
        k += 1
    fil.write("digraph Projekt {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25; \n")
    fil.write(graph)
    fil.write("}\n")
os.system(f"dot -Tsvg {pgrfil} > {pgrfil.replace('.dot', '.svg')}")

#GLOBAL ANALYS

with open('./data/top_index.html', 'w') as html:
    html.write(f"""<!DOCTYPE html>
    <html>
    <head><title>Statiska call-grafer för projektet {projDir}</title></head>
    <body>
    <a href="filGraph.svg">Graph över fil-beroenden</a><br>
    <a href="projektGraph.svg">Graph över hela projeket (STOR)</a>
    <h4>Skippade kataloger: {', '.join(skipDir)}</h4>
    <h1>Statiska call-grafer för {projDir}</h1>
      """)
    html.write("<table border=1>\n")
    html.write("<tr><th>Katalog</th><th>Fil</th><th>Log-fil</th></tr>\n")
    for fil in sorted(fileData.keys()):
        (dir, filnamn) = os.path.split(fil)
        dir = f"{dir}/".replace(projDir, '')
        filnamn = filnamn.replace('.php', '')
        if Path(f"./data/{filnamn}.html").is_file() and not Path(f"./data/{filnamn}.log").is_file():
            html.write(f"<tr><td>./{dir}</td><td><a href='{filnamn}.html'>{filnamn}</a></td>")
        else:
            html.write(f"<tr><td>./{dir}</td><td>{filnamn} <b>?</b></td>")
        if Path(f"./data/{filnamn}.log").is_file():
            html.write(f"<td><a href='{filnamn}.log'>Log</a></td></tr>\n")
        else:
            html.write(f"<td>-</td></tr>\n")
    html.write("</table>\n")
    html.write("<p><b>Analysen skiljer på gemena och versaler, vilket PHP inte gör\n")
    html.write("'getData' och 'getdata' är samma i PHP, men här behandlas dom som 2 olika identifierare.</b>\n")
    html.write("<h2>Inte använda funktioner</h2>\n")
    html.write(', '.join(sorted(Definierade - Anropade)))
        
    html.write("<h2>Anropade men inte definierade</h2>\n")
    html.write(', '.join(sorted(Anropade - Definierade)))
    
    html.write("<h2>Funktioner definierade mer än 1 gång</h2>\n")
    html.write("<table border=1>\n")
    html.write("<tr><th>Funktion</th><th>Filer</th></tr>\n")
    for namn, filer in dublDef.items():
        html.write(f"<tr><td>{namn}</td><td>{'<br>'.join(filer)}</td></tr>\n")
    html.write("</table>\n")
    #html.write(f"{dublDef}")
    html.write("</body></html>")
