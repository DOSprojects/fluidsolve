'''
Catalogue utilities for loading and searching component library data.

This module provides the Catalogue class, which loads one or more JSON
libraries and offers query helpers to find matching libraries and records.
Loaded data is stored in-memory as dictionaries keyed by library name.

Main capabilities:

* load built-in and user-provided catalogue directories,
* list or filter libraries by keyword expressions,
* search records with logical and comparison criteria,
* evaluate case-sensitive or case-insensitive matching.

Query model:

* logical operators: ``AND``, ``OR``, ``NOT``
* grouping with parentheses: ``(...)``
* comparison operators for record fields: ``=``, ``!=``, ``<``, ``<=``, ``>``, ``>=``
* wildcard support for library keyword matching via ``*``

Typical workflow:

1. Create ``Catalogue()`` and load data (default behavior at init).
2. Use ``findLibraries(...)`` to narrow candidate libraries.
3. Use ``searchInLibrary(...)`` to retrieve matching records.

Examples::

  cat = Catalogue()
  libs = cat.findLibraries('pump AND APV')
  records = cat.searchInLibrary(
      libs,
      'T = centrifugal AND impeller0 = 110 AND speed0 = 2900'
  )

The parser is intentionally lightweight and expression-oriented, which keeps
catalogue searches readable while still supporting practical filtering logic.
'''
# =============================================================================
# PYLINT DIRECTIVES
# =============================================================================

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
import fluidsolve.medium    as flsme
# units
u         = flsme.unitRegistry
Quantity  = flsme.Quantity  # type: ignore[misc]
# =============================================================================
# PUMPCATALOGUE DATA CLASS
# =============================================================================
class Catalogue ():
  ''' Search one or more catalogues loaded from JSON files.

  Args:
    path (list, optional): List of paths where catalogues are found.
      These are appended to the built-in catalogue path.
    load (bool, optional): Load the catalogue data at init or not.
      

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
    ''' Load all catalogue libraries.

    Args:
      buildin (bool, optional): Also load the built-in catalogues.
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
    ''' Find library names that match the given criteria.

    Args:
      criteria (str): Logical criteria expression.
        If empty, all libraries are returned.
        Parentheses, AND, OR, NOT, and `*` wildcards are supported.
      matchcase (bool): Whether matching is case-sensitive.

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
    ''' Find records in one or more libraries matching the criteria.

    Args:
      lib (str | list): Library name or list of library names.
      criteria (str): Logical criteria expression.
      matchcase (bool): Whether matching is case-sensitive.

    Returns:
      list[dict]: Matching records.

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
    ''' Parse a criteria expression represented as tokens.

      A token can be a string literal or a value. Strings with spaces
      must be enclosed in single or double quotes.
      A token group can also be in the form `field op value`
      (for example: `WT >= 2.4`).
      Supported operators are AND, OR, NOT, and parentheses.

      This method is used for both library-level and record-level
      criteria parsing.

    Args:
        tokens (list): The input tokens.

    Returns:
      dict: Parsed expression tree.

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
    ''' Evaluate a parsed expression against library metadata values.

    Args:
      expr (str): Parsed expression tree.
      values (list): Keywords to test against the expression.
      matchcase (bool, optional): Whether matching is case-sensitive.

    Returns:
      bool: True when the expression matches.
    '''
    def match(term: str) -> bool:
      if not matchcase:
        term = term.lower()
      return any(fnmatch.fnmatchcase(value, term) for value in values_in)

    def evalExpr(expr: Any) -> bool:
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

  def _evalRecExpression(self, expr: Any, rec: Any, matchcase: Any=True) -> Any:
    ''' Evaluate a parsed expression against a single record.

    Args:
      expr (Any): Parsed expression tree.
      rec (Any): Record dictionary to evaluate.
      matchcase (bool, optional): Whether matching is case-sensitive.

    Returns:
      bool: True when the record matches the expression.
    '''
    def parseCriterion(atom: str) -> Any:
      # Supported operators (longest first)
      ops = ['>=', '<=', '!=', '=', '<', '>']
      for op in ops:
        if op in atom:
          parts = atom.split(op, 1)
          field = parts[0].strip()
          value = parts[1].strip()
          # Remove surrounding quotes when present.
          if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
          return field, op, value
      raise ValueError(f'Invalid atomic criterion: {atom}')

    def match(atom: Any) -> Any:
      field, op_str, val = parseCriterion(atom)
      if field not in rec:
        return False
      rec_val = rec[field]
      # Try to cast criterion value to the record value type.
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

    def evalExpr(expr: Any) -> Any:
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
