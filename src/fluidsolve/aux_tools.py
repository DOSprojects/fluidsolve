'''
https://github.com/MoserMichael/kwchecker/tree/master

'''
# =============================================================================
# IMPORTS
# =============================================================================
from typing   import Any, Callable
import types
import os
import re
import textwrap
# direct imports from pint and not from the medium module to avoid circular refs
from pint     import _DEFAULT_REGISTRY as u
from pint     import Quantity

# =============================================================================
# SOME HELPER FUNCTIONS
# =============================================================================
def toUnits(value: int | float | Quantity, units: Quantity, magnitude: bool=False) -> Quantity:
  ''' Convert a value or Quantitiy to a Quantity in specific units.

  Args:
    value (int | float | Quantity): The input value.
    units (Quantity): The Quantity units to convert to.
    magnitude (bool, optional): If True, only the magnitude is returned. Defaults to False.

  Returns:
    Quantity: The Quantity in thr asked units.
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
  ''' Prepare a dict with key-value pairs from the entered kwargs.
      If the value is None, then the key-value pair is omitted.
      This enables the function or method where this arguments are passed to,
      to take a default value when no argument wat provided.

  Returns:
      dict: the argument dict.
  '''
  args = {}
  for key, value in kwargs.items():
    if value is not None:
      args[key] = value
  return args

def getPumpCurveDataText(data_in: str) -> list:
  ''' Get Q-H data from a pump curve.
      Use eg. https://plotdigitizer.com/app
      or https://web.eecs.utk.edu/~dcostine/personal/PowerDeviceLib/DigiTest/index.html
      or similar

  Args:
    data_in (str): The input data from the pump curve.

  Returns:
    list: List of floats.
  '''
  data = textwrap.dedent(data_in)
  if len(data) > 0 :
    hdata = data.replace('\n', ' ').replace('\r', '').replace(',', '')
    return [float(x) for x in hdata.split()]
  else:
    return []

# =============================================================================
# KWARGS VALIDATION - PROCESSING
# =============================================================================
class GetArgs ():
  ''' Class to process a dict with arguments

  Args:
    args_in (dict, optional): The dict with arguments as key-value pairs.

  Raises:
    TypeError: If args_in is not a dict.

  Returns:
    None.
  '''

  def __init__(self, args_in: dict={}) -> None:
    if not isinstance(args_in, dict):
      raise TypeError(f'Error: The arguments input {args_in} is not a dict')
    self._args = args_in

  def getArg (self, name: str, validators: list=[], remove=True) -> Any:
    ''' Get an argument value based on the key from an argument dict or kwargs dict.
        A list of validator functions (see class vFun) can be added to validate or to modify the passed argument.
        Then this item is removed from the list of arguments (thus making it possible to check if every argument is used just once).

    Args:
      name (str): The key of the argument in the argument list
      validators (list, optional): The list with validator functions. Defaults to [].
      remove (bool, optional): Has the argument to be remover from the list or not. Defaults to True.

    Raises:
      TypeError: Name has to be a string
      TypeError: Validators has to be a list
      ValueError: Name has not been found as key in the input arguments
      TypeError: A validator is not a function

    Returns:
      Any: The validated or processed argument
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
    ''' Add extra arguments to the existing dict.
        Overwrite if already there.

    Args:
      key (str): the key of the argumetn to add.
      value (value): the value of the argumetn to add.

    Returns:
      None
    '''
    self._args[key] = value

  def addArgs (self, extra_args: dict={}) -> None:
    ''' Add extra (default) arguments to the existing dict if not already there.
        Can be used to set some default values.

    Args:
      extra_args (dict, optional): the dict with default argument key - value pairs. Defaults to {}.

    Returns:
      None
    '''
    for key, value in extra_args.items():
      if key not in self._args:
        self._args[key] = value

  def restArgs (self) -> dict:
    ''' return a dict with the arguments still in the dict (not deleted by getArg).

    Returns:
        dict: The rest of the arguments (to be processed).
    '''
    return self._args

  def isEmpty (self, raiseerror: bool=True) -> bool:
    ''' Returns False or raises an error if the argument list is not empty.
        Can be used to check if all arguments are processed.
        Probably not needed, but this can detect some errors if there are typos in the passed arguments.

    Args:
      raiseerror (bool, optional): Raise an error or not.

    Raises:
      TypeError: Still some arguments left.

    Returns:
      bool: Still some arguments left (False) or not (True).

    '''
    if not len(self._args) == 0:
      if raiseerror:
        raise TypeError(f'Error: argument left: {self._args}')
      return True
    else:
      return False

