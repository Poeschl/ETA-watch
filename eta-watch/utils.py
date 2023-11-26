from pyeta import VariableList, Variable


class Diff:
  path: str
  old: Variable
  new: Variable | None

  def __init__(self, path: str, old: Variable, new: Variable | None):
    super().__init__()
    self.path = path
    self.old = old
    self.new = new

  def msg_str(self) -> str:
    old = f"{self.old.name} = {self.old.value} ('{self.old.str_value}')"

    if self.new is not None:
      new = f"{self.new.name} = {self.new.value} ('{self.new.str_value}')"
    else:
      new = "None"

    return f" {self.path}\n {old} -> {new}"

  def __str__(self) -> str:
    return f" {self.path}: {self.old} -> {self.new}"

  def __repr__(self) -> str:
    return self.__str__()


def diff_variable_list(first_list: VariableList, second_list: VariableList, path: str = "") -> list[Diff]:
  diff = []

  for element_key in first_list.elements:
    variable_or_list = first_list.elements[element_key]
    other_variable_or_list = second_list.elements.get(element_key, None)

    if isinstance(variable_or_list, VariableList) and isinstance(other_variable_or_list, VariableList):
      deepdiff = diff_variable_list(variable_or_list, other_variable_or_list, path + f"/{element_key}")
      diff.extend(deepdiff)

    elif isinstance(variable_or_list, Variable) and isinstance(other_variable_or_list, Variable):
      if variable_or_list.value != other_variable_or_list.value or variable_or_list.str_value != other_variable_or_list.str_value:
        diff.append(Diff(path, variable_or_list, other_variable_or_list))

    else:
      diff.append(Diff(path, variable_or_list, None))

  return diff


def replace_variable_in_list_with_same_variable_in_other_list(list: VariableList, list_newer: VariableList) -> int:
  """
  Replaces any variable from the first list with the equivalent variable from the second list, when the value differs.
  If the variable can not be updated, it will stay as it is.

  :param list: The list which will be updated
  :param list_newer: The list with the source variables for the replacement
  :returns The count of updated values
  """
  changes = 0

  for element_key in list.elements:
    variable_or_list = list.elements[element_key]
    other_variable_or_list = list_newer.elements.get(element_key, None)

    if isinstance(variable_or_list, VariableList) and isinstance(other_variable_or_list, VariableList):
      changes += replace_variable_in_list_with_same_variable_in_other_list(variable_or_list, other_variable_or_list)

    elif isinstance(variable_or_list, Variable) and isinstance(other_variable_or_list, Variable):
      if variable_or_list.value != other_variable_or_list.value or variable_or_list.str_value != other_variable_or_list.str_value:
        list.elements[element_key] = other_variable_or_list
        changes += 1

  return changes
