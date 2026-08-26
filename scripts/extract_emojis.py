import os
import re

emojis = set()

for root, dirs, files in os.walk('d:/SpaceX/cogs'):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r'<a?:[^:]+:\d+>', content)
                for m in matches:
                    emojis.add(m)

for root, dirs, files in os.walk('d:/SpaceX'):
    for file in files:
        if file == 'main.py':
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r'<a?:[^:]+:\d+>', content)
                for m in matches:
                    emojis.add(m)

print("FOUND EMOJIS:")
for e in emojis:
    print(e)
