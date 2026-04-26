'''Auto-generated tests for fluidsolve.comp_pump.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import pytest
import fluidsolve.comp_pump as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Comp_Pump', 'Comp_PumpCentrifugal', 'Comp_PumpParallel', 'Comp_PumpSerial'])
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

@pytest.mark.parametrize('name', ['N_CURVE_POINTS', 'Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_comp_pump_requires_curve_data_by_default() -> None:
  with pytest.raises(ValueError, match='No pump data'):
    module_under_test.Comp_Pump(speed0=2900)

def test_comp_pump_initializes_curve_properties_and_metadata() -> None:
  pump = module_under_test.Comp_Pump(
    vendor='demo',
    spec='model',
    din=50,
    dout=40,
    speed0=2900,
    dataQH=[0, 12, 10, 6, 20, 0],
  )

  assert pump.vendor == 'demo'
  assert pump.spec == 'model'
  assert pump.din == 50 * module_under_test.u.mm
  assert pump.dout == 40 * module_under_test.u.mm
  assert pump.speed0 == 2900 * module_under_test.u.rpm
  assert pump.speed == 2900 * module_under_test.u.rpm
  assert pump.Qb == 0 * module_under_test.u.m**3 / module_under_test.u.h
  assert pump.Qe == 20 * module_under_test.u.m**3 / module_under_test.u.h
  assert pump.Qc == 0 * module_under_test.u.m**3 / module_under_test.u.h
  assert pump.Hb == 0 * module_under_test.u.m
  assert pump.He == 12 * module_under_test.u.m

def test_comp_pump_calcH_and_calcQ_cover_forward_reverse_and_clamping() -> None:
  pump = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 12, 10, 6, 20, 0])

  assert pump.calcH(5).to(module_under_test.u.m).magnitude == pytest.approx(9.0)
  assert pump.calcH(5, sense=-1).to(module_under_test.u.m).magnitude == 0.0
  assert pump.calcH(-5, sense=-1).to(module_under_test.u.m).magnitude == pytest.approx(9.0)
  assert pump.calcH(25).to(module_under_test.u.m).magnitude == 0.0

  assert pump.calcQ(6 * module_under_test.u.m).to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(10.0)
  assert pump.calcQ(-1 * module_under_test.u.m).to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(21.666666666666668)

def test_comp_pump_speed_setter_accepts_scalar_and_updates_quantity() -> None:
  pump = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 12, 10, 6, 20, 0])

  pump.speed = 1450
  assert pump.speed == 1450 * module_under_test.u.rpm
  assert pump.calcH(5).to(module_under_test.u.m).magnitude == pytest.approx(9.0)

def test_comp_pump_to_string_includes_metadata() -> None:
  pump = module_under_test.Comp_Pump(vendor='demo', spec='model', speed0=2900, dataQH=[0, 12, 10, 6, 20, 0])

  text = pump.toString()
  assert 'Pump: demo: model' in text
  assert 'speed0:2900 revolutions_per_minute' in text

def test_comp_pump_centrifugal_scales_curve_with_speed_and_impeller() -> None:
  pump = module_under_test.Comp_PumpCentrifugal(
    speed0=2900,
    speed=1450,
    impeller0=100,
    impeller=50,
    dataQH=[0, 12, 10, 6, 20, 0],
  )

  assert pump.impeller0 == 100 * module_under_test.u.mm
  assert pump.impeller == 50 * module_under_test.u.mm
  assert pump.Qe.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.5)
  assert pump.calcH(2.5).to(module_under_test.u.m).magnitude == pytest.approx(0.375)

def test_comp_pump_centrifugal_trims_negative_head_data() -> None:
  pump = module_under_test.Comp_PumpCentrifugal(
    speed0=2900,
    impeller0=100,
    dataQH=[0, 12, 10, 4, 20, -1],
  )

  assert pump.Qe.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(10.0)
  assert pump.calcH(20).to(module_under_test.u.m).magnitude == 0.0

def test_comp_pump_serial_combines_pump_heads() -> None:
  pump_a = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 10, 10, 5, 20, 0])
  pump_b = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 8, 10, 4, 20, 0])
  serial = module_under_test.Comp_PumpSerial(pumps=[pump_a, pump_b])

  assert serial.Qb == 0 * module_under_test.u.m**3 / module_under_test.u.h
  assert serial.Qe == 20 * module_under_test.u.m**3 / module_under_test.u.h
  assert serial.calcH(10).to(module_under_test.u.m).magnitude == pytest.approx(9.0)
  assert serial.calcH(10, sense=-1).to(module_under_test.u.m).magnitude == 0.0
  assert serial.calcQ(9 * module_under_test.u.m).to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(10.0)

def test_comp_pump_serial_requires_at_least_one_pump() -> None:
  with pytest.raises(ValueError, match='less than min 1'):
    module_under_test.Comp_PumpSerial(pumps=[])

def test_comp_pump_parallel_combines_flows() -> None:
  pump_a = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 10, 10, 5, 20, 0])
  pump_b = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 8, 10, 4, 20, 0])
  parallel = module_under_test.Comp_PumpParallel(pumps=[pump_a, pump_b])

  assert parallel.Qb.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude > 0
  assert parallel.Qe.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude > parallel.Qb.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude
  assert parallel.calcQ(5 * module_under_test.u.m).to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(17.5)
  assert parallel.calcH(17.5).to(module_under_test.u.m).magnitude == pytest.approx(5.0)

def test_serial_and_parallel_to_string_include_labels() -> None:
  pump = module_under_test.Comp_Pump(speed0=2900, dataQH=[0, 10, 10, 5, 20, 0])

  serial = module_under_test.Comp_PumpSerial(pumps=[pump])
  parallel = module_under_test.Comp_PumpParallel(pumps=[pump])

  assert 'Serial pumps:' in serial.toString()
  assert 'Parallel pumps:' in parallel.toString()
