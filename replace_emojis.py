import os
import re

emoji_replacements = {
    r'✅': '✅',
    r'👑': '👑',
    r'<:verified_tick:\d+>': '✅',
    r'<a:verified_tick:\d+>': '✅'
}

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for pattern, replacement in emoji_replacements.items():
                    new_content = re.sub(pattern, replacement, new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Replaced in: {filepath}")

replace_in_files("d:/SpaceX")
