import sys
import os
import subprocess
from pathlib import Path
import json
from pprint import pprint,pp
import pydotplus

class Node:

    def __init__(self, name, typ, data=''):
        self.name = name
        if typ in ('Fil', 'Klass', 'Funk', 'Anrop'):
            self.typ = typ
        else:
            sys.exit(f"Okänd typ {typ} för {name}")
        self.data = data.replace('this->', '')
        self.nodes = set()

    def insert(self, nod):
        self.nodes.add(nod)
        return nod
    
    def printTree(self, prefix=''):
        print(prefix, self.typ, self.name, self.data)
        
        for typ in ('Klass', 'Funk', 'Anrop'):
            for n in [x for x in self.nodes if x.typ == typ]:
                n.printTree(prefix + '  ')

class ast():
    def __init__(self, file):
        self.tree = Node(file, 'Fil')
        self.current = [self.tree]
        #get ast
        cmd = f"php parse2data.php {file}"  #get ast as datastruct - Walk recursively
        res = subprocess.check_output(cmd, shell=True)
        self.astData = json.loads(res)

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
                    #print(f" Anrop {var}->{prop}{name}")
                    nod = self.current[-1].insert(Node(name, 'Anrop', data=f"{var}->{prop}"))
                elif ast['expr'].get('AST_VAR'):
                    #{'expr': {'AST_VAR': {'name': '"this"'}}, 'method': '"Children"', ...
                    ast_var = ast['expr']['AST_VAR']
                    prop = ''
                    var = ast_var['name'].replace('"', '')
                    #print(f" Anrop {var}->{prop}{name}")
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
        #{'AST_ASSIGN': {'var': {'AST_VAR': {'name': '"MS"'}},
        #                'expr': {'AST_NEW': {'class': {'AST_NAME': {'name': '"MS"', ...
        pass

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

    def getData(self):
        self.process(self.astData)
        return self.data

    def getTree(self):
        self.process(self.astData)
        return self.tree
#end ast

"""
##TEST
f = 'MSPDO1.php'
fileAST = ast(f)
t = fileAST.getTree()
print('----------')
t.printTree()
sys.exit()
###
"""
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
fileData = {}
allFuncs = set()
for f in Path(projDir).rglob('*.php'):
    if '/smarty/' in str(f):
        print(f"SKIP {f}")
        continue
    try:
        print(f"Analyserar '{f}'")
        fileAST = ast(f)
        fileData[f] = fileAST.getTree()
        fileData[f].printTree()
    except Exception as e:
        print(f"MISSLYCKADES med {f}")



"""
allFuncs = data['MSPDO1.php']['class']['MS']['func'].keys()

allCalls = False
#allCalls = True
for key, val in data['MSPDO1.php']['class']['MS']['func'].items():
    if val['anrop']:
        print(f"Anrop för {key}")
        for c in val['anrop']:
            if c in allFuncs:
                print(f"  cls {c}")
            else:
                if allCalls: print(f"  std {c}")
                pass
"""
sys.exit()
graph = pydotplus.graphviz.Graph(graph_name="MSPDO1", graph_type="digraph",
                                 overlap=False, rankdir = 'LR', ranksep = 0.25, nodesep=0.3)

#do Klass MS
classNamn = 'MS'
classData = data['MSPDO1.php']['class'][classNamn]
for func, val in classData['func'].items():
    if val['typ'] == 'private':
        graph.add_node(pydotplus.graphviz.Node(name=func, style='filled', fillcolor='green', label=f'"{func}"'))
    elif val['typ'] == 'public':
        graph.add_node(pydotplus.graphviz.Node(name=func, style='filled', fillcolor='gold', shape='box', label=f'"{func}"'))
for key, val in classData['func'].items():
    if val['anrop']:
        for c in val['anrop']:
            if c in allFuncs:
                graph.add_edge(pydotplus.graphviz.Edge(src=key, dst=c))
with open(f"MSPDO1.dot", 'w') as f:
    f.write(graph.to_string())
os.system(f"dot -Tsvg MSPDO1.dot > MSPDO1.svg")

#process => data contains result

