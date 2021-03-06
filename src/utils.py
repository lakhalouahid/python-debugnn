import re
import os
import json
import string
import random
from typing import Union

def json_read(json_filepath):
  """load json file
  """
  with open(json_filepath, "r") as fd:
    fd.seek(0)
    return json.load(fd)


def json_write(obj: Union[list, dict], json_filepath):
  """dump object to json file
  """
  with open(json_filepath, "w") as fd:
    fd.seek(0)
    return json.dump(obj, fd, separators=(",", ":"))

def json_writelist(dicts: list, cfg_filepaths):
  """dump objects to json files separately
  """
  for _dict, cfg_filepath in zip(dicts, cfg_filepaths):
    json_write(_dict, cfg_filepath)

def randstr(length: int = 32):
  """get random string with specific length
  """
  letters = string.ascii_letters + string.digits
  return "".join(random.choice(letters) for _ in range(length))

def randsubdirs(size: int, rootdir="data", length: int = 10):
  """get random sub-directories from root directory
  """
  cwds = [os.path.join(rootdir, randstr(length)) for _ in range(size)]
  return cwds

def makenumberedsubdirs(size: int, rootdir="data"):
  """make new numbers subdirectories
  """
  try:
    subdirs = [subdir for subdir in os.listdir(rootdir) if os.path.isdir(os.path.join(rootdir, subdir))]
    train_subdirs = []
    for subdir in subdirs:
      try:
        train_subdirs.append(int(subdir))
      except:
        pass
    train_subdirs.sort(reverse=True)
    if len(subdirs) > 0:
      base = 1 + train_subdirs[0]
    else:
      base = 1
  except  FileNotFoundError:
    base = 1
  cwds = [os.path.join(rootdir, str(i)) for i in range(base, base + size)]
  return cwds


def rawparse_args(rawoptions: str):
  """parse raw args to dict
  """
  matches = re.findall(r'(?:--?)([\w-]+)(.*?)(?= -|$)', rawoptions)
  result = {}
  for m in matches:
    try:
      result[m[0]] = True if not m[1] else float(m[1].strip())
    except ValueError:
      result[m[0]] = True if not m[1] else m[1].strip()
  return result

def dict_pretty_print(_dict):
  """pretty print of dict
  """
  return json.dumps(_dict, indent=4)


def read_lastline(filepath):
  """read last line of file
  """
  with open(filepath, 'rb') as f:
    try:
      f.seek(-2, os.SEEK_END)
      while f.read(1) != b'\n':
       f.seek(-2, os.SEEK_CUR)
    except OSError:
      f.seek(0)
    last_line = f.readline().decode()
  return last_line

def gen_rawoptionslist_from_dicts(dictcmds):
  """generate list of raw arguments from list of dicts
  """
  rawoptionslist = []
  for i in range(len(dictcmds)):
    cmd = ""
    for argname, argval in dictcmds[i].items():
      options = " --{} {}".format(argname, argval)
      if type(argval) == bool:
        if argval == True:
          options = " --{}".format(argname)
        else:
          options == ""
      cmd += options
    rawoptionslist.append(cmd)

  return rawoptionslist

def append_basename(sub_dirs: list[str], basename: str):
  """append basename to list of sub directories
  """
  return [os.path.join(sub_dir, basename) for sub_dir in sub_dirs]
def prepend_prefix(suffix_list: list[str], prefix: str):
  """preprend prefix to list strings
  """
  return ["{} {}".format(prefix, suffix) for suffix in suffix_list]

def append_suffix(prefix_list: list[str], suffix: str):
  """append subffix to list strings
  """
  return ["{} {}".format(prefix, suffix) for prefix in prefix_list]

def prepend_dir(sub_dirs: list[str], dirname: str):
  """prepend prefix to list of sub directories
  """
  return [os.path.join(dirname, sub_dir) for sub_dir in sub_dirs]

def get_subdirs(root: str, exclude_folders = []):
  """list sub directories from root directory
  """
  sub_dirs = [subdir for subdir in os.listdir(root) if os.path.isdir(os.path.join(root, subdir)) and (not subdir in exclude_folders)]
  sub_dirs.sort(key=lambda x: os.stat(os.path.join(root, x)).st_ctime, reverse=True)
  return prepend_dir(sub_dirs, root)


def gen_rawoptionslist(cfg):
  """generate raw options list
  """
  args, default_args = cfg["args"], cfg["default-args"]
  shape, idx = tuple([len(arg["values"]) for arg in args]), [0 for _ in range(len(args))]
  rawoptionslist, n = [], len(shape)
  while idx[-1] < shape[-1]:
    cmd = default_args
    for i, arg in enumerate(args):
      argval, argname, argtype = arg["values"][idx[i]], arg["name"], arg["type"]
      options = " --{} {}".format(argname, argval)
      if argtype == "bool":
        options = ""
        if argval:
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
  """parse list of str to dicts
  """
  return [rawparse_args(rawoptions) for rawoptions in rawoptionslist]


def dict_formatfzf(_dict: dict, filterfields: list[str] = []):
  """format dict
  """
  s = ''
  for k, v in _dict.items():
    if not k in filterfields:
      s += ", {}: {}".format(k, v)
  return s[2:]


def maplist(_list: list, func):
  """maplist
  """
  return [func(item) for item in _list]

def maplistindex(_list: list, func):
  """maplist
  """
  return [func(item, index) for index, item in enumerate(_list)]

def runlist(_list: list, func):
  """runlist
  """
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
  """repeat item
  """
  return [item for _ in range(size)]


def get_latesfile(dirpath, exclude_folders=[]):
  """get latest file under dirpath
  """
  return max(get_subdirs(dirpath, exclude_folders=exclude_folders), key = os.path.getctime)