class vFun (): # pylint: disable=invalid-name
  ''' Class with static methods to be used as validators in the GetArgs class above.
      There are sanitizers, modifiers and validation checks.

      Every static method returns a function (Callable) with 2 arguments:
      The first one is the name for the argument (used for eventual error generation).
      The second one is the argument to be validated itself.
      The validators themselves alwaus have to return the (modified) argument.

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
    def _default(_argname, argvalue) -> Any:
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
    def _totype(_argname, argvalue) -> Any:
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
    def _strip(_argname, argvalue) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).strip()
    return _strip

  @staticmethod
  def tolower(need: bool=True) -> Callable[..., str]:
    ''' Set the argumetn to lower case.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., str]: The validator function.
    '''
    def _tolower(_argname, argvalue) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).lower()
    return _tolower

  @staticmethod
  def toupper(need: bool=True) -> Callable[..., str]:
    ''' set the argument to upper case.

    Args:
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., str]: The validator function.
    '''
    def _toupper(_argname, argvalue) -> str:
      if not need and argvalue is None:
        return None
      return str(argvalue).upper()
    return _toupper

  @staticmethod
  def tounits(units: Any, magnitude: bool=False, need: bool=True) -> Callable[..., Any | Quantity]:
    '''  Set the argument value or Quantity to a Quantity with the desired units.
         As an option, onlu the magnitede is returned

    Args:
      units (Any): The desired units.
      magnitude (bool, optional): if True, the values is converted or interpreted with the desired units, and then only the magnitude is returned
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any | Quantity]: The validator function.
    '''
    def _tounits(_argname, argvalue) -> Any | Quantity:
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
    def _sanitizefilepath(_argname, argvalue) -> Any:
      if not need and argvalue is None:
        return None
      return os.path.normpath(argvalue)
    return _sanitizefilepath

  @staticmethod
  def tolambda(fun: Any, need: bool=True) -> Callable[..., Any]:
    ''' Execute a lambda function.
        Eg. vFun.tolambda(lambda x: x.to(u.m) if isinstance(x, Quantity) else x * u.m)
            vFun.tolambda(lambda x: x if isinstance(x, flsm.Medium) else flsm.Medium(prd=x))

    Args:
      fun (Any): The lamba function to be executed.
      need (bool, optional): if False, this argument can also be None

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _lambda(_argname, argvalue) -> Any:
      if not need and argvalue is None:
        return None
      return fun(argvalue)
    return _lambda

  # - - - - - - - - - - - - - - - - - - - -
  # Validators
  @staticmethod
  def istype(*type_type, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if the argument is of a type or list or tuple of types.

    Args:
      type_type (list | tuple | Any): The type or list of types allowed.
      need (bool, optional): if False, this argument can also be None
      errmsg (Str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    if len(type_type) == 1 and isinstance(type_type[0], (list, tuple)):
      t_type = type_type[0]
    else:
      t_type = type_type

    def _istype(argname, argvalue) -> Any:
      if not need and argvalue is None:
        return None
      if not isinstance(argvalue, t_type):
        print(type(argvalue))
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} not of type {t_type}')
      return argvalue
    return _istype

  @staticmethod
  def notnone(errmsg: str=None) -> Callable[..., Any]:
    ''' Check if the argument is not None.

    Args:
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _notempty(argname, argvalue) -> Any:
      if argvalue is None:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} may not be None')
      return argvalue
    return _notempty

  @staticmethod
  def notempty(errmsg: str=None) -> Callable[..., Any]:
    ''' Check if the argument is not Empty / False / ...

    Args:
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _notempty(argname, argvalue) -> Any:
      if len(argvalue) == 0:
        if errmsg is not None:
          raise ValueError(errmsg)
        raise ValueError(f'Error: argument {argname} may not be empty')
      return argvalue
    return _notempty

  @staticmethod
  def haslen(length: int, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    '''  Check if the length of the argument is equal to.

    Args:
      length (int): Desired length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
       Callable[..., Any]: The validator function.
    '''
    def _haslen(argname, argvalue) -> Any:
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
    '''  Check if the length of the argument is below a max.

    Args:
      max_length (int): Max length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
       Callable[..., Any]: The validator function.
    '''
    def _lenmax(argname, argvalue) -> Any:
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
    '''  Check if the length of the argument is above a min.

    Args:
      min_length (int): Min length.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def _lenmin(argname, argvalue) -> Any:
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
      inv (bool, optional): If True value must be in range, if False it must be out of the range. Defaults to False.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., None]: The validator function.
    '''
    def _inrange(argname, argvalue) -> Any:
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
  def inlist(*items, inv: bool=False, need: bool=True, errmsg: str=None) -> Callable[..., Any]:
    ''' Check if a value is contained in a list or not (if inv=True).
        This function accepts either a single list or tuple, or multiple individual arguments.
        If the condition fails and `errmsg` is provided, a ValueError is raised.

    Args:
      items (list | tuple | Any): The list with alowed (or disalowed values).
      inv (bool, optional):  False if the list contains the alowed values, True if it contains the disalowed values. Defaults to False.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

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

    def _inlist(argname, argvalue) -> Any:
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
    ''' Check if the argument matches a regex or not.

    Args:
      expr (str): The regex expression.
      inv (bool, optional): If True, the regex must apply, if False: the regex may not apply. Defaults to False.
      need (bool, optional): if False, this argument can also be None
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.

    Example:
      vFun.regex(r"^[0-9a-zA-Z]*$")

    '''
    try:
      regex_compiled = re.compile( expr )
    except re.error as re_error:
      raise ValueError(f'Error: validator {expr} is not a valid regex: ' + str(re_error)) # pylint: disable=raise-missing-from

    def _regex(argname, argvalue) -> Any:
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
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname, argvalue) -> Any:
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
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname, argvalue) -> Any:
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
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname, argvalue) -> Any:
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
      errmsg (str, optional): The eventual error message. Defaults to None.

    Returns:
      Callable[..., Any]: The validator function.
    '''
    def validate(_argname, argvalue) -> Any:
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
