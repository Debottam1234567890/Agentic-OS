import os
import ast
def build_adjacency_list(root_dir='.'):
    graph = {}
    ignore_dirs = {'.git', '__pycache__', 'venv', '.chronos_vault', 'node_modules'}
    local_modules = set()
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith('.py'):
                local_modules.add(file.replace('.py', ''))
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if not file.endswith('.py'):
                continue
            filepath = os.path.join(root, file)
            module_name = file.replace('.py', '')
            graph[module_name] = []
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_module = alias.name.split('.')[0]
                        if base_module in local_modules and base_module != module_name:
                            graph[module_name].append(base_module)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    base_module = node.module.split('.')[0]
                    if base_module in local_modules and base_module != module_name:
                        graph[module_name].append(base_module)
    for k in graph:
        graph[k] = list(set(graph[k]))
    return graph
