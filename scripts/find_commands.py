import os, re

cogs_dir = r"d:\SpaceX\cogs"
commands = []

for filename in os.listdir(cogs_dir):
    if not filename.endswith(".py"):
        continue
    filepath = os.path.join(cogs_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            found = re.findall(r"@commands\.hybrid_command\(name=[\'\"]([^\'\"]+)[\'\"]", content)
            for cmd in found:
                commands.append((cmd, filename))
    except Exception as e:
        pass

for cmd, file in sorted(commands):
    print(f"{cmd} -> {file}")
