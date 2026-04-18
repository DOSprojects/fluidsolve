"""Behavioral unit tests for fluidsolve.catalogue."""

import inspect
import json

import pytest

import fluidsolve.catalogue as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", ["Catalogue"])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)


@pytest.mark.parametrize("name", ["Quantity", "u"])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)


def test_catalogue_loads_builtin_libraries() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries()
  assert len(libs) > 0
  assert "PUMP:C:APV" in libs
  assert "PIPE:NW" in libs


def test_find_libraries_matchcase_false() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries("apv", matchcase=False)
  assert "PUMP:C:APV" in libs


def test_find_libraries_with_expression() -> None:
  cat = module_under_test.Catalogue(load=True)
  libs = cat.findLibraries("pump AND centrifugal")
  assert "PUMP:C:APV" in libs


def test_search_in_library_with_numeric_and_string_criteria() -> None:
  cat = module_under_test.Catalogue(load=True)
  records = cat.searchInLibrary(
    "PUMP:C:APV",
    'T = centrifugal AND spec = "W+ 22/20" AND impeller0 = 110 AND speed0 = 2900',
  )
  assert len(records) >= 1
  for rec in records:
    assert rec["T"] == "centrifugal"
    assert rec["spec"] == "W+ 22/20"
    assert rec["impeller0"] == 110
    assert rec["speed0"] == 2900


def test_search_in_library_list_input() -> None:
  cat = module_under_test.Catalogue(load=True)
  records = cat.searchInLibrary(["PIPE:NW"], "OD < 20")
  dns = {rec["DN"] for rec in records}
  assert "DN10" in dns
  assert "DN15" in dns


def test_parse_expression_builds_tree_for_and_or() -> None:
  cat = module_under_test.Catalogue(load=False)
  parsed = cat._parseExpression(["A", "AND", "(", "B", "OR", "C", ")"])  # pylint: disable=protected-access
  assert "AND" in parsed
  assert parsed["AND"][0] == "A"
  assert "OR" in parsed["AND"][1]


def test_eval_record_expression_supports_not() -> None:
  cat = module_under_test.Catalogue(load=False)
  expr = {"NOT": "OD < 10"}
  rec = {"OD": 13.0}
  assert cat._evalRecExpression(expr, rec) is True  # pylint: disable=protected-access


def test_load_data_from_custom_path_only(tmp_path) -> None:
  data = {
    "library": {
      "name": "TEST:LIB",
      "keywords": ["demo", "custom"],
      "norm": [],
    },
    "keys": ["k", "v"],
    "records": [{"k": "x", "v": 1}],
  }
  file_path = tmp_path / "test_lib.json"
  file_path.write_text(json.dumps(data), encoding="utf-8")

  cat = module_under_test.Catalogue(path=str(tmp_path), load=False)
  cat.loadAllData(buildin=False)
  libs = cat.findLibraries()
  assert libs == ["TEST:LIB"]
