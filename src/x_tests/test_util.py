'''Behavioral unit tests for fluidsolve.util.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring,missing-class-docstring,protected-access,unused-argument

import inspect
import pytest
import fluidsolve.util as module_under_test

u = module_under_test.u

def test_module_importable() -> None:
  assert module_under_test is not None

def test_public_classes_exist() -> None:
  public_class_names = [
    name
    for name, obj in inspect.getmembers(module_under_test, inspect.isclass)
    if obj.__module__ == module_under_test.__name__ and not name.startswith('_')
  ]

  for name in public_class_names:
    obj = getattr(module_under_test, name)
    assert inspect.isclass(obj)

@pytest.mark.parametrize('name', ['CvtoK', 'CvtoKv', 'FdtoK', 'Htop', 'KtoCv', 'KtoFd', 'KtoH', 'KtoKv', 'Ktop', 'KvtoCv', 'KvtoK', 'Qtov', 'calcCurve', 'calcOrifice', 'calcOrifice2', 'ptoH', 'vtoQ'])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_k_fd_conversions_roundtrip() -> None:
  k_loss = 3.2
  length = 12 * u.m
  diameter = 80 * u.mm

  fd = module_under_test.KtoFd(k_loss, length, diameter)
  k_back = module_under_test.FdtoK(fd, length, diameter)

  assert k_back == pytest.approx(k_loss)

def test_kv_cv_and_k_conversions_roundtrip() -> None:
  diameter = 50 * u.mm
  kv = 25 * u.m**3 / u.h

  cv = module_under_test.KvtoCv(kv)
  kv_back = module_under_test.CvtoKv(cv)

  assert kv_back.to(u.m**3 / u.h).magnitude == pytest.approx(kv.to(u.m**3 / u.h).magnitude)
  with pytest.raises(Exception):
    module_under_test.KtoKv(15.0, diameter)

def test_head_pressure_and_velocity_flow_conversions_are_consistent() -> None:
  rho = 998 * u.kg / u.m**3
  head = 12 * u.m
  pressure = module_under_test.Htop(head, rho)
  head_back = module_under_test.ptoH(pressure, rho)

  flow = 9 * u.m**3 / u.h
  diameter = 100 * u.mm
  velocity = module_under_test.Qtov(flow, diameter)
  flow_back = module_under_test.vtoQ(velocity, diameter)

  assert head_back.to(u.m).magnitude == pytest.approx(head.to(u.m).magnitude)
  assert flow_back.to(u.m**3 / u.h).magnitude == pytest.approx(flow.to(u.m**3 / u.h).magnitude)

def test_ktoh_and_ktop_match_via_density_conversion() -> None:
  k_loss = 6.0
  velocity = 1.5 * u.m / u.s
  rho = 1000 * u.kg / u.m**3

  head = module_under_test.KtoH(k_loss, velocity)
  pressure_from_head = module_under_test.Htop(head, rho)
  pressure_direct = module_under_test.Ktop(k_loss, velocity, rho)

  assert pressure_from_head.to(u.bar).magnitude == pytest.approx(pressure_direct.to(u.bar).magnitude)

def test_calc_curve_filters_out_of_bounds_and_accepts_quantity_output() -> None:
  x_pts, y_pts = module_under_test.calcCurve(
    xb=0,
    xe=10,
    xn=6,
    yfun=lambda x: (x - 5) * u.m,
    yb=-2,
    ye=2,
  )

  assert list(x_pts) == [4.0, 6.0]
  assert list(y_pts) == [-1.0, 1.0]

def test_calc_orifice_branches_and_solver_arguments(monkeypatch) -> None:
  captured = {}

  def fake_solver(**kwargs):
    captured.clear()
    captured.update(kwargs)
    if kwargs.get('D2') is None:
      return 22 * u.mm
    if kwargs.get('P1') is None:
      return 2.4 * u.bar
    if kwargs.get('P2') is None:
      return 1.1 * u.bar
    if kwargs.get('m') is None:
      return 500 * u.kg / u.h
    return 42.0

  monkeypatch.setattr(module_under_test.fu, 'differential_pressure_meter_solver', fake_solver)

  out_orifice = module_under_test.calcOrifice(Q=3, d=50, Pin=2, Pout=1)
  out_pin = module_under_test.calcOrifice(Q=3, d=50, orifice=25, Pout=1)
  out_pout = module_under_test.calcOrifice(Q=3, d=50, orifice=25, Pin=2)
  out_q = module_under_test.calcOrifice(d=50, orifice=25, Pin=2, Pout=1)

  assert out_orifice.to(u.mm).magnitude == pytest.approx(22)
  assert out_pin.to(u.bar).magnitude == pytest.approx(2.4)
  assert out_pout.to(u.bar).magnitude == pytest.approx(1.1)
  assert out_q.to(u.m**3 / u.h).magnitude > 0.0
  assert captured['meter_type'] == 'ISO 5167 orifice'
  assert captured['taps'] in ['corner', '25 millimeter']

  with pytest.raises(ValueError, match='Name d not found'):
    module_under_test.calcOrifice(Q=3, orifice='corner', Pin=2, Pout=1)

def test_calc_orifice2_returns_diameter_from_newton_solution(monkeypatch) -> None:
  class DummyCircuit:
    rho = 1000 * u.kg / u.m**3
    mu = 1e-3 * u.Pa * u.s
    k = 1.4

    @staticmethod
    def calcH(_Q):
      return 10 * u.m

  monkeypatch.setattr(module_under_test.fu, 'P_from_head', lambda head, rho: 1.0 * u.bar)
  monkeypatch.setattr(module_under_test, 'newton', lambda func, x0, tol: 0.5)

  diameter = module_under_test.calcOrifice2(DummyCircuit(), 4 * u.m**3 / u.h, 80 * u.mm)

  assert diameter.to(u.mm).magnitude == pytest.approx(40.0)
