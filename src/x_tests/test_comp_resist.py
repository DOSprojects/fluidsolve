"""Auto-generated tests for fluidsolve.comp_resist."""

import inspect

import pytest

import fluidsolve.comp_resist as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", ['C_EntranceBeveled', 'Comp_Appendage', 'Comp_Bend', 'Comp_BendLong', 'Comp_ConicalReduction', 'Comp_Entrance', 'Comp_Hstatic', 'Comp_PHE', 'Comp_Parallel', 'Comp_Parallel2', 'Comp_Serial', 'Comp_SharpReduction', 'Comp_Tube'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)


@pytest.mark.parametrize("name", [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)


@pytest.mark.parametrize("name", ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)
