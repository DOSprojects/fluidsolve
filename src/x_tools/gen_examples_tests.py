'''
Tool to generate the examples.rst and tests.rst

'''
import os

def generate_examples_rst():
    '''
    Generate examples.rst by combining static files and autodoc blocks for modules in src/x_examples.
    '''
    fstatic =  os.path.join('source', '_gen', 'examples_static.rst')
    dir = os.path.abspath('../src/x_examples')
    reldir = '../../src/x_examples'
    foutput = os.path.abspath(os.path.join('source', 'examples.rst'))
    # Read static content
    content = ''
    if os.path.exists(fstatic):
      with open(fstatic, 'r') as fhandle:
        content = fhandle.read()
    # List all .py files in the directory (excluding __init__.py)
    py_files = []
    if os.path.exists(dir):
      py_files = [f for f in os.listdir(dir) if f.endswith('.py') and f != '__init__.py']
      py_files.sort()
    for py_file in py_files:
      fname = os.path.splitext(py_file)[0]
      name = f'Test: `{fname}`'
      content += f'{name}\n' \
              + '-' * len(name) + '\n' \
              + '\n' \
              + f'.. automodule:: x_examples.{fname}\n' \
              + '   :exclude-members:\n' \
              + '\n' \
              + f'.. literalinclude:: {reldir}/{fname}.py\n' \
              + '   :language: python\n' \
              + '   :linenos:\n' \
              + '\n' \
    # Write to examples.rst
    with open(foutput, 'w') as f:
        f.write(content)

def generate_tests_rst():
    '''
    Generate tests.rst by combining static files and autodoc blocks for modules in src/x_tests.
    '''
    fstatic =  os.path.join('source', '_gen', 'tests_static.rst')
    dir = os.path.abspath('../src/x_tests')
    reldir = '../../src/x_tests'
    foutput = os.path.abspath(os.path.join('source', 'tests.rst'))
    # Read static content
    content = ''
    if os.path.exists(fstatic):
      with open(fstatic, 'r') as fhandle:
        content = fhandle.read()
    # List all .py files in the directory (excluding __init__.py)
    py_files = []
    if os.path.exists(dir):
      py_files = [f for f in os.listdir(dir) if f.endswith('.py') and f != '__init__.py']
      py_files.sort()
    for py_file in py_files:
      fname = os.path.splitext(py_file)[0]
      name = f'Tests: `{fname}`'
      content += f'{name}\n' \
              + '-' * len(name) + '\n' \
              + '\n' \
              + f'.. automodule:: x_tests.{fname}\n' \
              + '   :exclude-members:\n' \
              + '\n' \
              + f'.. literalinclude:: {reldir}/{fname}.py\n' \
              + '   :language: python\n' \
              + '   :linenos:\n' \
              + '\n' \
    # Write to examples.rst
    with open(foutput, 'w') as f:
        f.write(content)


generate_examples_rst()
generate_tests_rst()