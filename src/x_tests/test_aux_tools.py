'''Behavioral unit tests for fluidsolve.aux_tools.'''

# PYLINT DIRECTIVES
# pylint: disable=invalid-name,missing-function-docstring

import inspect
import pytest
import fluidsolve.aux_tools as module_under_test

def test_module_importable() -> None:
  assert module_under_test is not None

@pytest.mark.parametrize('name', ['GetArgs', 'vFun'])
def test_public_classes_exist(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert inspect.isclass(obj)

@pytest.mark.parametrize('name', ['getPumpCurveDataText', 'prepareArgs', 'spec', 'toUnits'])
def test_public_functions_are_callable(name: str) -> None:
  obj = getattr(module_under_test, name)
  assert callable(obj)

def test_toUnits_scalar_to_quantity() -> None:
  q = module_under_test.toUnits(2, module_under_test.u.m)
  assert q.magnitude == 2
  assert q.units == module_under_test.u.m

def test_toUnits_quantity_conversion_and_magnitude() -> None:
  value = 250 * module_under_test.u.cm
  out = module_under_test.toUnits(value, module_under_test.u.m, magnitude=True)
  assert out == 2.5

def test_toUnits_none_value_raises() -> None:
  with pytest.raises(ValueError, match='Value is None'):
    module_under_test.toUnits(None, module_under_test.u.m)  # type: ignore[arg-type]

def test_toUnits_returns_value_unchanged_when_units_none() -> None:
  value = 5
  assert module_under_test.toUnits(value, None) == value  # type: ignore[arg-type]

def test_prepareArgs_filters_none_values() -> None:
  args = module_under_test.prepareArgs(a=1, b=None, c='x')
  assert args == {'a': 1, 'c': 'x'}

def test_getPumpCurveDataText_parses_whitespace_and_commas() -> None:
  data = '''
    1, 2
    3 4
  '''
  assert module_under_test.getPumpCurveDataText(data) == [1.0, 2.0, 3.0, 4.0]

def test_getPumpCurveDataText_empty_string_returns_empty_list() -> None:
  assert module_under_test.getPumpCurveDataText('') == []

def test_spec_returns_input_kwargs_as_dict() -> None:
  out = module_under_test.spec(comp='Tube', nodes=['A', 'B'], sense=-1, D=50)
  assert out == {'comp': 'Tube', 'nodes': ['A', 'B'], 'sense': -1, 'D': 50}

def test_getargs_with_validators_and_remove() -> None:
  args = module_under_test.GetArgs({'name': '  abc  '})
  result = args.getArg('name', [module_under_test.vFun.stripspaces(), module_under_test.vFun.toupper()])
  assert result == 'ABC'
  assert args.restArgs() == {}

def test_getargs_init_rejects_non_dict() -> None:
  with pytest.raises(TypeError, match='is not a dict'):
    module_under_test.GetArgs([('name', 'abc')])  # type: ignore[arg-type]

def test_getargs_getarg_keeps_value_when_remove_false() -> None:
  args = module_under_test.GetArgs({'name': 'abc'})
  result = args.getArg('name', remove=False)
  assert result == 'abc'
  assert args.restArgs() == {'name': 'abc'}

def test_getargs_invalid_name_type_raises() -> None:
  args = module_under_test.GetArgs({'name': 'abc'})
  with pytest.raises(TypeError, match='name argument 1 is not a str'):
    args.getArg(1)  # type: ignore[arg-type]

def test_getargs_invalid_validators_type_raises() -> None:
  args = module_under_test.GetArgs({'name': 'abc'})
  with pytest.raises(TypeError, match='validators argument .* is not a list'):
    args.getArg('name', module_under_test.vFun.stripspaces())  # type: ignore[arg-type]

def test_getargs_non_function_validator_raises() -> None:
  args = module_under_test.GetArgs({'name': 'abc'})
  with pytest.raises(TypeError, match='is not a function'):
    args.getArg('name', ['not-a-function'])  # type: ignore[list-item]

def test_getargs_addarg_and_addargs_preserve_existing_values() -> None:
  args = module_under_test.GetArgs({'a': 1})
  args.addArg('b', 2)
  args.addArgs({'b': 99, 'c': 3})
  assert args.restArgs() == {'a': 1, 'b': 2, 'c': 3}

def test_getargs_isempty_behaviour_matches_current_contract() -> None:
  empty_args = module_under_test.GetArgs({})
  assert empty_args.isEmpty() is False

  remaining_args = module_under_test.GetArgs({'left': 1})
  assert remaining_args.isEmpty(raiseerror=False) is True
  with pytest.raises(TypeError, match='argument left'):
    remaining_args.isEmpty()

def test_getargs_default_when_missing() -> None:
  args = module_under_test.GetArgs({})
  result = args.getArg('speed', [module_under_test.vFun.default(2900)])
  assert result == 2900

def test_getargs_missing_without_default_raises() -> None:
  args = module_under_test.GetArgs({})
  with pytest.raises(ValueError, match='Name speed not found'):
    args.getArg('speed', [module_under_test.vFun.istype(int)])

def test_vfun_istype_rejects_wrong_type() -> None:
  validator = module_under_test.vFun.istype(int)
  with pytest.raises(ValueError, match='not of type'):
    validator('n', '3')

def test_vfun_totype_casts_and_respects_optional_none() -> None:
  validator = module_under_test.vFun.totype(int)
  assert validator('n', '3') == 3
  optional_validator = module_under_test.vFun.totype(int, need=False)
  assert optional_validator('n', None) is None

def test_vfun_case_converters_and_stripspaces_allow_optional_none() -> None:
  assert module_under_test.vFun.stripspaces()('name', '  a b  ') == 'a b'
  assert module_under_test.vFun.tolower()('name', 'AbC') == 'abc'
  assert module_under_test.vFun.toupper(need=False)('name', None) is None

def test_vfun_tounits_converts_and_handles_none_modes() -> None:
  validator = module_under_test.vFun.tounits(module_under_test.u.cm, magnitude=True)
  assert validator('length', 2) == 2
  with pytest.raises(ValueError, match='Argument is None'):
    module_under_test.vFun.tounits(module_under_test.u.cm)('length', None)
  assert module_under_test.vFun.tounits(module_under_test.u.cm, need=False)('length', None) is None

def test_vfun_sanitizefilepath_and_tolambda_transform() -> None:
  validator = module_under_test.vFun.sanitizefilepath()
  assert validator('path', 'a/../b\\file.txt') == module_under_test.os.path.normpath('a/../b\\file.txt')
  lambda_validator = module_under_test.vFun.tolambda(lambda value: value * 2)
  assert lambda_validator('n', 4) == 8
  assert module_under_test.vFun.tolambda(lambda value: value, need=False)('n', None) is None

def test_vfun_istype_accepts_tuple_and_custom_message() -> None:
  validator = module_under_test.vFun.istype((int, float))
  assert validator('n', 3.5) == 3.5
  with pytest.raises(ValueError, match='bad type'):
    module_under_test.vFun.istype(int, errmsg='bad type')('n', '3')

def test_vfun_notnone_and_notempty_raise_custom_messages() -> None:
  with pytest.raises(ValueError, match='required'):
    module_under_test.vFun.notnone(errmsg='required')('name', None)
  with pytest.raises(ValueError, match='empty'):
    module_under_test.vFun.notempty(errmsg='empty')('name', '')

def test_vfun_length_validators_cover_success_and_failure() -> None:
  assert module_under_test.vFun.haslen(3)('name', 'abc') == 'abc'
  with pytest.raises(ValueError, match='length 2 not equal to 3'):
    module_under_test.vFun.haslen(3)('name', 'ab')

  assert module_under_test.vFun.lenmax(3)('name', 'abc') == 'abc'
  with pytest.raises(ValueError, match='more than max 3'):
    module_under_test.vFun.lenmax(3)('name', 'abcd')

  assert module_under_test.vFun.lenmin(2)('name', 'abc') == 'abc'
  with pytest.raises(ValueError, match='less than min 2'):
    module_under_test.vFun.lenmin(2)('name', 'a')
  assert module_under_test.vFun.lenmin(2, need=False)('name', None) is None

def test_vfun_inrange_current_behaviour_and_optional_none() -> None:
  validator = module_under_test.vFun.inrange(1, 5)
  assert validator('n', 3) == 3
  with pytest.raises(ValueError, match='must be between 1 to 5'):
    validator('n', 7)
  assert module_under_test.vFun.inrange(1, 5, need=False)('n', None) is None

def test_vfun_inlist_allows_and_rejects() -> None:
  validator = module_under_test.vFun.inlist('a', 'b', 'c')
  assert validator('k', 'b') == 'b'
  with pytest.raises(ValueError, match='must be one of'):
    validator('k', 'z')

def test_vfun_inlist_supports_tuple_input_and_inverse() -> None:
  validator = module_under_test.vFun.inlist(('a', 'b'))
  assert validator('k', 'a') == 'a'
  inverse_validator = module_under_test.vFun.inlist('x', 'y', inv=True)
  assert inverse_validator('k', 'z') == 'z'
  with pytest.raises(ValueError, match='may not be one of x,y'):
    inverse_validator('k', 'x')

def test_vfun_regex_inv_true_requires_match() -> None:
  validator = module_under_test.vFun.regex(r'^[A-Z]+$', inv=True)
  assert validator('code', 'ABC') == 'ABC'
  with pytest.raises(ValueError, match='must conform to regex'):
    validator('code', 'Abc')

def test_vfun_regex_default_mode_rejects_matching_values_and_invalid_pattern() -> None:
  validator = module_under_test.vFun.regex(r'^[A-Z]+$')
  assert validator('code', 'Abc') == 'Abc'
  with pytest.raises(ValueError, match='may not conform to regex'):
    validator('code', 'ABC')
  with pytest.raises(ValueError, match='is not a valid regex'):
    module_under_test.vFun.regex('[')

def test_vfun_fileexists(tmp_path) -> None:
  file_path = tmp_path / 'x.txt'
  file_path.write_text('ok', encoding='utf-8')
  validator = module_under_test.vFun.fileexists()
  assert validator('file', str(file_path)) == str(file_path)
  with pytest.raises(ValueError, match='does not exist'):
    validator('file', str(file_path.with_name('missing.txt')))

def test_vfun_file_access_validators_support_optional_none_and_existing_files(tmp_path) -> None:
  file_path = tmp_path / 'x.txt'
  file_path.write_text('ok', encoding='utf-8')

  assert module_under_test.vFun.fileexists(need=False)('file', None) is None
  assert module_under_test.vFun.isfilereadable()('file', str(file_path)) == str(file_path)
  assert module_under_test.vFun.isfilewritable()('file', str(file_path)) == str(file_path)
  assert module_under_test.vFun.isfileexecutable(need=False)('file', None) is None

def test_vfun_file_access_validators_raise_for_missing_files(tmp_path) -> None:
  missing = str(tmp_path / 'missing.txt')
  with pytest.raises(ValueError, match='missing'):
    module_under_test.vFun.isfilereadable(errmsg='missing')('file', missing)
  with pytest.raises(ValueError, match='missing'):
    module_under_test.vFun.isfilewritable(errmsg='missing')('file', missing)
  with pytest.raises(ValueError, match='missing'):
    module_under_test.vFun.isfileexecutable(errmsg='missing')('file', missing)
