'''Behavioral unit tests for fluidsolve.medium.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import pytest
import fluidsolve.medium as module_under_test

u = module_under_test.unitRegistry

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Medium'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', [])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

@pytest.mark.parametrize(
  'name',
  ['CTE_E_RVS', 'CTE_G', 'CTE_K', 'CTE_MU', 'CTE_NP', 'CTE_NT', 'CTE_NU', 'CTE_RHO', 'CTE_WATER', 'Quantity', 'u', 'unitRegistry'],
)
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_medium_defaults_are_initialized_from_reference_water() -> None:
  medium = module_under_test.Medium()
  temperature = medium.T
  pressure = medium.p
  density = medium.rho
  viscosity = medium.mu
  conductivity = medium.k
  assert medium.name == 'water'
  assert medium.cprd is not None
  assert getattr(temperature, 'to')(u.degC).magnitude == pytest.approx(20.0, rel=1e-3)
  assert getattr(pressure, 'to')(u.bar).magnitude == pytest.approx((1.0 * u.atm).to(u.bar).magnitude, rel=1e-3)
  assert getattr(density, 'magnitude') > 0.0
  assert getattr(viscosity, 'magnitude') > 0.0
  assert getattr(conductivity, 'magnitude') > 0.0

def test_medium_accepts_custom_conditions_and_name() -> None:
  medium = module_under_test.Medium(name='hot_water', T=50.0 * u.degC, p=2.0 * u.bar)
  temperature = medium.T
  pressure = medium.p

  assert medium.name == 'hot_water'
  assert getattr(temperature, 'to')(u.degC).magnitude == pytest.approx(50.0, rel=1e-3)
  assert getattr(pressure, 'to')(u.bar).magnitude == pytest.approx(2.0, rel=1e-3)

def test_medium_manual_properties_allowed_without_thermo_product() -> None:
  medium = module_under_test.Medium(
    prd='',
    name='manual',
    rho=950.0,
    mu=0.0012,
    k=0.55,
  )
  density = medium.rho
  viscosity = medium.mu
  conductivity = medium.k

  assert medium.cprd is None
  assert medium.name == 'manual'
  assert getattr(density, 'to')(u.kg / u.m**3).magnitude == pytest.approx(950.0)
  assert getattr(viscosity, 'to')(u.Pa * u.s).magnitude == pytest.approx(0.0012)
  assert getattr(conductivity, 'to')(u.W / u.m / u.degK).magnitude == pytest.approx(0.55)

def test_medium_without_product_requires_rho_mu_and_k() -> None:
  with pytest.raises(ValueError, match='Medium must have a valid prd or have a rho, mu and k'):
    module_under_test.Medium(prd='')

def test_medium_property_setters_update_values_and_keep_overrides() -> None:
  medium = module_under_test.Medium()

  medium.rho = 975.0
  medium.mu = 0.00105
  medium.k = 0.62
  medium.T = 60.0 * u.degC
  medium.p = 3.0 * u.bar
  temperature = medium.T
  pressure = medium.p
  density = medium.rho
  viscosity = medium.mu
  conductivity = medium.k

  assert getattr(temperature, 'to')(u.degC).magnitude == pytest.approx(60.0, rel=1e-3)
  assert getattr(pressure, 'to')(u.bar).magnitude == pytest.approx(3.0, rel=1e-3)
  assert getattr(density, 'to')(u.kg / u.m**3).magnitude == pytest.approx(975.0, rel=1e-3)
  assert getattr(viscosity, 'to')(u.Pa * u.s).magnitude == pytest.approx(0.00105, rel=1e-4)
  assert getattr(conductivity, 'to')(u.W / u.m / u.degK).magnitude == pytest.approx(0.62, rel=1e-3)

def test_medium_name_setter_and_text_representations() -> None:
  medium = module_under_test.Medium(name='old_name')
  medium.name = 'new_name'

  text_basic = str(medium)
  text_detail = medium.toString(detail=1)
  rep = repr(medium)

  assert medium.name == 'new_name'
  assert 'Medium new_name:' in text_basic
  assert 'rho:' in text_basic
  assert 'mu:' in text_basic
  assert 'T:' in text_detail
  assert 'p:' in text_detail
  assert 'k:' in text_detail
  assert 'Medium(name="new_name", prd="water"' in rep

def test_medium_repr_for_empty_name_uses_default_signature() -> None:
  medium = module_under_test.Medium(name='')

  assert repr(medium).startswith('Medium(prd="water"')
