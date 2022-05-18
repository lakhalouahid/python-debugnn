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

def prepend_prefix(sub_dirs: list[str], prefix: str):
  return [os.path.join(prefix, sub_dir) for sub_dir in sub_dirs]

def get_subdirs(root: str):
  return prepend_prefix(os.listdir(root), root)

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

      options = " --{}={}".format(argname, argval)
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
