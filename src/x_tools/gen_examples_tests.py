'''
gen_examples_tests.py

Generate docs/source/examples.rst and docs/source/tests.rst from static snippets
and discovered Python modules.
'''
from pathlib import Path


def _doc_root() -> Path:
    '''Return the documentation root directory (doc).'''
    return Path(__file__).resolve().parents[2] / 'doc'

def generate_examples_rst():
    '''Generate examples.rst from x_examples modules and static content.'''
    doc_root = _doc_root()
    fstatic = doc_root / 'source' / '_gen' / 'examples_static.rst'
    examples_dir = Path(__file__).resolve().parents[1] / 'x_examples'
    reldir = '../../src/x_examples'
    foutput = doc_root / 'source' / 'examples.rst'
    # Read static content
    content = ''
    if fstatic.exists():
      with fstatic.open('r', encoding='utf-8') as fhandle:
        content = fhandle.read()
    # List all .py files in the directory (excluding __init__.py)
    py_files = []
    if examples_dir.exists():
      py_files = [f.name for f in examples_dir.glob('*.py') if f.name != '__init__.py']
      py_files.sort()
    for py_file in py_files:
      fname = Path(py_file).stem
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
    with foutput.open('w', encoding='utf-8') as f:
        f.write(content)

def generate_tests_rst():
    '''Generate tests.rst from x_tests modules and static content.'''
    doc_root = _doc_root()
    fstatic = doc_root / 'source' / '_gen' / 'tests_static.rst'
    tests_dir = Path(__file__).resolve().parents[1] / 'x_tests'
    reldir = '../../src/x_tests'
    foutput = doc_root / 'source' / 'tests.rst'
    # Read static content
    content = ''
    if fstatic.exists():
      with fstatic.open('r', encoding='utf-8') as fhandle:
        content = fhandle.read()
    # List all .py files in the directory (excluding __init__.py)
    py_files = []
    if tests_dir.exists():
      py_files = [f.name for f in tests_dir.glob('*.py') if f.name != '__init__.py']
      py_files.sort()
    for py_file in py_files:
      fname = Path(py_file).stem
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
    with foutput.open('w', encoding='utf-8') as f:
        f.write(content)


def main() -> None:
    '''Generate both examples and tests documentation pages.'''
    generate_examples_rst()
    generate_tests_rst()


if __name__ == '__main__':
    main()