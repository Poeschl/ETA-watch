import logging
import os
from typing import Type

from pyeta import VariableList, Variable, VariableType
from yaml import load, YAMLError, dump, SafeLoader, SequenceNode, MappingNode

CONFIG_FILE = "config.yaml"
DEFAULT_CONFIG = {
  "bot_token": "",
  "users": [],
  "eta_host": "",
  "reference_settings": {}
}


def variablelist_constructor(loader: SafeLoader, node: MappingNode) -> VariableList:
  return VariableList(**loader.construct_mapping(node))


def variable_constructor(loader: SafeLoader, node: MappingNode) -> Variable:
  mapping = loader.construct_mapping(node)
  parsed_var = Variable(mapping["name"], mapping["uri"], mapping["variable_type"], mapping["adv_text_offset"], mapping["unit"], mapping["str_value"],
                        mapping["scale_factor"], mapping["dec_places"], mapping["value"])
  parsed_var.last_updated = mapping["last_updated"]
  return parsed_var


def variabletype_constructor(loader: SafeLoader, node: SequenceNode) -> VariableType:
  return VariableType(loader.construct_sequence(node)[0])


config_loader: Type[SafeLoader] = SafeLoader
config_loader.add_constructor("tag:yaml.org,2002:python/object:pyeta.VariableList", variablelist_constructor)
config_loader.add_constructor("tag:yaml.org,2002:python/object:pyeta.Variable", variable_constructor)
config_loader.add_constructor("tag:yaml.org,2002:python/object/apply:pyeta.VariableType", variabletype_constructor)


def read_config() -> dict:
  if os.path.exists(CONFIG_FILE):
    with (open(CONFIG_FILE, "r") as configFile):
      try:
        config = load(configFile, Loader=config_loader)
        return config
      except YAMLError as exc:
        logging.error("Error on file config read. {}".format(exc))
        return {}
  else:
    with (open(CONFIG_FILE, "w") as configFile):
      configFile.writelines(dump(DEFAULT_CONFIG))
      return DEFAULT_CONFIG


def save_ref_settings(ref_setting: dict):
  config = read_config()
  config["reference_settings"] = ref_setting
  with (open(CONFIG_FILE, "w") as configFile):
    configFile.writelines(dump(config))


def save_yaml_ref_settings(yaml_ref: str) -> None:
  config = read_config()
  config["reference_settings"] = load(yaml_ref, config_loader)
  with (open(CONFIG_FILE, "w") as configFile):
    configFile.writelines(dump(config))


def load_yaml_ref_settings() -> str:
  config = read_config()
  return dump(config["reference_settings"])
