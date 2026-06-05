import ast
source = '\n# This is a comment\ndef foo():\n    \'\'\'Docstring here\'\'\'\n    print("hello")\n    \n    # another comment\n    print("world")\n'
parsed = ast.parse(source)
for node in ast.walk(parsed):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
        if ast.get_docstring(node):
            node.body.pop(0)
unparsed = ast.unparse(parsed)
lines = [line for line in unparsed.splitlines() if line.strip()]
print('\n'.join(lines))
