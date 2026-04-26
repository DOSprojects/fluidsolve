'''Auto-generated tests for fluidsolve.material.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import pytest
import fluidsolve.material as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['Material'])
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

@pytest.mark.parametrize('name', ['CTE_E_RVS', 'CTE_G', 'CTE_K', 'CTE_NT', 'CTE_RHO', 'Quantity', 'u'])
def test_public_variables_exist(name: str) -> None:
  assert hasattr(module_under_test, name)

def test_material_defaults_and_public_properties() -> None:
  material = module_under_test.Material()
  temperature = material.T

  assert material.name == 'mat'
  assert getattr(temperature, 'to')(module_under_test.u.degC).magnitude == pytest.approx(20.0)
  assert material.rho == module_under_test.CTE_RHO
  assert material.k == module_under_test.CTE_K
  assert material.e == module_under_test.CTE_E_RVS
  assert material.cmat is None

def test_material_init_accepts_custom_values_and_units() -> None:
  material = module_under_test.Material(
    mat='steel',
    name='Steel',
    T=30 * module_under_test.u.degC,
    rho=800.0,
    k=2.0,
    e=5.0,
  )
  temperature = material.T

  assert material.name == 'Steel'
  assert getattr(temperature, 'to')(module_under_test.u.degC).magnitude == pytest.approx(30.0)
  assert material.rho == 800 * module_under_test.u.kg / module_under_test.u.m**3
  assert material.k == 2 * module_under_test.u.W / module_under_test.u.m / module_under_test.u.degK
  assert material.e == 5 * module_under_test.u.um

def test_material_setters_update_stored_values() -> None:
  material = module_under_test.Material()

  material.name = 'custom'
  material.T = 40 * module_under_test.u.degC
  material.rho = 950.0
  material.k = 0.6
  material.e = 4.0
  temperature = material.T

  assert material.name == 'custom'
  assert getattr(temperature, 'to')(module_under_test.u.degC).magnitude == pytest.approx(40.0)
  assert material.rho == 950 * module_under_test.u.kg / module_under_test.u.m**3
  assert material.k == 0.6 * module_under_test.u.W / module_under_test.u.m / module_under_test.u.degK
  assert material.e == 4 * module_under_test.u.um

def test_material_to_string_and_repr_cover_detail_levels() -> None:
  material = module_under_test.Material(name='steel', rho=800.0, k=2.0, e=5.0)

  text_basic = material.toString()
  text_detail = material.toString(1)
  text_formatted = f'{material:1}'
  rep = repr(material)

  assert 'Material steel:' in text_basic
  assert 'rho:800.00' in text_basic
  assert 'kg/m' in text_basic
  assert 'T:' in text_detail
  assert 'k:' in text_detail
  assert text_formatted == text_detail
  assert 'Material(name="steel"' in rep

def test_material_update_product_is_safe_without_library_backend() -> None:
  material = module_under_test.Material(mat='steel', rho=700.0, k=3.0, e=7.0)

  material._updateProduct()  # pylint: disable=protected-access

  assert material.cmat is None
  assert material.rho == 700 * module_under_test.u.kg / module_under_test.u.m**3
  assert material.k == 3 * module_under_test.u.W / module_under_test.u.m / module_under_test.u.degK
  assert material.e == 7 * module_under_test.u.um
