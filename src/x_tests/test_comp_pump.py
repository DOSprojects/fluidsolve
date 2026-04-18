"""Auto-generated tests for fluidsolve.comp_pump."""

import inspect

import pytest

import fluidsolve.comp_pump as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", ['Comp_Pump', 'Comp_PumpCentrifugal', 'Comp_PumpParallel', 'Comp_PumpSerial'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)


@pytest.mark.parametrize("name", [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)


@pytest.mark.parametrize("name", ['N_CURVE_POINTS', 'Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)
