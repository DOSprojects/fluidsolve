"""Behavioral unit tests for fluidsolve.aux_tools."""

import inspect
import pytest
import fluidsolve.aux_tools as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize("name", ["GetArgs", "vFun"])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize("name", ["getPumpCurveDataText", "prepareArgs", "spec", "toUnits"])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

def test_toUnits_scalar_to_quantity() -> None:
  q = module_under_test.toUnits(2, module_under_test.u.m)
  assert q.magnitude == 2
  assert q.units == module_under_test.u.m

def test_toUnits_quantity_conversion_and_magnitude() -> None:
  value = 250 * module_under_test.u.cm
  out = module_under_test.toUnits(value, module_under_test.u.m, magnitude=True)
  assert out == 2.5

def test_toUnits_none_value_raises() -> None:
  with pytest.raises(ValueError, match="Value is None"):
    module_under_test.toUnits(None, module_under_test.u.m)  # type: ignore[arg-type]

def test_prepareArgs_filters_none_values() -> None:
  args = module_under_test.prepareArgs(a=1, b=None, c="x")
  assert args == {"a": 1, "c": "x"}

def test_getPumpCurveDataText_parses_whitespace_and_commas() -> None:
  data = """
    1, 2
    3 4
  """
  assert module_under_test.getPumpCurveDataText(data) == [1.0, 2.0, 3.0, 4.0]

def test_spec_returns_input_kwargs_as_dict() -> None:
  out = module_under_test.spec(comp="Tube", nodes=["A", "B"], sense=-1, D=50)
  assert out == {"comp": "Tube", "nodes": ["A", "B"], "sense": -1, "D": 50}

def test_getargs_with_validators_and_remove() -> None:
  args = module_under_test.GetArgs({"name": "  abc  "})
  result = args.getArg("name", [module_under_test.vFun.stripspaces(), module_under_test.vFun.toupper()])
  assert result == "ABC"
  assert args.restArgs() == {}

def test_getargs_default_when_missing() -> None:
  args = module_under_test.GetArgs({})
  result = args.getArg("speed", [module_under_test.vFun.default(2900)])
  assert result == 2900

def test_getargs_missing_without_default_raises() -> None:
  args = module_under_test.GetArgs({})
  with pytest.raises(ValueError, match="Name speed not found"):
    args.getArg("speed", [module_under_test.vFun.istype(int)])

def test_vfun_istype_rejects_wrong_type() -> None:
  validator = module_under_test.vFun.istype(int)
  with pytest.raises(ValueError, match="not of type"):
    validator("n", "3")

def test_vfun_inlist_allows_and_rejects() -> None:
  validator = module_under_test.vFun.inlist("a", "b", "c")
  assert validator("k", "b") == "b"
  with pytest.raises(ValueError, match="must be one of"):
    validator("k", "z")

def test_vfun_regex_inv_true_requires_match() -> None:
  validator = module_under_test.vFun.regex(r"^[A-Z]+$", inv=True)
  assert validator("code", "ABC") == "ABC"
  with pytest.raises(ValueError, match="must conform to regex"):
    validator("code", "Abc")

def test_vfun_fileexists(tmp_path) -> None:
  file_path = tmp_path / "x.txt"
  file_path.write_text("ok", encoding="utf-8")
  validator = module_under_test.vFun.fileexists()
  assert validator("file", str(file_path)) == str(file_path)
  with pytest.raises(ValueError, match="does not exist"):
    validator("file", str(file_path.with_name("missing.txt")))
