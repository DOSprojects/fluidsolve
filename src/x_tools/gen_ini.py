'''
Tool to generate the __init__.py

'''
import os
import shutil
import ast

def extractSymbols(fname: str, exclude: dict) -> tuple:
  ''' Extract top-level variable, function and class names from a Python file.

  Args:
      fname (str): filename
      exclude (dict): names to exclude

  Returns:
      tuple: The found variables, functions and classes.
  '''
  exclude_var = exclude.get('var', [])
  exclude_cls = exclude.get('cls', [])
  exclude_fun = exclude.get('fun', [])
  symbols_var = []
  symbols_cls = []
  symbols_fun = []
  with open(fname, 'r', encoding='utf-8') as file:
    try:
      tree = ast.parse(file.read(), filename=fname)
      for node in tree.body:
        if isinstance(node, ast.Assign):
          for target in node.targets:
            if isinstance(target, ast.Name):
              if target.id not in exclude_var:
                symbols_var.append(target.id)
        elif isinstance(node, ast.FunctionDef):
          if node.name not in exclude_fun:
            symbols_fun.append(node.name)
        elif isinstance(node, ast.ClassDef):
          if node.name not in exclude_cls:
            symbols_cls.append(node.name)
    except SyntaxError as e:
      print(f'Syntax error in {fname}: {e}')
  return (symbols_var, symbols_fun, symbols_cls)

def generate(path: str, files: list, exclude: dict={}) -> str:
  ''' Generate the content for a __init__.py file.

  Args:
      path (str): path of library
      files (list): list with filenaes
      exclude (dict, optional): names to exclude. Defaults to {}.

  Returns:
      str: The __init__.py file
  '''
  symbols_var = []
  symbols_cls = []
  symbols_fun = []
  txt = ''
  for f in files:
    modname = os.path.splitext(f)[0]
    fpath = os.path.normpath(os.path.join(path, f))
    s_var, s_fun, s_cls = extractSymbols(fpath, exclude)
    symbols_var += s_var
    symbols_fun += s_fun
    symbols_cls += s_cls
    if len (s_var) > 0 or len (s_fun) > 0 or len (s_cls) > 0:
      txt += f'from .{modname} import (\n'
      if len (s_var) > 0:
        for s in s_var:
          txt += f'  {s},\n'
      if len (s_fun) > 0:
        for s in s_fun:
          txt += f'  {s},\n'
      if len (s_cls) > 0:
        for s in s_cls:
          txt += f'  {s},\n'
      txt += '  )\n'
  txt += '\n'
  txt += '__all__ = [\n' \
      + '  #VAR\n'
  for name in sorted(set(symbols_var)):
    txt += f"  '{name}',\n"
  txt += '  #FUN\n'
  for name in sorted(set(symbols_fun)):
    txt += f"  '{name}',\n"
  txt += '  #CLS\n'
  for name in sorted(set(symbols_cls)):
    txt += f"  '{name}',\n"
  txt += ']\n'
  return txt

#******************************************************************************
# MAIN
#******************************************************************************
if __name__ == '__main__':
  print('\nGenerating __init__.py file...\n')
  path_script = os.path.abspath(os.path.dirname(__file__))
  path_lib = os.path.normpath(os.path.join(path_script, '..', '..', 'src', 'fluidsolve'))
  file_init = os.path.join(path_script, 'init.py')
  file_bak = os.path.join(path_script, 'init.bak')
  #
  exclude = {
    'var': [
      'u',
      'Quantity',
      'unitRegistry',
      '__all__'
    ],
    'fun': [
      'main'
    ],
    'cls': [
    ],
  }

  # Backup __init__.py if it exists
  if os.path.exists(file_init):
    shutil.copy2(file_init, file_bak)
    print(f'Backup created: {file_bak}')

  # List all Python files excluding __init__.py
  modfiles = [f for f in os.listdir(path_lib) if f.endswith('.py') and f not in ('__init__.py', '__main__.py')]

  # Generate import statements and __all__ list
  ftxt = generate(path_lib, modfiles, exclude)
  # Write to __init__.py
  with open(file_init, 'w', encoding='utf-8') as hfile:
    hfile.write(ftxt)

  print(f'{file_init} updated with imports and __all__ list.')
