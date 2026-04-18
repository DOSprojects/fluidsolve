"""Auto-generated tests for fluidsolve.comp_valve."""

import inspect

import pytest

import fluidsolve.comp_valve as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", ['Comp_Valve', 'Comp_Valve_01', 'Comp_Valve_3W', 'Comp_Valve_CV', 'Comp_Valve_DS', 'Comp_Valve_NR'])
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
