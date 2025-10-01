import sys
import subprocess
import json
from pprint import pprint,pp
"""
def traverse(ast):
    if not ast:
        return
    for node in ast:
        nt.add(node['nodeType'])
        if node['nodeType'] == 'Stmt_Class':
            print('Klass', node['name']['name'])
        elif node['nodeType'] == 'Stmt_ClassMethod':
            print('Method', node['name']['name'])
            if node['name']['name'] == 'AAtest':
                pprint.pprint(node)
                sys.exit()
        try:
            traverse(node.get('stmts'))
        except Exception as e:
            print(f"E: {e}")
            #pprint.pprint(node)
            return
"""

#global
file = 'MSPDO1.php'
#file = 'test.php'
data = {file: {'class': {}, 'function': {}, 'anrop': {}}}
cls = {}
method = ''

def doClass(ast):
    global data, cls
    name = ast['name'].replace('"', '')
    print(f"Klass {name} start")
    data[file]['class'][name] = {'namn': '', 'func': {}}
    cls = data[file]['class'][name]
    for key,val in ast.items():
        do(val)
    print(f"Klass {name} end")
    
def doMethod(ast):
    global cls, method
    name = ast['name'].replace('"', '')
    if ast.get('flags'):
        flags = ast.get('flags').replace('MODIFIER_', '').split()[0]
    else:
        flags = ''
    print(f"{flags} function {name} start")
    cls['func'][name] = {'typ': flags.lower(), 'anrop': set()}
    method = cls['func'][name]
    for key,val in ast.items():
        do(val)
    print(f"{flags} function {name} end")
    
def doMethodCall(ast):
    global method
    try:
        if ast.get('method'):
            name = ast['method'].replace('"', '')
        if ast.get('expr'):
            if ast['expr'].get('AST_PROP'):
                #{'expr': {'AST_PROP': {'expr': {'AST_VAR': {'name': '"this"'}}, 'prop': '"PDO"'}}, 'method': '"prepare"',
                ast_var = ast['expr']['AST_PROP']['expr']['AST_VAR']
                prop = ast['expr']['AST_PROP']['prop'].replace('"', '') + "->"
            elif ast['expr'].get('AST_VAR'):
                #{'expr': {'AST_VAR': {'name': '"this"'}}, 'method': '"Children"', ...
                ast_var = ast['expr']['AST_VAR']
                prop = ''
            var = ast_var['name'].replace('"', '')
        else:
            print(f" ? {ast}")
            sys.exit()
        print(f" Anrop {var}->{prop}{name}")
        method['anrop'].add(f"{var}->{prop}{name}")
        for key,val in ast.items():
            do(val)
    except Exception as e:
        print(' ERR: doMethodCall' , e)
        print('  ', ast)
        sys.exit()

def doCall(ast):
#    {'AST_CALL':
#           {'expr': {'AST_NAME': {'name': '"testPriv"', 'flags': 'NAME_NOT_FQ (1)'}},
#            'args': {'AST_ARG_LIST': [{'AST_VAR': {'name': '"aa"'}}]}
#           }
    name = ast['expr']['AST_NAME']['name']
    print(f"  Anrop {name} start")
    for key,val in ast.items():
        do(val)

def doNew(ast):
    #{'AST_ASSIGN': {'var': {'AST_VAR': {'name': '"MS"'}},
    #                'expr': {'AST_NEW': {'class': {'AST_NAME': {'name': '"MS"', ...
    pass
                                                                
def do(ast):
    if type(ast) is dict:
        if ast.get('AST_CLASS'):
            doClass(ast['AST_CLASS'])
        elif ast.get('AST_METHOD'):
            doMethod(ast['AST_METHOD'])
        elif ast.get('AST_METHOD_CALL'):
            doMethodCall(ast['AST_METHOD_CALL'])
        elif ast.get('AST_CALL'):
            doCall(ast['AST_CALL'])
        else:
            for key,val in ast.items():
                do(val)
    elif type(ast) is list:
        i = 0
        for t in ast:
            do(t)
            i += 1
    else:
        pass

cmd = f"php parse2data.php {file}"  #get ast as datastruct - Walk recursively
res = subprocess.check_output(cmd, shell=True)
ast = json.loads(res)
#print(ast)
res = do(ast)

print('==============')
#pprint(data)
allFuncs = data['MSPDO1.php']['class']['MS']['func'].keys()
for key, val in data['MSPDO1.php']['class']['MS']['func'].items():
    if val['anrop']:
        print(f"Anrop för {key}")
        for f in val['anrop']:
            if f.replace('this->', '') in allFuncs:
                print(f"  {f}")
                
