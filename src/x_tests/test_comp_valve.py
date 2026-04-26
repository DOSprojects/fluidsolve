'''Auto-generated tests for fluidsolve.comp_valve.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import pytest
import fluidsolve.comp_valve as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Comp_Valve', 'Comp_Valve_01', 'Comp_Valve_3W', 'Comp_Valve_DS', 'Comp_Valve_Kv', 'Comp_Valve_NR'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

def test_public_functions_are_callable() -> None:
  public_function_names = [
    name
    for name, obj in inspect.getmembers(module_under_test, inspect.isfunction)
    if obj.__module__ == module_under_test.__name__ and not name.startswith('_')
  ]

  for name in public_function_names:
    obj = getattr(module_under_test, name)
    assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_comp_valve_base_properties_and_to_string() -> None:
  valve = module_under_test.Comp_Valve(name='valve', D=50, state=1)

  assert valve.group == 'Resistance'
  assert valve.part == 'Valve'
  assert valve.state == 1
  assert valve.calcK(1, sense=1) == 0.0
  assert 'State:1.00' in valve.toString()
  assert 'D:50.00 mm' in valve.toString()

def test_comp_valve_base_calcH_uses_loss_conversion(monkeypatch) -> None:
  valve = module_under_test.Comp_Valve(D=50)

  monkeypatch.setattr(module_under_test.flsu, 'Qtov', lambda flow, diameter: 3.0)
  monkeypatch.setattr(module_under_test.flsu, 'KtoH', lambda loss, velocity: (loss + velocity) * module_under_test.u.m)
  monkeypatch.setattr(valve, 'calcK', lambda *args, **kwargs: 2.0)

  assert valve.calcH(10).magnitude == pytest.approx(-5.0)

def test_comp_valve_nr_allows_only_forward_flow() -> None:
  valve = module_under_test.Comp_Valve_NR(D=50)

  assert valve.calcK(1, sense=1, pin=1, pout=2) == 0.0
  assert valve.calcK(1, sense=1, pin=2, pout=1) == 1e6
  assert valve.calcK(1, sense=-1, pin=1, pout=2) == 1e6

def test_comp_valve_01_switches_between_open_and_closed() -> None:
  valve = module_under_test.Comp_Valve_01(D=50, state=0)
  assert valve.calcK(1, sense=1) == 1e6

  valve.state = 1
  assert valve.calcK(1, sense=1) == 0.0

def test_comp_valve_kv_properties_setters_and_calcK() -> None:
  valve = module_under_test.Comp_Valve_Kv(D=50, Kvs=25, R=4, state=0.5)

  assert valve.Kvs == 25
  assert valve.R == 4
  expected_kv_half = 25.0 * (4.0 ** 0.5 - 1.0) / 3.0
  assert valve.calcK(1, sense=1) == pytest.approx(module_under_test.flsu.KvtoK(expected_kv_half, 50 * module_under_test.u.mm))

  valve.Kvs = 30
  valve.R = 9
  valve.state = 1.0
  assert valve.Kvs == 30
  assert valve.R == 9
  assert valve.calcK(1, sense=1) == pytest.approx(module_under_test.flsu.KvtoK(30.0, 50 * module_under_test.u.mm))

  valve.state = 0.0
  assert valve.calcK(1, sense=1) == 1e6

  valve.state = 0.01
  k_001 = valve.calcK(1, sense=1)
  valve.state = 0.02
  k_002 = valve.calcK(1, sense=1)

  assert k_001 <= 1e6
  assert k_001 > k_002

def test_comp_valve_3w_connections_and_calcK_errors() -> None:
  valve = module_under_test.Comp_Valve_3W(D=50, state=1)

  assert valve.connections() == [(1, 2)]
  assert valve.connections(state=2) == [(1, 3)]
  assert valve.calcK(1, pin=1, pout=2) == pytest.approx(0.7)
  assert valve.calcK(1, pin=2, pout=1) == pytest.approx(0.7)
  assert valve.calcK(1, pin=2, pout=3) == 1e6

  valve.state = 3
  with pytest.raises(ValueError, match='Invalid state for 3-way valve'):
    valve.calcK(1, pin=1, pout=2)

  valve.state = 1
  with pytest.raises(ValueError, match='Invalid ports for 3-way valve'):
    valve.calcK(1, pin=0, pout=2)
  with pytest.raises(ValueError, match='pin and pout must be different'):
    valve.calcK(1, pin=1, pout=1)

def test_comp_valve_ds_connections_and_calcK_errors() -> None:
  valve = module_under_test.Comp_Valve_DS(D=50, state=1)

  assert not valve.connections()
  assert valve.connections(state=1) == [(1, 2), (3, 4)]
  assert valve.connections(state=2) == [(1, 3), (2, 4)]
  assert valve.calcK(1, pin=1, pout=2) == pytest.approx(0.7)
  assert valve.calcK(1, pin=2, pout=4) == 1e6

  valve.state = 2
  assert valve.calcK(1, pin=2, pout=4) == pytest.approx(0.7)

  valve.state = 9
  with pytest.raises(ValueError, match='Invalid state for 3-way valve'):
    valve.calcK(1, pin=1, pout=2)

  valve.state = 1
  with pytest.raises(ValueError, match='Invalid ports for 3-way valve'):
    valve.calcK(1, pin=5, pout=2)
  with pytest.raises(ValueError, match='pin and pout must be different'):
    valve.calcK(1, pin=1, pout=1)
