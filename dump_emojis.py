import os
import re

custom_emoji_pattern = re.compile(r'<a?:[^:]+:([0-9]+)>')
# A simple way to extract unicode emojis is harder without third party libs, but we can look for typical discord emojis.
emojis = set()

for root, dirs, files in os.walk('d:/SpaceX/cogs'):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(r'<a?:[a-zA-Z0-9_]+:[0-9]+>', content)
                for m in matches:
                    emojis.add(m)
                # also let's just find anything like ✅
                if "✅" in content: emojis.add("✅")
                if "✔️" in content: emojis.add("✔️")
                
with open('d:/SpaceX/emojis.txt', 'w', encoding='utf-8') as f:
    for e in emojis:
        f.write(e + "\n")
