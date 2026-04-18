"""Auto-generated tests for fluidsolve.plotlib."""

import inspect

import pytest

import fluidsolve.plotlib as module_under_test


def test_module_importable() -> None:
  assert module_under_test is not None


@pytest.mark.parametrize("name", ['PlotAnnotation', 'PlotAxis', 'PlotButton', 'PlotCurve', 'PlotFigure', 'PlotGraph', 'PlotGrid', 'PlotLine', 'PlotSlider'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)


@pytest.mark.parametrize("name", [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)


@pytest.mark.parametrize("name", [])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)
