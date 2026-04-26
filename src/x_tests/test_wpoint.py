'''Behavioral unit tests for fluidsolve.wpoint.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,unused-argument,no-member

import inspect
import types
import pytest
import fluidsolve.wpoint as module_under_test

u = module_under_test.u

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Wpoint', 'WpointDyn'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', ['calcOperatingPoint'])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

class DummyComp(module_under_test.flsb.Comp_Base):
  _group = 'Test'
  _part = 'Dummy'

  def __init__(self, name: str='C', factor: float=1.0) -> None:
    super().__init__(name=name)
    self.factor = factor
    self.calls = []

  def calcH(self, Q, sense: int=1, pin: int=1, pout: int=2):
    self.calls.append((Q, sense, pin, pout))
    q_mag = Q.to(u.m**3 / u.h).magnitude if hasattr(Q, 'to') else float(Q)
    return self.factor * q_mag * sense * u.m

def test_wpoint_defaults_setters_and_magnitudes() -> None:
  point = module_under_test.Wpoint()

  assert point.name == ''
  assert point.Qmag == 0.0
  assert point.Hmag == 0.0

  point.name = 'WP1'
  point.Q = 3.5
  point.H = 8.0
  flow = point.Q
  head = point.H

  assert point.name == 'WP1'
  assert getattr(flow, 'to')(u.m**3 / u.h).magnitude == pytest.approx(3.5)
  assert getattr(head, 'to')(u.m).magnitude == pytest.approx(8.0)
  assert point.Qmag == pytest.approx(3.5)
  assert point.Hmag == pytest.approx(8.0)
  assert point.update() is point

def test_wpoint_string_and_repr_for_named_and_unnamed() -> None:
  unnamed = module_under_test.Wpoint(Q=2.0, H=4.0)
  named = module_under_test.Wpoint(name='NodeA', Q=2.0, H=4.0)

  assert str(unnamed).startswith('Pt: Q:')
  assert repr(unnamed).startswith('Pt: Q:')
  assert 'Pt NodeA:' in str(named)
  assert 'Pt NodeA:' in repr(named)

def test_calc_operating_point_returns_expected_values(monkeypatch) -> None:
  comp1 = DummyComp('C1', factor=-2.0)
  comp2 = DummyComp('C2', factor=3.0)

  monkeypatch.setattr(
    module_under_test,
    'root',
    lambda func, x0, method='hybr': types.SimpleNamespace(success=True, x=[2.5], message='ok', status=1),
  )

  q_op, h_op = module_under_test.calcOperatingPoint(comp1, comp2, guess=1.0)

  assert q_op.to(u.m**3 / u.h).magnitude == pytest.approx(2.5)
  assert h_op.to(u.m).magnitude == pytest.approx(7.5)
  assert hasattr(comp2.calls[-1][0], 'to')

def test_calc_operating_point_raises_when_solver_fails(monkeypatch) -> None:
  comp1 = DummyComp('C1', factor=-2.0)
  comp2 = DummyComp('C2', factor=3.0)

  monkeypatch.setattr(
    module_under_test,
    'root',
    lambda func, x0, method='hybr': types.SimpleNamespace(success=False, x=[1.0], message='no convergence', status=4),
  )

  with pytest.warns(RuntimeWarning, match='did not converge|no convergence'):
    q_op, h_op = module_under_test.calcOperatingPoint(comp1, comp2)

  assert q_op.to(u.m**3 / u.h).magnitude == 0.0
  assert h_op.to(u.m).magnitude == 0.0

def test_wpointdyn_uses_components_and_updates_from_operating_point(monkeypatch) -> None:
  comp1 = DummyComp('C1', factor=-1.0)
  comp2 = DummyComp('C2', factor=2.0)

  monkeypatch.setattr(
    module_under_test,
    'calcOperatingPoint',
    lambda s1, s2, guess: (4.0 * u.m**3 / u.h, 6.0 * u.m),
  )

  point = module_under_test.WpointDyn(name='dyn', s1=comp1, s2=comp2, guess=10)

  assert point.name == 'dyn'
  assert point.Qmag == pytest.approx(4.0)
  assert point.Hmag == pytest.approx(6.0)

  point.update()
  assert point.Qmag == pytest.approx(4.0)
  assert point.Hmag == pytest.approx(6.0)

def test_wpointdyn_without_components_keeps_initial_values() -> None:
  with pytest.raises(ValueError, match='argument s1 not of type'):
    module_under_test.WpointDyn(name='dyn', Q=1.0, H=2.0)
