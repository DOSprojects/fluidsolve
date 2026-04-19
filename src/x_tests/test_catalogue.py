'''Behavioral unit tests for fluidsolve.catalogue.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import json
import pytest
import fluidsolve.catalogue as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Catalogue'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_catalogue_loads_builtin_libraries() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries()
  assert len(libs) > 0
  assert 'PUMP:C:APV' in libs
  assert 'PIPE:NW' in libs

def test_find_libraries_matchcase_false() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries('apv', matchcase=False)
  assert 'PUMP:C:APV' in libs

def test_find_libraries_with_expression() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries('pump AND centrifugal')
  assert 'PUMP:C:APV' in libs

def test_search_in_library_with_numeric_and_string_criteria() -> None:
  cat = module_under_test.Catalogue(load=True)
  records = cat.searchInLibrary(
    'PUMP:C:APV',
    'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900',
  )
  assert len(records) >= 1
  for rec in records:
    assert rec['T'] == 'centrifugal'
    assert rec['spec'] == 'W+ 22/20'
    assert rec['impeller0'] == 110
    assert rec['speed0'] == 2900

def test_search_in_library_list_input() -> None:
  cat = module_under_test.Catalogue(load=True)
  records = cat.searchInLibrary(['PIPE:NW'], 'OD < 20')
  dns = {rec['DN'] for rec in records}
  assert 'DN10' in dns
  assert 'DN15' in dns

def test_parse_expression_builds_tree_for_and_or() -> None:
  cat = module_under_test.Catalogue(load=False)
  parsed = cat._parseExpression(['A', 'AND', '(', 'B', 'OR', 'C', ')'])  # pylint: disable=protected-access
  assert 'AND' in parsed
  assert parsed['AND'][0] == 'A'
  assert 'OR' in parsed['AND'][1]

def test_eval_record_expression_supports_not() -> None:
  cat = module_under_test.Catalogue(load=False)
  expr = {'NOT': 'OD < 10'}
  rec = {'OD': 13.0}
  assert cat._evalRecExpression(expr, rec) is True  # pylint: disable=protected-access

def test_load_data_from_custom_path_only(tmp_path) -> None:
  data = {
    'library': {
      'name': 'TEST:LIB',
      'keywords': ['demo', 'custom'],
      'norm': [],
    },
    'keys': ['k', 'v'],
    'records': [{'k': 'x', 'v': 1}],
  }
  file_path = tmp_path / 'test_lib.json'
  file_path.write_text(json.dumps(data), encoding='utf-8')
  cat = module_under_test.Catalogue(path=str(tmp_path), load=False)
  cat.loadAllData(buildin=False)
  libs = cat.findLibraries()
  assert libs == ['TEST:LIB']

def test_catalogue_init_normalizes_path_string_to_single_item_list(tmp_path) -> None:
  cat = module_under_test.Catalogue(path=str(tmp_path), load=False)
  assert cat._path == [str(tmp_path)]  # pylint: disable=protected-access

def test_load_all_data_reports_invalid_json_and_skips_file(tmp_path, capsys) -> None:
  valid_data = {
    'library': {'name': 'VALID:LIB', 'keywords': ['valid'], 'norm': []},
    'keys': ['name'],
    'records': [{'name': 'demo'}],
  }
  (tmp_path / 'valid.json').write_text(json.dumps(valid_data), encoding='utf-8')
  (tmp_path / 'broken.json').write_text('{not valid json', encoding='utf-8')
  cat = module_under_test.Catalogue(path=str(tmp_path), load=False)
  cat.loadAllData(buildin=False)
  captured = capsys.readouterr()
  assert 'Error decoding JSON from file' in captured.out
  assert cat.findLibraries() == ['VALID:LIB']

def test_find_libraries_empty_criteria_returns_all_loaded_keys() -> None:
  cat = module_under_test.Catalogue(load=False)
  cat._d = {  # pylint: disable=protected-access
    'LIB:A': {'library': {'name': 'LIB:A', 'keywords': ['pump'], 'norm': []}, 'records': []},
    'LIB:B': {'library': {'name': 'LIB:B', 'keywords': ['valve'], 'norm': []}, 'records': []},
  }
  assert cat.findLibraries() == ['LIB:A', 'LIB:B']

def test_find_libraries_supports_not_and_wildcards() -> None:
  cat = module_under_test.Catalogue(load=False)
  cat._d = {  # pylint: disable=protected-access
    'PUMP:C:APV': {'library': {'name': 'PUMP:C:APV', 'keywords': ['pump', 'centrifugal', 'APV'], 'norm': []}, 'records': []},
    'VALVE:C:GEN': {'library': {'name': 'VALVE:C:GEN', 'keywords': ['valve', 'control'], 'norm': []}, 'records': []},
  }
  assert cat.findLibraries('pump AND A*') == ['PUMP:C:APV']
  assert cat.findLibraries('NOT valve') == ['PUMP:C:APV']

def test_search_in_library_respects_matchcase_for_record_strings() -> None:
  cat = module_under_test.Catalogue(load=False)
  cat._d = {  # pylint: disable=protected-access
    'TEST:LIB': {
      'library': {'name': 'TEST:LIB', 'keywords': ['demo'], 'norm': []},
      'records': [
        {'kind': 'Pump', 'dn': 20},
        {'kind': 'Valve', 'dn': 25},
      ],
    },
  }
  assert cat.searchInLibrary('TEST:LIB', 'kind = pump', matchcase=False) == [{'kind': 'Pump', 'dn': 20}]
  assert not cat.searchInLibrary('TEST:LIB', 'kind = pump', matchcase=True)

def test_parse_expression_keeps_quoted_values_with_spaces_together() -> None:
  cat = module_under_test.Catalogue(load=False)
  parsed = cat._parseExpression(['spec', '=', '"W+', '22/20"', 'AND', 'speed0', '=', '2900'])  # pylint: disable=protected-access
  assert parsed == {'AND': ['spec = "W+ 22/20"', 'speed0 = 2900']}

def test_parse_expression_unclosed_quote_raises_value_error() -> None:
  cat = module_under_test.Catalogue(load=False)
  with pytest.raises(ValueError, match='Unclosed quoted value'):
    cat._parseExpression(['spec', '=', '"W+'])  # pylint: disable=protected-access

def test_eval_library_expression_raises_for_invalid_expression_shape() -> None:
  cat = module_under_test.Catalogue(load=False)
  with pytest.raises(ValueError, match='Invalid expression format'):
    cat._evalLibExpression({'XOR': ['pump', 'valve']}, ['pump'])  # pylint: disable=protected-access

def test_eval_record_expression_supports_comparisons_and_missing_fields() -> None:
  cat = module_under_test.Catalogue(load=False)
  rec = {'dn': 25, 'kind': 'Valve'}
  assert cat._evalRecExpression('dn >= 20', rec) is True  # pylint: disable=protected-access
  assert cat._evalRecExpression('kind != Pump', rec) is True  # pylint: disable=protected-access
  assert cat._evalRecExpression('missing = x', rec) is False  # pylint: disable=protected-access

def test_eval_record_expression_raises_for_invalid_inputs() -> None:
  cat = module_under_test.Catalogue(load=False)
  with pytest.raises(ValueError, match='Invalid atomic criterion'):
    cat._evalRecExpression('invalid criterion', {'dn': 25})  # pylint: disable=protected-access
  with pytest.raises(ValueError, match='Invalid expression format'):
    cat._evalRecExpression({'XOR': ['dn > 10', 'dn < 30']}, {'dn': 25})  # pylint: disable=protected-access
