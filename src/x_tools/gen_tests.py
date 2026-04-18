'''
gen_tests.py

Generate unit-test module skeletons into src/x_tests from src/fluidsolve modules.

Usage:
  python src/x_tools/gen_tests.py
  python src/x_tools/gen_tests.py --overwrite
'''
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import ast


EXCLUDE_MODULES = {
  '__init__',
  '__main__',
  '___version',
}


@dataclass
class ModuleSymbols:
  module_name: str
  classes: list[str]
  functions: list[str]
  variables: list[str]


def _project_src_root() -> Path:
  return Path(__file__).resolve().parents[1]


def _collect_public_symbols(module_file: Path) -> ModuleSymbols:
  module_name = module_file.stem
  classes: list[str] = []
  functions: list[str] = []
  variables: list[str] = []

  tree = ast.parse(module_file.read_text(encoding='utf-8'), filename=str(module_file))

  for node in tree.body:
    if isinstance(node, ast.ClassDef):
      if not node.name.startswith('_'):
        classes.append(node.name)
      continue

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
      if not node.name.startswith('_'):
        functions.append(node.name)
      continue

    if isinstance(node, ast.Assign):
      for target in node.targets:
        if isinstance(target, ast.Name) and not target.id.startswith('_'):
          variables.append(target.id)
      continue

    if isinstance(node, ast.AnnAssign):
      target = node.target
      if isinstance(target, ast.Name) and not target.id.startswith('_'):
        variables.append(target.id)

  return ModuleSymbols(
    module_name=module_name,
    classes=sorted(set(classes)),
    functions=sorted(set(functions)),
    variables=sorted(set(variables)),
  )


def _render_list(values: list[str]) -> str:
  if not values:
    return '[]'
  return '[' + ', '.join(repr(v) for v in values) + ']'


def _build_test_content(symbols: ModuleSymbols) -> str:
  module_name = symbols.module_name
  class_list = _render_list(symbols.classes)
  function_list = _render_list(symbols.functions)
  variable_list = _render_list(symbols.variables)

  return f'''"""Auto-generated tests for fluidsolve.{module_name}."""

import inspect

import pytest

import fluidsolve.{module_name} as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", {class_list})
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)


@pytest.mark.parametrize("name", {function_list})
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)


@pytest.mark.parametrize("name", {variable_list})
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)
'''


def generate_tests(overwrite: bool = False) -> tuple[list[Path], list[Path]]:
  src_root = _project_src_root()
  pkg_dir = src_root / 'fluidsolve'
  tests_dir = src_root / 'x_tests'
  tests_dir.mkdir(parents=True, exist_ok=True)

  created: list[Path] = []
  skipped: list[Path] = []

  module_files = sorted(
    file_path for file_path in pkg_dir.glob('*.py')
    if file_path.stem not in EXCLUDE_MODULES
  )

  for module_file in module_files:
    symbols = _collect_public_symbols(module_file)
    test_file = tests_dir / f'test_{symbols.module_name}.py'

    if test_file.exists() and not overwrite:
      skipped.append(test_file)
      continue

    content = _build_test_content(symbols)
    test_file.write_text(content, encoding='utf-8')
    created.append(test_file)

  return created, skipped


def main() -> None:
  parser = argparse.ArgumentParser(description='Generate x_tests test module skeletons.')
  parser.add_argument(
    '--overwrite',
    action='store_true',
    help='Overwrite existing test files in x_tests.',
  )
  args = parser.parse_args()

  created, skipped = generate_tests(overwrite=args.overwrite)

  print('Generated test files:')
  if created:
    for path in created:
      print(f'  + {path}')
  else:
    print('  + <none>')

  print('Skipped existing files:')
  if skipped:
    for path in skipped:
      print(f'  - {path}')
  else:
    print('  - <none>')


if __name__ == '__main__':
  main()
