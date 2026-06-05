import os
import ast

def minify_python_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            
        parsed = ast.parse(source)
        
        # Remove docstrings
        for node in ast.walk(parsed):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
                if ast.get_docstring(node):
                    node.body.pop(0)
                    
        unparsed = ast.unparse(parsed)
        
        # Remove all blank lines
        lines = [line for line in unparsed.splitlines() if line.strip()]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
            
        print(f"Minified {filepath}")
    except Exception as e:
        print(f"Failed to minify {filepath}: {e}")

if __name__ == "__main__":
    project_root = "/Users/sandeep/Agentic_OS"
    exclude_dirs = {".git", "venv", ".venv", "sandbox", "__pycache__"}
    
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py") and file != "minify.py":
                minify_python_file(os.path.join(root, file))
