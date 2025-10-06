import sys
import os
import subprocess
from pathlib import Path
import json
from collections import defaultdict

# Globala variabler
uid = 0
defined = {}  #name2Id  BYT NAMN
localDefined = {} #defined in this file
defFunk = set()  #id of defined functions (Funk)
localDefFunk = set()  #id of functions defined in this file

class Node:
    def __init__(self, name, typ, data=''):
        self.name = name
        self.id = '?'
        if typ in ('Fil', 'Klass', 'Funk', 'Anrop'):
            self.typ = typ
        else:
            sys.exit(f"Okänd typ {typ} för {name}")
        self.data = data
        self.nodes = []
        self.graph = None

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
            self.graph = "digraph testmk {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25; concentrate=true;\n"
            graph = self.graph
            done = set()
        if self.typ in ('Fil', 'Klass', 'Funk'):
            #DEB label = f"{self.id} {self.data} {self.name}"
            #label = f"{self.data} {self.name}" #Extended
            label = f"{self.name}"  #Minimal
            color = 'firebrick1'
            if self.typ == 'Fil':
                graph += f'{self.id} [fillcolor="chartreuse", label="{label}", style=filled, shape="box"];\n'                
            elif self.typ == 'Klass':
                color = 'coral'
                graph += f'subgraph cluster{self.name} {{graph [style=rounded] label="Klass {label}"\n'
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
            if self.id in defFunk:
                graph += f"{id} -> {self.id};\n"
        else:
            sys.exit(f"Okänd typ {self.id}: {self.typ} {self.name} {self.data}")
        return graph

    def assignIds(self):
        global uid
        global defined
        if f"{self.name}" in defined:
            self.id = defined[f"{self.name}"]
        if self.id == '?':
            uid += 1
            self.id = uid
            defined[f"{self.name}"] = uid
        localDefined[f"{self.name}"] = self.id
        for n in self.nodes:
            n.assignIds()

    def definedFunctions(self):  #BYT NAMN
        global defFunk
        if self.typ == 'Funk':
            defFunk.add(self.id)
            localDefFunk.add(self.id)
        for n in self.nodes:
            n.definedFunctions()

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
            print(' ERR: doMethodCall' , e)
            print('  ', ast)
            sys.exit()

    def doAST_Call(self, ast):
    #    {'AST_CALL':
    #           {'expr': {'AST_NAME': {'name': '"testPriv"', 'flags': 'NAME_NOT_FQ (1)'}},
    #            'args': {'AST_ARG_LIST': [{'AST_VAR': {'name': '"aa"'}}]}
    #           }
        name = ast['expr']['AST_NAME']['name'].replace('"', '')
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
        except:
            #print(f"ERR doNew {ast}")
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
                self.doAST_Call(ast['AST_CALL'])
            elif ast.get('AST_STATIC_CALL'):
                self.doAST_Static_Call(ast['AST_STATIC_CALL'])
            elif ast.get('AST_ASSIGN'):
                self.doNew(ast['AST_ASSIGN'])
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
    
try:
    projDir = sys.argv[1]
    print(f"Projektkatalog={projDir}")
    if not os.path.isdir(projDir):
        help(f"'{projDir}' är inte en katalog")
except Exception as e:
    sys.exit(f"{projDir} är inte en katalog {e}")

allData = {}  #all data per file
fileData = {}  #ast per file
# Gå igenom alla PHP-filer i projdDir recursivt utom 'smarty' ??
for filPath in Path(projDir).rglob('*.php'):
    f = str(filPath)
    if '/smarty/' in f: continue
    if 'Web/Dis' in f: continue
    try:
        print(f"Analyserar '{f}'")
        allData[f] = {'ast': None, 'defined': {}, 'id2Namn': {}, 'defFunk': set(), 'calls': set(), 'anropade': set(),
                      'allFuncs': set(), 'externa_anrop': set(), 'inteAnropadeNamn': set(), 'graphDot': ''}
        localDefined = {}
        localDefFunk = set()
        fileData[f] = None
        fileAST = ast(f)
        fileData[f] = fileAST.getTree()
        allData[f]['ast'] = fileData[f]
        fileData[f].assignIds()
        # data per fil
        allData[f]['defined'] = localDefined
        fileData[f].definedFunctions() #funktioner använda i denna fil
        allData[f]['defFunk'] = localDefFunk #funktioner i definierade i denna fill
        allData[f]['id2Name'] = {v: k for k, v in localDefined.items()}
        allData[f]['allFuncs'] = set(allData[f]['defined'].values())  #Alla funktioner i denna fil
        allData[f]['externa_anrop'] = list(allData[f]['allFuncs'].difference(allData[f]['defFunk']))  #anropade externa funktioner
        allData[f]['externaAnropadeNamn'] = [ allData[f]['id2Name'][x] for x in  allData[f]['externa_anrop'] ]
        allData[f]['graphDot'] = allData[f]['ast'].mkGraph() # UTAN externa anrop - för att kunna hitta anropade
        #anropade (called) functions
        allData[f]['calls'] = defaultdict(set)
        allData[f]['anropade'] = set()
        for l in allData[f]['graphDot'].splitlines():
            try:
                (caller, callee) = l.strip().rstrip(';').split(' -> ')
                allData[f]['calls'][caller].add(int(callee))
                allData[f]['anropade'].add(int(callee))  #Behöver uppdateras med anrop från andra filer
            except:
                pass
        allData[f]['inteAnropadeNamn'] = [allData[f]['id2Name'][x] for x in  allData[f]['allFuncs'].difference(allData[f]['anropade']).difference(allData[f]['externa_anrop'])]
    except Exception as e:
        import traceback
        print(traceback.print_exception(e))
        print(f"MISSLYCKADES med {f}\n{e}\n")
        print(type(e))
        print(e.args)
        print(traceback.format_exc())
        logfil = 'data/' + os.path.split(f)[1].replace('php', 'log')
        with open(logfil, 'w') as log:
            log.write(f"MISSLYCKADES med {f}\n")
            log.write(str(type(e)) + "\n")
            log.write("".join(traceback.format_exception(e)))

