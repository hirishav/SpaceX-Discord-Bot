import os

tick_emojis = ["✅", "✔️", "☑️", "<:tick:123>", "✅"] # replace all possible ticks?
# Let's just find them first.
for root, dirs, files in os.walk('d:/SpaceX/cogs'):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                content = f.read()
                if "✅" in content or "✔️" in content or "☑️" in content or "✔" in content:
                    print(file)
