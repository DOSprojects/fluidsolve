'''
This module implements a class to store catalogue.
The data is internally stored in a dictionary.
'''
# =============================================================================
# IMPORTS
# =============================================================================
import os
import json
import fnmatch
from operator import eq, ne, lt, gt, le, ge
from typing               import Optional, Any
# module own
import fluidsolve.aux_tools as flsa
import fluidsolve.medium    as flsm
# units
u         = flsm.unitRegistry
Quantity  = flsm.Quantity
# =============================================================================
# PUMPCATALOGUE DATA CLASS
# =============================================================================
class Catalogue ():
  ''' Class to search some catalogues.
      The catalogues are provided as json files.

  Args:
    path (list, optional): List of path names where the catalogues are found.
      These can be appended to the build in path (with the build in catalogues). See `loadAllData`.
      Defaults to [].
    load (bool, optional): Load the catalogue data at init or not.
      Defaults to True.


  Returns:
    None
  '''

  def __init__ (self, **kwargs: int) -> None:
    args = flsa.GetArgs(kwargs)
    self._path: str = args.getArg(
      'path',
      [
          flsa.vFun.default([]),
          flsa.vFun.istype(str, list),
          flsa.vFun.tolambda(lambda x: x if isinstance(x, list) else [x]),
      ]
    )
    load: bool = args.getArg(
      'load',
      [
          flsa.vFun.default(True),
          flsa.vFun.istype(bool),
      ]
    )
    #
    self._d: dict = {}
    self._buildinpath : str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comp_cat')
    #
    if load:
      self.loadAllData()


  def loadAllData(self, buildin: bool=True) -> None:
    '''  Load the libraries.

    Args:
        buildin (bool, optional): also load the buildin catalogues
        Defaults to True.
    '''
    allpaths = list(self._path)
    if buildin:
      allpaths.append(self._buildinpath)
    for path in allpaths:
      for fname in os.listdir(path):
        if fname.endswith('.json'):
          file_path = os.path.join(path, fname)
          with open(file_path, 'r', encoding='utf-8') as file:
            try:
              data = json.load(file)
              key = data['library']['name']
              self._d[key] = data
            except json.JSONDecodeError as e:
              print(f'Error decoding JSON from file {file_path}: {e}')

  def findLibraries(self, criteria: str='', matchcase: bool=True) -> list:
    ''' find all libraries containing some conditions

    Args:
        criteria (str): Criteria string (logical expression).
                      If this is empty, then all libraries are returned.
                      Can be a combination with parentheses, AND, OR and NOT and the * wildcard can be used.
        matchcase (bool): Case must match or not (Default=True)

    Returns:
        list: Matching library names.

    Examples:
      lib = cat.findLibraries()
      lib = cat.findLibraries('APV')
      lib = cat.findLibraries('appendage AND (bend OR BS-90) OR (DIN11852 AND BS-90)')
    '''
    if len(criteria) == 0:
      return list(self._d.keys())
    else:
      # tokenize
      hcriteria = criteria.replace('(', ' ( ').replace(')', ' ) ')
      tokens = hcriteria.split()
      parsed = self._parseExpression(tokens)
      #print('Parsed L: ', parsed)
      # do search
      found = []
      for libname, libdata in self._d.items():
        terms = []
        for v in libdata['library'].values():
          if isinstance(v, list):
            terms.extend(v)
          else:
            terms.append(v)
        if self._evalLibExpression(parsed, terms, matchcase):
          found.append(libname)
      return found

  def searchInLibrary(self, lib: str | list, criteria: str, matchcase: bool=True) -> list[dict]:
    ''' Find all records in a library or list of libraries matching the given criteria.

    Args:
        lib (str | list): Library name or list of names to search in
        criteria (str): Criteria string (logical expression).
        matchcase (bool): Case must match or not (Default=True)

    Returns:
        list[dict]: The list of records found.

    Examples:
      items = cat.searchInLibrary(lib, 'OD < 20')
      items = cat.searchInLibrary(lib, 'WT >= 2 AND DN < 80')        
    '''
    if isinstance(lib, str):
        lib = [lib]
    # tokenize
    hcriteria = criteria.replace('(', ' ( ').replace(')', ' ) ')
    tokens = hcriteria.split()
    parsed = self._parseExpression(tokens)
    #print('Parsed S: ', parsed)
    # do search
    found = []
    for l in lib:
      data = self._d[l]['records']
      for rec in data:
        if self._evalRecExpression(parsed, rec, matchcase):
          found.append(rec)
    return found

  def _parseExpression(self, tokens: list) -> dict:
    ''' Parse a (criterion) expression presented as a list of tokens.
        One token can be a string or a value. A string with spaces in it has to be delimited in single or double quotes.
        It can also be a trio field operand value (e.g. WT >= 2.4); again a field with spaces in it has to be delimited in single or double quotes.
        It can be AND, OR or NOR or an opening or closing parenthesis.

        This internal method first is used to parse an input criterion to select one or a number of available libraries.
        Secondly it is used to select one or more records form a library or list of libraries.

    Args:
        tokens (list): The input tokens.

    Returns:
        dict: A multilevel dict with the parsed expression.

    Examples:
        _parseExpression(['appendage', 'AND', 'bend'])
        {'AND': ['appendage', 'bend']}

        _parseExpression(['WT', '>=', '2', 'AND', 'DN', '<', '80'])
        {'AND': ['WT >= 2', 'DN < 80']}

    '''
    stack = []
    ops = ['>=', '<=', '!=', '=', '<', '>']
    #print('T', tokens)
    while tokens:
      token = tokens.pop(0)
      # Check for criterion of type: field op value (e.g. WT >= 2.4)
      if len(tokens) >= 2 and tokens[0] in ops:
        field = token
        op = tokens.pop(0)
        value = tokens.pop(0)
        if value.startswith('"') or value.startswith("'"):
          quote_char = value[0]
          while not (value.endswith(quote_char) and len(value) > 1):
            if not tokens:
              raise ValueError('Unclosed quoted value in criteria {token}')
            value += ' ' + tokens.pop(0)
        stack.append(f'{field} {op} {value}')
      else:
        if token == '(':
          stack.append(self._parseExpression(tokens))
        elif token == ')':
            break
        elif token.upper() == 'AND':
          stack.append('AND')
        elif token.upper() == 'OR':
          stack.append('OR')
        elif token.upper() == 'NOT':
          stack.append({'NOT': tokens.pop(0)})
        else:
          stack.append(token)
    # reduce stack
    # Step 1: Handle NOT (highest precedence)
    i = 0
    while i < len(stack):
      if isinstance(stack[i], dict) and 'NOT' in stack[i]:
        stack[i] = {'NOT': stack[i]['NOT']}
      i += 1
    # Step 2: Handle AND
    i = 0
    while i < len(stack):
      if stack[i] == 'AND':
        left = stack[i - 1]
        right = stack[i + 1]
        stack[i - 1:i + 2] = [{'AND': [left, right]}]
        i = 0  # Restart to handle nested ANDs
      else:
        i += 1
    # Step 3: Handle OR
    i = 0
    while i < len(stack):
      if stack[i] == 'OR':
        left = stack[i - 1]
        right = stack[i + 1]
        stack[i - 1:i + 2] = [{'OR': [left, right]}]
        i = 0  # Restart to handle nested ORs
      else:
          i += 1
    return stack[0]

  def _evalLibExpression(self, expr: str, values: list, matchcase: bool=True) -> bool:
    ''' This internal method is used to parse an input criterion to select one or a number of available libraries.

    Args:
        expr (str): This is the parsed tokenized search expression.
        values (list): This is the list of keywords to be searched.
        matchcase (bool, optional): Has the case to match or not. Defaults to True.

    Returns:
        bool: True is one of the values matches the expression.
    '''
    def match(term: str) -> bool:
      if not matchcase:
        term = term.lower()
      return any(fnmatch.fnmatchcase(value, term) for value in values_in)

    def evalExpr(expr) -> bool:
      if isinstance(expr, str):
        return match(expr)
      if 'AND' in expr:
        return all(evalExpr(sub) for sub in expr['AND'])
      elif 'OR' in expr:
        return any(evalExpr(sub) for sub in expr['OR'])
      elif 'NOT' in expr:
        return not evalExpr(expr['NOT'])
      raise ValueError('Invalid expression format')

    if matchcase:
      values_in = values
    else:
      values_in = [v.lower() for v in values]
    return evalExpr(expr)

  def _evalRecExpression(self, expr, rec, matchcase=True):
    '''This method is used to select one or more records form a library or list of libraries.

    Args:
        expr (_type_): This is the parsed tokenized search expression.
        rec (_type_): This is the list of records to be searched.
        matchcase (bool, optional): Has the case to match or not. Defaults to True.
    '''
    def parseCriterion(atom: str):
      # Supported operators, longest first
      ops = ['>=', '<=', '!=', '=', '<', '>']
      for op in ops:
        if op in atom:
          parts = atom.split(op, 1)
          field = parts[0].strip()
          value = parts[1].strip()
          # Remove quotes if present
          if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
          return field, op, value
      raise ValueError(f'Invalid atomic criterion: {atom}')

    def match(atom):
        field, op_str, val = parseCriterion(atom)
        if field not in rec:
            return False
        rec_val = rec[field]
        # Try to convert val to type of rec_val
        try:
            if isinstance(rec_val, (int, float)):
                val_cast = type(rec_val)(val)
            else:
                val_cast = val
        except Exception:
            val_cast = val
        if not matchcase and isinstance(rec_val, str) and isinstance(val_cast, str):
            rec_val = rec_val.lower()
            val_cast = val_cast.lower()
        return op_map[op_str](rec_val, val_cast)

    def evalExpr(expr):
        if isinstance(expr, str):
            return match(expr)
        if 'AND' in expr:
            return all(evalExpr(sub) for sub in expr['AND'])
        elif 'OR' in expr:
            return any(evalExpr(sub) for sub in expr['OR'])
        elif 'NOT' in expr:
            return not evalExpr(expr['NOT'])
        raise ValueError(f'Invalid expression format {expr}')

    op_map = {
        '=': eq,
        '!=': ne,
        '<': lt,
        '>': gt,
        '<=': le,
        '>=': ge
    }
    
    return evalExpr(expr)