id2Name = {v: k for k, v in defined.items()}

##Generera resultatfiler

for f,data in allData.items():
    #if not 'MSPDO1' in str(f): continue  #DEB
    # Generera HTML för varje PHP-fil
    allFuncs = data['allFuncs']  #set(defined.values())  #Alla funktioner
    externa_anrop = data['externa_anrop']  #list(allFuncs.difference(defFunk))  #anrop till externa funktioner
    dotfil = './data/' + os.path.split(f)[1].replace('php', 'dot')
    #Graph med externa anrop
    allaAnrop = set()
    for fx,fxData in allData.items():
        if fxData['anropade']:
            allaAnrop.update(set(fxData['anropade']))
    lokalaFunkInteAnropade = (allData[f]['defFunk'] & allaAnrop) -  allData[f]['anropade']
    lokalaFunkExterntAnropade = allData[f]['defFunk'] & allaAnrop
    if data['graphDot']:
        dotAdd = 'Extern  [fillcolor="coral", style=filled, shape="box"];\n'
        for id in lokalaFunkExterntAnropade:
            dotAdd += f"Extern -> {id};\n"
        graph = allData[f]['graphDot'] + dotAdd
        with open(f"{dotfil}", 'w') as fil:
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
        """??
        if allFuncs.difference(anropade).difference(externa_anrop):
            html.write("<h2>Inte !lokalt! anropade funktioner ?</h2>\n")
            inteAnropadeNamn = data['inteAnropadeNamn']  #[id2Name[x] for x in allFuncs.difference(anropade).difference(externa_anrop)]
            html.write(', '.join(sorted(inteAnropadeNamn)))
            html.write("<p>\n")
        """
        #printa externa_anrop
        if externa_anrop:
            html.write("<h2>Externa anrop till: ?</h2>\n")
            externaAnropadeNamn = data['externaAnropadeNamn']
            html.write(', '.join(sorted(externaAnropadeNamn)))
        # FIX KOLLA OM det finns graf!
        if ' -> ' in graph:
            html.write("<h2>Call-graf</h2>\n")
            html.write("""Röd? anger anrop från en annan fil.<br>
            Gul anger "public functions".<br>
            Grön anger "private functions".<br>\n""")
            html.write(f"<img src='{dotfil.replace('data/', '').replace('.dot', '.svg')}' width='100%'>\n")
        html.write("</body>\n</html>\n")

#Global analys

## Kolla dubbletter och inte anropade
#print('Funktioner definierade i mer än 1 fil')
dubl = defaultdict(int)
for f, data in allData.items():
    for id in allData[f]['defFunk']:
        if id2Name[id] == '__construct': continue
        dubl[id] += 1
dublDef = {}
for id,ant in dubl.items():
    if ant > 1:
        files = []
        for f, data in allData.items():
            if id in data['defFunk']:
                files.append(f)
        #print(f"{id}, {id2Name[id]}, {','.join(files)}")
        dublDef[id2Name[id]] = files
#
#inte anropade - alla allaDefFunk - allaAnropade
allaAnropade = set()
for f,data in allData.items(): #?
    allaAnropade.update(set(data['anropade']))
allaInteAnropade = defFunk - allaAnropade
#print(allaInteAnropade)
#for id in allaInteAnropade:
#    print(id, id2Name[id])

with open('./data/top_index.html', 'w') as html:
    html.write(f"""<!DOCTYPE html>
    <html>
    <head><title>Statiska call-grafer för {projDir}</title></head>
    <body>
    <h1>Statiska call-grafer för {projDir}</h1>
    """)
    html.write("<table border=1>\n")
    html.write("<tr><th>Katalog</th><th>Fil</th><th>Log-fil</th></tr>\n")
    for fil in sorted(fileData.keys()):
        (dir, filnamn) = os.path.split(fil)
        dir = f"{dir}/".replace(projDir, '')
        filnamn = filnamn.replace('.php', '')
        if Path(f"./data/{filnamn}.html").is_file():
            html.write(f"<tr><td>./{dir}</td><td><a href='{filnamn}.html'>{filnamn}</a></td>")
        else:
            html.write(f"<tr><td>./{dir}</td><td>ERR {filnamn}</td>")
        if Path(f"./data/{filnamn}.log").is_file():
            html.write(f"<td><a href='{filnamn}.log'>Log</a></td></tr>\n")
        else:
            html.write(f"<td>-</td></tr>\n")
    html.write("</table>\n")
    #Inte anropade
    html.write("<h2>Inte använda funktioner</h2>\n")
    for id in allaInteAnropade:
        html.write(f"{id2Name[id]}, ")
    #html.write(f"{allaInteAnropade}")
    html.write("<h2>Funktioner definierade mer än 1 gång</h2>\n")
    html.write("<table border=1>\n")
    html.write("<tr><th>Funktion</th><th>File</th></tr>\n")
    for namn, filer in dublDef.items():
        html.write(f"<tr><td>{namn}</td><td>{'<br>'.join(filer)}</td></tr>\n")
    html.write("</table>\n")
    #html.write(f"{dublDef}")
    html.write("</body></html>")
"""
#Check inte använda
    for id in allaInteAnropade:
        namn = id2Name[id]
        cmd = f'grep -r -e "{namn}" {projDir}'
        ext = subprocess.check_output(cmd, shell=True)
        print(ext)
"""
