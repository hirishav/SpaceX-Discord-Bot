import os
import re

replacement_string = "<a:giveaway:686211362548088858>"

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace both animated and non-animated variants just in case
                new_content = re.sub(r'<a?:verified_tick:\d+>', replacement_string, content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Replaced in: {filepath}")

replace_in_files("d:/SpaceX")
