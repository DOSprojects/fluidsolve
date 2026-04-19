'''
Utility helpers for argument handling, unit conversion, and validators.

This module provides small building blocks used throughout fluidsolve for
consistent argument parsing and validation.

Main parts:

* Unit helpers:
  ``toUnits`` converts numeric values and quantities to a requested unit.
* Argument helpers:
  ``prepareArgs`` removes ``None`` values from keyword dictionaries and
  ``spec`` builds readable component specification dictionaries.
* Argument processor:
  ``GetArgs`` provides structured extraction/consumption of keyword
  arguments with validation chains.
* Validator factory:
  ``vFun`` contains static methods that return validator/transformer
  callables for ``GetArgs.getArg``.

Typical usage pattern:

1. Wrap incoming kwargs with ``GetArgs``.
2. Retrieve each expected argument through ``getArg`` and a list of
   validators (defaults, type checks, conversions).
3. Call ``isEmpty`` to ensure no unexpected arguments are left.

Example::

  args = GetArgs(kwargs)
  name = args.getArg('name', [vFun.default(''), vFun.istype(str)])
  roughness = args.getArg('e', [vFun.default(15), vFun.tounits(u.um)])
  args.isEmpty()
    
This approach keeps component constructors compact, explicit, and uniform.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

# =============================================================================
# IMPORTS
# =============================================================================
from typing   import Any, Callable
import types
import os
import re
import textwrap
# Import directly from pint (not via medium) to avoid circular imports.
from pint     import _DEFAULT_REGISTRY as u
from pint     import Quantity

# =============================================================================
# SOME HELPER FUNCTIONS
# =============================================================================
def toUnits(value: int | float | Quantity, units: Quantity, magnitude: bool=False) -> Quantity:
  ''' Convert a value to a Quantity in the requested units.

  Args:
    value (int | float | Quantity): The input value.
    units (Quantity): The Quantity units to convert to.
    magnitude (bool, optional): If True, only the magnitude is returned.

  Returns:
    Quantity: Value converted to the requested units.
  '''
  if value is None:
    raise ValueError('Value is None.')
  if units is None:
    return value
  if not isinstance(value , Quantity):
    return value * units
  value = value.to(units)
  if magnitude:
    return value.magnitude
  return value

def prepareArgs(**kwargs: int) -> dict:
  ''' Build an argument dict from kwargs, skipping None values.
      This lets downstream functions use their own defaults when an argument was not provided.

  Returns:
    dict: Filtered argument dictionary.
  '''
  args = {}
  for key, value in kwargs.items():
    if value is not None:
      args[key] = value
  return args

def getPumpCurveDataText(data_in: str) -> list:
  ''' Parse Q-H data copied from a pump curve digitizer.
      Use eg. https://plotdigitizer.com/app
      or https://web.eecs.utk.edu/~dcostine/personal/PowerDeviceLib/DigiTest/index.html
      or similar

  Args:
    data_in (str): The input data from the pump curve.

  Returns:
    list: Parsed numeric values.
  '''
  data = textwrap.dedent(data_in)
  if len(data) > 0 :
    hdata = data.replace('\n', ' ').replace('\r', '').replace(',', '')
    return [float(x) for x in hdata.split()]
  else:
    return []

# =============================================================================
# HELPER FUNCTION FOR DEFS
# =============================================================================
def spec(**kwargs: Any) -> Any:
  ''' Helper to define a component specification entry.

  Example:
    spec(comp='Tube', nodes=['A', 'B'], sense=-1, D=50)
  '''
  return kwargs

# =============================================================================
# KWARGS VALIDATION - PROCESSING
# =============================================================================
class GetArgs ():
  ''' Process and validate an argument dictionary.

  Args:
    args_in (dict, optional): Input key-value pairs.

  Raises:
    TypeError: Raised when args_in is not a dict.

  Returns:
    None
  '''

  def __init__(self, args_in: dict | None=None) -> None:
    if args_in is None:
      args_in = {}
    if not isinstance(args_in, dict):
      raise TypeError(f'Error: The arguments input {args_in} is not a dict')
    self._args = args_in

  def getArg (self, name: str, validators: list=[], remove: Any=True) -> Any:
    ''' Get an argument value based on the key from an argument dict or kwargs dict.
        A list of validator functions (see class vFun) can be added to validate or to modify the passed argument.
        Then this item is removed from the list of arguments (thus making it possible to check if every argument is used just once).

    Args:
      name (str): Key of the argument in the internal argument dict.
      validators (list, optional): The list with validator functions.
      remove (bool, optional): Remove the argument after processing.

    Raises:
      TypeError: Name has to be a string
      TypeError: Validators has to be a list
      ValueError: Name is not found in the input arguments
      TypeError: A validator is not a function

    Returns:
      Any: Validated or transformed argument value.
    '''
    #print('---------- validator')
    #print('args_in:', self._args)
    #print('name:', name)
    #print('validators:', validators)
    # check syntax
    if not isinstance(name, str):
      raise TypeError(f'Error: The name argument {name} is not a str')
    if not isinstance(validators, list):
      raise TypeError(f'Error: The validators argument {validators} is not a list')
    # execute validation
    if name not in self._args:
      if any(getattr(validator, '__name__', '') == '_default' for validator in validators):
        self._args[name] = None
      else:
        raise ValueError(f'Error: Name {name} not found in arguments {self._args}')
    value_in = self._args[name]
    for validator in validators:
      if not isinstance(validator, types.FunctionType):
        raise TypeError(f'Error: pattern {validator} is not a function')
      value_in = validator(name, value_in)
      #print(value_in)
    # remove from self._args
    if remove:
      del self._args[name]
      #print('delete', name, self._args)
    # result
    #print('result:', value_in)
    return value_in

  def addArg (self, key: str, value: Any) -> None:
    ''' Add one argument to the internal dictionary.
        Overwrites the value if the key already exists.

    Args:
      key (str): Key of the argument to add.
      value (Any): Value of the argument to add.

    Returns:
      None
    '''
    self._args[key] = value

  def addArgs (self, extra_args: dict={}) -> None:
    ''' Add extra (default) arguments to the existing dict if not already there.
        Can be used to set some default values.

    Args:
      extra_args (dict, optional): Default key-value pairs.

    Returns:
      None
    '''
    for key, value in extra_args.items():
      if key not in self._args:
        self._args[key] = value

  def restArgs (self) -> dict:
    ''' Return the remaining, unprocessed arguments.

    Returns:
        dict: Remaining arguments.
    '''
    return self._args

  def isEmpty (self, raiseerror: bool=True) -> bool:
    ''' Check whether all arguments have been processed.
        Raises or reports that arguments are still left.

    Args:
      raiseerror (bool, optional): Raise an error when arguments remain.

    Raises:
      TypeError: Raised when arguments are left and raiseerror is True.

    Returns:
      bool: True when empty, False when arguments remain.

    '''
    if not len(self._args) == 0:
      if raiseerror:
        raise TypeError(f'Error: argument left: {self._args}')
      return True
    else:
      return False

class vFun (): # pylint: disable=invalid-name
  ''' Static validator helpers for use with GetArgs.
      Includes sanitizers, converters, and validation checks.

      Every static method returns a function (Callable) with 2 arguments:
      The first one is the name for the argument (used for eventual error generation).
      The second one is the argument to be validated itself.
      Validators always return the (possibly modified) argument.

  '''
  # - - - - - - - - - - - - - - - - - - - -
  # Sanitizers - Modifiers
  @staticmethod
  def default(default: Any) -> Callable[..., Any]:
    ''' Give a default value for the argument.

    Args:
      default (Any): The default value.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _default(_argname: Any, argvalue: Any) -> Any:
      if argvalue is None:
        return default
      else:
        return argvalue
    return _default

  @staticmethod
  def totype(type_type: Any, need: bool=True) -> Callable[..., Any]:
    ''' Cast the argument to the desired type.

    Args:
      type_type (Any): The type to be cast to.
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _totype(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not isinstance(argvalue, type_type):
        argvalue = type_type(argvalue)
      return argvalue
    return _totype

  @staticmethod
  def stripspaces(need: bool=True) -> Callable[..., str]:
    ''' Strip the leading and trailing spaces from the argument.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., str]: The validator function.
    '''
    def _strip(_argname: Any, argvalue: Any) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).strip()
    return _strip

  @staticmethod
  def tolower(need: bool=True) -> Callable[..., str]:
    ''' Set the argument to lower case.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., str]: The validator function.
    '''
    def _tolower(_argname: Any, argvalue: Any) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).lower()
    return _tolower

  @staticmethod
  def toupper(need: bool=True) -> Callable[..., str]:
    ''' Set the argument to upper case.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., str]: The validator function.
    '''
    def _toupper(_argname: Any, argvalue: Any) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).upper()
    return _toupper

  @staticmethod
  def tounits(units: Any, magnitude: bool=False, need: bool=True) -> Callable[..., Any | Quantity]:
    ''' Convert the argument to a Quantity with desired units.
        Optionally, only the magnitude is returned.

    Args:
      units (Any): The desired units.
      magnitude (bool, optional): If True, return only the magnitude.
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any | Quantity]: The validator function.
    '''
    def _tounits(_argname: Any, argvalue: Any) -> Any | Quantity:
      if not need and argvalue is None:
        return None
      if argvalue is None:
        raise ValueError('Error: Argument is None')
      if not isinstance(argvalue , Quantity):
        argvalue = argvalue * units
      else:
        argvalue = argvalue.to(units)
      if magnitude:
        return argvalue.magnitude
      return argvalue
    return _tounits

  @staticmethod
  def sanitizefilepath(need: bool=True) -> Callable[..., Any]:
    ''' Sanitize the argument as a filepath.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _sanitizefilepath(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      return os.path.normpath(argvalue)
    return _sanitizefilepath

  @staticmethod
  def tolambda(fun: Any, need: bool=True) -> Callable[..., Any]:
    ''' Execute a transformation function.
        Eg. vFun.tolambda(lambda x: x.to(u.m) if isinstance(x, Quantity) else x * u.m)
            vFun.tolambda(lambda x: x if isinstance(x, flsm.Medium) else flsm.Medium(prd=x))

    Args:
      fun (Any): The callable transformation.
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _lambda(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      return fun(argvalue)
    return _lambda

  # - - - - - - - - - - - - - - - - - - - -
  # Validators
  @staticmethod
  def istype(*type_type: Any, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check whether the argument matches one or more allowed types.

    Args:
      type_type (list | tuple | Any): Allowed type(s).
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    if len(type_type) == 1 and isinstance(type_type[0], (list, tuple)):
      t_type = type_type[0]
    else:
      t_type = type_type

    def _istype(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not isinstance(argvalue, t_type):
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} not of type {t_type}')
      return argvalue
    return _istype

  @staticmethod
  def notnone(errmsg: str=None) -> Callable[..., Any]:
    ''' Check that the argument is not None.

    Args:
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _notempty(argname: Any, argvalue: Any) -> Any:
      if argvalue is None:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} may not be None')
      return argvalue
    return _notempty

  @staticmethod
  def notempty(errmsg: str=None) -> Callable[..., Any]:
    ''' Check that the argument is not empty.

    Args:
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _notempty(argname: Any, argvalue: Any) -> Any:
      if len(argvalue) == 0:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} may not be empty')
      return argvalue
    return _notempty

  @staticmethod
  def haslen(length: int, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check that the argument length equals the expected length.

    Args:
      length (int): Desired length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
       Callable[..., Any]: The validator function.
    '''
    def _haslen(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if len(argvalue) != length:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} has length {len(argvalue)} not equal to {length}.')
      return argvalue
    return _haslen

  @staticmethod
  def lenmax(max_length: int, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check that the argument length does not exceed a maximum.

    Args:
      max_length (int): Max length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
       Callable[..., Any]: The validator function.
    '''
    def _lenmax(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if len(argvalue) > max_length:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} has length {len(argvalue)}; more than max {max_length}.')
      return argvalue
    return _lenmax

  @staticmethod
  def lenmin(min_length: int, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check that the argument length is at least a minimum.

    Args:
      min_length (int): Min length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _lenmin(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if len(argvalue) < min_length:
        if errmsg is not None:
          raise ValueError( errmsg )
        raise ValueError(f'Error: argument {argname} has length {len(argvalue)}; less than min {min_length}.')
      return argvalue
    return _lenmin

  @staticmethod
  def inrange(low: int | float, high: int | float, inv: bool=False, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a value is inside or outside a range.

    Args:
      low (int | float): Min value
      high (int | float): Max value
      inv (bool, optional): If True value must be in range, if False it must be out of the range.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., None]: The validator function.
    '''
    def _inrange(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not inv:
        if int(argvalue) < low or int(argvalue) > high:
          if errmsg is not None:
            raise ValueError( errmsg )
          raise ValueError( f'Error: argument {argname} must be between {low} to {high}' )
      else:
        if int(argvalue) < low or int(argvalue) > high:
          if errmsg is not None:
            raise ValueError( errmsg )
          raise ValueError( f'Error: argument {argname} must be outside {low} to {high}' )
      return argvalue
    return _inrange

  @staticmethod
  def inlist(*items: Any, inv: bool=False, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check whether a value is contained in a list (or excluded if inv=True).
        This function accepts either a single list or tuple, or multiple individual arguments.
        If the condition fails and `errmsg` is provided, a ValueError is raised.

    Args:
      items (list | tuple | Any): Allowed (or disallowed) values.
      inv (bool, optional): False to allow listed values, True to forbid them.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.

    Examples:
        >>> inlist(1, 2, 3)
        True

        >>> inlist([1, 2, 3])
        True

        >>> inlist(0, 0, inv=True)
        True

        >>> inlist(0, errmsg="Invalid input")
        Traceback (most recent call last):
            ...
        ValueError: Invalid input

    '''
    # Flatten args if a single list or tuple is passed
    if len(items) == 1 and isinstance(items[0], (list, tuple)):
      lst = items[0]
    else:
      lst = items
    string_list_error = ','.join(lst)

    def _inlist(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not inv:
        if argvalue not in lst:
          if errmsg is not None:
            raise ValueError( errmsg )
          raise ValueError( f'Error: argument {argname} must be one of {string_list_error}' )
      else:
        if argvalue in lst:
          if errmsg is not None:
            raise ValueError( errmsg )
          raise ValueError( f'Error: argument {argname} may not be one of {string_list_error}' )
      return argvalue
    return _inlist


  @staticmethod
  def regex(expr: str, inv: bool=False, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check whether the argument matches a regex rule.

    Args:
      expr (str): The regex expression.
      inv (bool, optional): If True, the regex must apply, if False: the regex may not apply.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.

    Example:
      vFun.regex(r"^[0-9a-zA-Z]*$")

    '''
    try:
      regex_compiled = re.compile( expr )
    except re.error as re_error:
      raise ValueError(f'Error: validator {expr} is not a valid regex: ' + str(re_error)) # pylint: disable=raise-missing-from

    def _regex(argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if inv:
        if regex_compiled.match(str(argvalue)) is None:
          if errmsg is not None:
            raise ValueError(errmsg)
          raise ValueError(f'Error: argument {argname} must conform to regex {expr}')
      else:
        if regex_compiled.match(str(argvalue)) is not None:
          if errmsg is not None:
            raise ValueError(errmsg)
          raise ValueError(f'Error: argument {argname} may not conform to regex {expr}')
      return argvalue
    return _regex

  @staticmethod
  def fileexists(need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a file exists.

    Args:
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not os.path.exists(argvalue):
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: file {argvalue} does not exist.')
      return argvalue
    return validate

  @staticmethod
  def isfilereadable(need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a file is readable.

    Args:
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not os.path.exists(str(argvalue)):
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: file {argvalue} does not exist.')
      if not os.access(str(argvalue), os.R_OK):
        raise ValueError(f'Error: file {argvalue} is not readable.')
      return argvalue
    return validate

  @staticmethod
  def isfilewritable(need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a file is writable.

    Args:
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not os.path.exists(str(argvalue)):
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: file {argvalue} does not exist.')
      if not os.access(str(argvalue), os.W_OK):
        raise ValueError(f'Error: file {argvalue} is not writable.')
      return argvalue
    return validate

  @staticmethod
  def isfileexecutable(need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a file is executable.

    Args:
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname: Any, argvalue: Any) -> Any:
      if not need and argvalue is None:
        return None
      if not os.path.exists(str(argvalue)):
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: file {argvalue} does not exist.')
      if not os.access(str(argvalue), os.X_OK):
        raise ValueError(f'Error: file {argvalue} is not executable.')
      return argvalue
    return validate
