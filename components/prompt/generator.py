import os
from .common import doeblockFileTypes

def get_formatted_path(target, mode, root):
    if not target: return ""
    if mode == "Name Only": return os.path.basename(target)
    if mode == "Relative Path" and root and target.startswith(root):
        try: return os.path.relpath(target, root)
        except: pass
    return target

def generate_tree_text(root, ignore):
    output = []
    ignores = {x.strip() for x in ignore.split(',') if x.strip()}
    def add(d, p=''):
        try:
            items = sorted([x for x in os.listdir(d) if x not in ignores and not x.startswith('.')])
            ptrs = ['├── '] * (len(items)-1) + ['└── '] if items else []
            for ptr, name in zip(ptrs, items):
                output.append(f"{p}{ptr}{name}")
                full = os.path.join(d, name)
                if os.path.isdir(full): add(full, p + ('│   ' if ptr == '├── ' else '    '))
        except: pass
    if root: output.append(os.path.basename(root)+"/"); add(root)
    return "\n".join(output)

def get_codeblock_language(path):
    ext = os.path.splitext(path)[1][1:].lower()
    return doeblockFileTypes.get(ext, 'plaintext')

def compile_prompt_data(data, root=""):
    # If the block is toggled OFF, return empty content
    if not data.get("is_active", True):
        return ""

    mode = data.get("type", "Message")
    text = data.get("text", "").strip()
    tgt = data.get("target_path", "")
    inject_files = data.get("tree_inject_files", [])

    out = f"{text}\n" if text else ""
    
    if mode != "Message" and tgt and os.path.exists(tgt):
        disp = get_formatted_path(tgt, data.get("path_mode"), root)
        
        if mode == "File":
            try: 
                with open(tgt, 'r', encoding='utf-8', errors='ignore') as f:
                    lang = get_codeblock_language(tgt)
                    out += f"\nFile: {disp}\n```{lang}\n{f.read()}\n```\n"
            except: out += f"[Error reading {disp}]\n"
            
        elif mode == "Folder Tree":
            # 1. The Tree Structure
            out += f"\nDir: {disp}\n```\n{generate_tree_text(tgt, data.get('ignore_patterns',''))}\n```\n"
            
            # 2. Injected Files
            if inject_files:
                out += "\n# --- Context Files for Tree ---\n"
                for f_path in inject_files:
                    if os.path.exists(f_path):
                        f_disp = get_formatted_path(f_path, data.get("path_mode"), root)
                        try:
                            with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lang = get_codeblock_language(f_path)
                                out += f"File: {f_disp}\n```{lang}\n{f.read()}\n```\n"
                        except:
                            out += f"[Error reading injected file: {f_disp}]\n"
    return out