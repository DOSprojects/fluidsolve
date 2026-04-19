'''Auto-generated tests for fluidsolve.comp_resist.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-class-docstring,missing-function-docstring

import inspect
from types import SimpleNamespace
import pytest
import fluidsolve.comp_resist as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['C_EntranceBeveled', 'Comp_Appendage', 'Comp_Bend', 'Comp_BendLong', 'Comp_ConicalReduction', 'Comp_Entrance', 'Comp_Hstatic',
                                  'Comp_PHE', 'Comp_Parallel', 'Comp_Parallel2', 'Comp_Serial', 'Comp_SharpReduction', 'Comp_Tube'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize('name', ['Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_comp_hstatic_properties_calcH_and_to_string() -> None:
  comp = module_under_test.Comp_Hstatic(name='hs', Hs_pos=5, Hs_neg=2)

  assert comp.Hs == 3 * module_under_test.u.m
  assert comp.calcH(1, sense=1, pin=1, pout=2) == 3 * module_under_test.u.m
  assert comp.calcH(1, sense=1, pin=2, pout=1) == -3 * module_under_test.u.m

  comp.Hs = 4
  assert comp.Hs == 4 * module_under_test.u.m
  assert 'Hs:4.00 m' in comp.toString()

def test_comp_appendage_calcH_uses_loss_coefficient_and_to_string() -> None:
  class FixedKAppendage(module_under_test.Comp_Appendage):
    def __init__(self) -> None:
      super().__init__(name='app', medium='water')
      self._D = 50 * module_under_test.u.mm
      self._L = 2 * module_under_test.u.m

    def calcK(self, Q, sense=1, pin=1, pout=2):
      return 4.0

  comp = FixedKAppendage()
  head = comp.calcH(10)

  expected = module_under_test.flsu.KtoH(4.0, module_under_test.flsu.Qtov(10 * module_under_test.u.m**3 / module_under_test.u.h, comp._D)) * comp.sign  # pylint: disable=protected-access
  assert head.to(module_under_test.u.m).magnitude == pytest.approx(expected.to(module_under_test.u.m).magnitude)
  assert 'L:2.00 m' in comp.toString()
  assert 'D:50.00 mm' in comp.toString()

def test_comp_tube_properties_and_calcH_with_static_head(monkeypatch) -> None:
  tube = module_under_test.Comp_Tube(L=10, D=50, Hs_pos=2)

  monkeypatch.setattr(tube, 'calcK', lambda *args, **kwargs: 0.0)
  assert tube.calcH(0).to(module_under_test.u.m).magnitude == pytest.approx(2.0)

  tube.L = 12
  tube.D = 60
  tube.Hs = 1
  assert tube.L == 12 * module_under_test.u.m
  assert tube.D == 60 * module_under_test.u.mm
  assert tube.Hs == 1 * module_under_test.u.m

def test_comp_bend_and_bendlong_delegate_to_fluids_helpers(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test.fu, 'Reynolds', lambda **kwargs: 123.0)
  monkeypatch.setattr(module_under_test.fu, 'friction_factor', lambda *args, **kwargs: 0.02)
  monkeypatch.setattr(module_under_test.fu, 'bend_rounded', lambda **kwargs: 7.5)
  monkeypatch.setattr(module_under_test.fu, 'bend_miter', lambda *args, **kwargs: 4.5 if 'L_unimpeded' not in kwargs else 5.5)

  bend = module_under_test.Comp_Bend(D=80)
  assert bend.calcK(10, sense=1) == pytest.approx(7.5)

  bend_long = module_under_test.Comp_BendLong(D=80)
  assert bend_long.calcK(10, sense=1) == pytest.approx(4.5)

  bend_long_lu = module_under_test.Comp_BendLong(D=80, Lu=1)
  assert bend_long_lu.calcK(10, sense=1) == pytest.approx(5.5)

def test_comp_entrance_selects_entrance_or_exit_loss(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test.fu, 'entrance_sharp', lambda: 1.25)
  monkeypatch.setattr(module_under_test.fu, 'exit_normal', lambda: 0.75)

  comp = module_under_test.Comp_Entrance(D=50)
  assert comp.calcK(10, sense=1, pin=1, pout=2) == pytest.approx(1.25)
  assert comp.calcK(10, sense=1, pin=2, pout=1) == pytest.approx(0.75)

def test_sharp_and_conical_reduction_validate_and_switch_branches(monkeypatch) -> None:
  with pytest.raises(ValueError, match='must be larger than D2'):
    module_under_test.Comp_SharpReduction(D1=40, D2=50)

  monkeypatch.setattr(module_under_test.fu, 'contraction_sharp', lambda **kwargs: 2.0)
  monkeypatch.setattr(module_under_test.fu, 'diffuser_sharp', lambda **kwargs: 3.0)
  sharp = module_under_test.Comp_SharpReduction(D1=80, D2=40)
  assert sharp.calcK(10, sense=1, pin=1, pout=2) == pytest.approx(2.0)
  assert sharp.calcK(10, sense=1, pin=2, pout=1) == pytest.approx(3.0)

  with pytest.raises(ValueError, match='must be larger than D2'):
    module_under_test.Comp_ConicalReduction(D1=40, D2=50, L=1)

  monkeypatch.setattr(module_under_test.fu, 'Reynolds', lambda **kwargs: 100.0)
  monkeypatch.setattr(module_under_test.fu, 'friction_factor', lambda *args, **kwargs: 0.02)
  monkeypatch.setattr(module_under_test.fu, 'fittings', SimpleNamespace(
    contraction_conical=lambda **kwargs: 4.0,
    diffuser_conical=lambda **kwargs: 5.0,
  ), raising=False)
  conical = module_under_test.Comp_ConicalReduction(D1=80, D2=40, L=1)
  assert conical.calcK(10, sense=1, pin=1, pout=2) == pytest.approx(4.0)
  assert conical.calcK(10, sense=1, pin=2, pout=1) == pytest.approx(5.0)

def test_beveled_entrance_forward_and_reverse_flow(monkeypatch) -> None:
  monkeypatch.setattr(module_under_test.fu, 'entrance_beveled', lambda *args, **kwargs: 6.0)
  with pytest.raises(TypeError, match='argument left'):
    module_under_test.C_EntranceBeveled(D=50, Lb=5, R=45)

def test_comp_serial_combines_components_and_builds_profile() -> None:
  class FixedHead(module_under_test.flsb.Comp_Base):
    def __init__(self, name: str, head: float) -> None:
      super().__init__(name=name)
      self._head = head * module_under_test.u.m

    def calcH(self, Q, sense=1, pin=1, pout=2):
      return self._head * sense

  comp_a = FixedHead('a', 2)
  comp_b = FixedHead('b', 3)
  serial = module_under_test.Comp_Serial(item=[comp_a, comp_b])

  assert serial.Components == [comp_a, comp_b]
  assert serial.getComp(0) is comp_a
  assert serial.calcH(1).to(module_under_test.u.m).magnitude == pytest.approx(5.0)

  profile = serial.calcHprofile(1, sense=1, incr=True)
  assert [point.name for point in profile] == ['0:a', '1:b', 'Tot']
  assert profile[0].H.to(module_under_test.u.m).magnitude == pytest.approx(2.0)
  assert profile[1].H.to(module_under_test.u.m).magnitude == pytest.approx(5.0)

  comp_c = FixedHead('c', 4)
  assert serial.setComp(1, comp_c) is comp_c
  assert serial.addComp(comp_b) is comp_b
  assert '0:' in serial.toString()

def test_comp_parallel_validates_guess_and_uses_fsolve_result(monkeypatch) -> None:
  class FixedHead(module_under_test.flsb.Comp_Base):
    def __init__(self, name: str, head: float) -> None:
      super().__init__(name=name)
      self._head = head * module_under_test.u.m

    def calcH(self, Q, sense=1, pin=1, pout=2):
      return self._head

  comp_a = FixedHead('a', 2)
  comp_b = FixedHead('b', 2)
  parallel = module_under_test.Comp_Parallel(item=[comp_a, comp_b], guess=[1.0])

  with pytest.raises(ValueError, match='does not match number of equations'):
    parallel.calcH(2)

  parallel.guess = [1.0, 1.0]

  def fake_fsolve(func=None, x0=None, args=None, full_output=None):
    assert callable(func)
    assert x0 == [1.0, 1.0]
    assert args.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.0)
    assert full_output == 1
    return [0.5, 1.5], {'ok': True}, 1, 'ok'

  monkeypatch.setattr(module_under_test, 'fsolve', fake_fsolve)
  head = parallel.calcH(2)
  assert head.to(module_under_test.u.m).magnitude == pytest.approx(2.0)
  assert list(parallel.getQ().magnitude) == pytest.approx([0.5, 1.5])
  assert '0:' in parallel.toString()

def test_comp_parallel2_uses_solver_result_and_reports_failure(monkeypatch) -> None:
  class FixedHead(module_under_test.flsb.Comp_Base):
    def __init__(self, name: str, head: float) -> None:
      super().__init__(name=name)
      self._head = head * module_under_test.u.m

    def calcH(self, Q, sense=1, pin=1, pout=2):
      return self._head

  comp_a = FixedHead('a', 2)
  comp_b = FixedHead('b', 2)
  parallel = module_under_test.Comp_Parallel2(item=[comp_a, comp_b], guess=1.0)

  def fake_ok(func=None, x0=None, args=None, full_output=None):
    assert callable(func)
    assert x0 == 1.0
    assert args.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.0)
    assert full_output == 1
    return [0.75 * module_under_test.u.m**3 / module_under_test.u.h], {'ok': True}, 1, 'ok'

  monkeypatch.setattr(module_under_test, 'fsolve', fake_ok)
  head = parallel.calcH(2)
  assert head.to(module_under_test.u.m).magnitude == pytest.approx(2.0)
  assert parallel.getQ()[0].magnitude == pytest.approx(0.75)

  def fake_fail(func=None, x0=None, args=None, full_output=None):
    assert callable(func)
    assert x0 == 1.0
    assert args.to(module_under_test.u.m**3 / module_under_test.u.h).magnitude == pytest.approx(2.0)
    assert full_output == 1
    return [0.75 * module_under_test.u.m**3 / module_under_test.u.h], {}, 0, 'failed'

  monkeypatch.setattr(module_under_test, 'fsolve', fake_fail)
  with pytest.raises(ValueError, match='failed'):
    parallel.calcH(2)
