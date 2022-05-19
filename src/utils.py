import re
import os
import json
import string
import random
from typing import Union

def json_read(json_filepath):
  with open(json_filepath, "rt") as fd:
    return json.load(fd)


def json_write(obj: Union[list, dict], json_filepath):
  with open(json_filepath, "wt") as fd:
    return json.dump(obj, fd, separators=(",", ":"))

def json_writelist(dicts: list, cfg_filepaths):
  for _dict, cfg_filepath in zip(dicts, cfg_filepaths):
    return json_write(_dict, cfg_filepath)

def randstr(length: int = 32):
  letters = string.ascii_letters + string.digits
  return "".join(random.choice(letters) for _ in range(length))

def randsubdirs(size: int, rootdir="data", length: int = 10):
  cwds = [os.path.join(rootdir, randstr(length)) for _ in range(size)]
  return cwds


def rawparse_args(rawoptions: str):
  matches = re.findall(r'(?:--?)([\w-]+)(.*?)(?= -|$)', rawoptions)
  result = {}
  for m in matches:
    try:
      result[m[0]] = True if not m[1] else float(m[1].strip())
    except ValueError:
      result[m[0]] = True if not m[1] else m[1].strip()
  return result

def dict_pretty_print(_dict):
  return json.dumps(_dict, indent=4)


def read_lastline(filepath):
  with open(filepath, 'rb') as f:
    try:
      f.seek(-2, os.SEEK_END)
      while f.read(1) != b'\n':
        f.seek(-2, os.SEEK_CUR)
    except OSError:
      f.seek(0)
    last_line = f.readline().decode()
  return last_line


def append_basename(sub_dirs: list[str], basename: str):
  return [os.path.join(sub_dir, basename) for sub_dir in sub_dirs]

def prepend_prefix(suffix_list: list[str], prefix: str):
  return ["{} {}".format(prefix, suffix) for suffix in suffix_list]

def append_prefix(prefix_list: list[str], suffix: str):
  return ["{} {}".format(prefix, suffix) for prefix in prefix_list]

def prepend_dir(sub_dirs: list[str], dirname: str):
  return [os.path.join(dirname, sub_dir) for sub_dir in sub_dirs]

def get_subdirs(root: str):
  return prepend_dir(os.listdir(root), root)

def gen_rawoptionslist(cfg):
  args, default_args = cfg["args"], cfg["default-args"]
  shape, idx = tuple([len(arg["values"]) for arg in args]), [0 for _ in range(len(args))]
  rawoptionslist, n = [], len(shape)
  while idx[-1] < shape[-1]:
    cmd = default_args
    for i, arg in enumerate(args):
      argval = arg["values"][idx[i]]
      argname = arg["name"]
      argtype = arg["type"]

      options = " --{} {}".format(argname, argval)
      if argtype == "bool" and argval:
        options = " --{}".format(args[i]['name'])
      cmd += options
    rawoptionslist.append(cmd)

    for i in range(n):
      idx[i] +=  1
      if idx[i] < shape[i] or idx[-1] == shape[-1]:
        break
      else:
        idx[i] = 0
  return rawoptionslist

def get_dictoptionslist(rawoptionslist: list[str]):
  return [rawparse_args(rawoptions) for rawoptions in rawoptionslist]


def dict_formatfzf(_dict: dict):
  s = ''
  for k,v in _dict.items():
    s += ", {}: {}".format(k, v)
  return s[2:]


def maplist(_list: list, func):
  return [func(item) for item in _list]

def runlist(_list: list, func):
  for item in _list:
    func(item)


def script2cmd(script: str, executable: str, options: str):
  script_abspath = os.path.join(os.getcwd(), script)
  return "{} {} {}".format(executable, script_abspath, options)


def get_valdicts(dicts: list[dict], key: str):
  return [_dict[key] for _dict in dicts]

def set_keyvaldicts(dicts: list[dict], keys: list[str], values: list):
  for i in range(len(dicts)):
    dicts[i][keys[i]] = values[i]
  return dicts

def repeat(item, size: int):
  return [item for _ in range(size)]
