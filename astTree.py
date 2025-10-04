import sys
import os
import subprocess
from pathlib import Path
import json

uid = 0
defined = {}  #name2Id
defFunk = set()  #defined functions
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
            self.graph = "digraph testmk {nodesep=0.3; overlap=False; rankdir=LR; ranksep=0.25; compound=true;\n"
            graph = self.graph
            done = set()
        if self.typ in ('Fil', 'Klass', 'Funk'):
            #DEB label = f"{self.id} {self.data} {self.name}"
            label = f"{self.data} {self.name}"
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
        for n in self.nodes:
            n.assignIds()

    def definedFunctions(self):
        global defFunk
        if self.typ == 'Funk':
            defFunk.add(self.id)
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

# Gå igenom alla PHP-filer i projdDir recursivt utom 'smarty' ?? och 'Dis*'??
done = []
totNotCalled = set()
totExt = set()
fileData = {}
allFuncs = set()
for f in Path(projDir).rglob('*.php'):
    if '/smarty/' in str(f):
        #print(f"SKIP {f}")
        continue
    try:
        #DEB if not 'pushJsonData' in str(f): continue  #DEB
        print(f"Analyserar '{f}'")
        fileAST = ast(f)
        fileData[f] = fileAST.getTree()
        fileData[f].assignIds()
        fileData[f].definedFunctions()
        #uid och defFunk globala!!
        #fileData[f].printTree()
        dotfil = 'data/' + os.path.split(f)[1].replace('php', 'dot')
        graph = fileData[f].mkGraph()
        with open(f"{dotfil}", 'w') as f:
            f.write(graph)  #graph.to_string())
            f.write("}\n")
        os.system(f"dot -Tsvg {dotfil} > {dotfil.replace('.dot', '.svg')}")
    except Exception as e:
        import traceback
        print(traceback.print_exception(e))
        print(f"MISSLYCKADES med {f} {e}")
        print(type(e))
        print(e.args)
        print(traceback.format_exc())
