import os

target_string = "<:verified_tick:837551087786393710>"
replacement_string = "<:verified_tick:837551087786393710>"

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if target_string in content:
                    new_content = content.replace(target_string, replacement_string)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Replaced in: {filepath}")

replace_in_files("d:/SpaceX")
