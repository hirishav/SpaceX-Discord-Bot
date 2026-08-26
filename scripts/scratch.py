import ast, json, os

cogs = {}
aliases = {}

for f in os.listdir('cogs'):
    if not f.endswith('.py'): continue
    cogs[f] = []
    aliases[f] = []
    with open('cogs/'+f, encoding='utf-8') as file:
        tree = ast.parse(file.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            has_cmd = False
            name = node.name
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    func_name = ''
                    if hasattr(dec.func, 'attr'): func_name = dec.func.attr
                    elif hasattr(dec.func, 'id'): func_name = dec.func.id
                    if func_name in ['command', 'group']:
                        has_cmd = True
                        for kw in dec.keywords:
                            if kw.arg == 'name' and hasattr(kw.value, 'value'):
                                name = kw.value.value
                            if kw.arg == 'aliases' and hasattr(kw.value, 'elts'):
                                aliases[f].extend([e.value for e in kw.value.elts if hasattr(e, 'value')])
            if has_cmd:
                cogs[f].append(name)

conflicts = set()
music_cmds = set(cogs['music.py'] + aliases['music.py'])
for f in cogs:
    if f in ['music.py', 'lavalink_music.py']: continue
    other_cmds = set(cogs[f] + aliases[f])
    intersect = music_cmds.intersection(other_cmds)
    if intersect:
        print(f'Conflict with {f}: {intersect}')
