import subprocess

import json
import time
import copy
import pyfzf
import sys
import os
import re
import random, string

from typing import Optional

def get_random_str(length: int = 32):
   letters = string.ascii_letters + string.digits
   return ''.join(random.choice(letters) for _ in range(length))


def prepare_training(root_dir: str = "root"):
  jcfg = get_jcfg()
  cmds, jcmds = dict2cmd(jcfg)
  jinfos = instances_info(jcfg, jcmds)
  cwds = get_wds(len(cmds), root_dir)
  for cwd in cwds:
    path = os.path.join(os.getcwd(), cwd)
    if not os.path.exists(path):
      os.makedirs(path)
  return (jcfg, cmds, jinfos, cwds)


def train(root_dir: str = "root"):
  jcfg, cmds, jinfos, cwds = prepare_training(root_dir)
  num_workers = jcfg["num_workers"]
  poll = run_poll(cmds, cwds, num_workers, shell=True)
  pstatus = [None for _ in range(len(cmds))]

  procs = []
  for i, proc in enumerate(poll):
    procs.append(proc)
    with open(os.path.join(cwds[i], "training.json"), "wt") as fd:
      jinfos[i]["start-time"] = time.strftime('%Y-%m-%dT%H:%M:%S')
      json.dump(jinfos[i], fd)

  while True:
    all_terminated = True
    for i in range(len(procs)):
      pstatus[i] = procs[i].poll()
      if pstatus[i] == None:
        all_terminated = False
      else:
        jinfos[i]["end-time"] = time.strftime('%Y-%m-%dT%H:%M:%S')
        jinfos[i]["returncode"] = procs[i].poll()
        with open(os.path.join(cwds[i], "training.json"), "wt") as fd:
          json.dump(jinfos[i], fd)

    if all_terminated:
      break
    else:
      time.sleep(1)


def instances_info(jcfg, jcmds):
  jinfos = []
  for jcmd in jcmds:
    jinfo = copy.deepcopy(jcfg)
    for i, arg in enumerate(jinfo["args"]):
      arg["value"] = jcmd[i]
      del arg["values"]
      jinfos.append(jinfo)
  return jinfos

def run_training(cmds):
  raw_cmds = [cmd["raw"] for cmd in cmds]
  json_cmds = [cmd["json"] for cmd in cmds]
  return raw_cmds, json_cmds

def get_wds(size: int, root_dir="data",length: int = 32):
  cwds = []
  for _ in range(size):
    cwds.append(os.path.join(root_dir, get_random_str(length)))
  return cwds


def get_jcfg(cfg_path: str = "debugnn_config.json"):
  with open(cfg_path) as fd:
    return json.load(fd)



def dict2cmd(jcfg, prefix="python"):
  args = jcfg["args"]
  dargs = jcfg["default-args"]
  shape = tuple([len(arg["values"]) for arg in args])
  ixs = [0 for _ in range(len(shape))]
  cmds = []
  jcmds = []
  while ixs[-1] < shape[-1]:
    executable_path = os.path.join(os.getcwd(), jcfg['filename'])
    cmd = "{} {} {}".format(prefix, executable_path, dargs)
    jcmd = list(range(len(args)))

    for i in range(len(shape)):
      jcmd[i] = args[i]["values"][ixs[i]]
      argname = args[i]["name"]

      if args[i]["type"] == "bool" and jcmd[i]:
        options = " --{}".format(args[i]['name'])
      else:
        options =" --{}={}".format(argname, jcmd[i])
      cmd += options

    cmds.append(cmd)
    jcmds.append(jcmd)

    for i in range(len(shape)):
      ixs[i] +=  1
      if ixs[i] < shape[i] or ixs[-1] == shape[-1]:
        break
      else:
        ixs[i] = 0
  return cmds, jcmds


def run_poll(cmds: list, cwds: list, num_workers: int, sleep: float = 1, **args):
  ecmds = 0
  procs = []
  fds = []
  while ecmds < len(cmds) or len(procs) > 0:
    if len(procs) < num_workers and ecmds < len(cmds):
      fds.append(open(os.path.join(cwds[ecmds], "stdout.txt"), "w+"))
      proc = subprocess.Popen(cmds[ecmds], cwd=cwds[ecmds], stdout=fds[-1], **args)
      yield proc
      procs.append(proc)
      ecmds += 1
    for proc in procs:
      if proc.poll() != None:
        fds[procs.index(proc)].close()
        fds.pop(procs.index(proc))
        procs.remove(proc)
    time.sleep(sleep)

def parse_jtraining(jpath: str):
  fd = open(jpath, "r")
  jdata = json.load(fd)
  jinfo = {}
  jinfo["args"] = {}
  for arg in jdata["args"]:
    jinfo["args"][arg["name"]] = arg["value"]

  for k, v in parse_args(jdata["default-args"]).items():
    try:
      jinfo["args"][k] = float(v)
    except ValueError:
      jinfo["args"][k] = v
  fd.close()
  return jinfo


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


def get_jtraining(dirpath: str, jtraining_filename="training.json"):
  jtraining_filepath = os.path.join(dirpath, jtraining_filename)
  return parse_jtraining(jtraining_filepath)

def parse_args(args: str):
  matches = re.findall(r'(?:--?)([\w-]+)(.*?)(?= -|$)', args)

  result = {}
  for m in matches:
    result[m[0]] = True if not m[1] else m[1].strip()
  return result


def get_dirs(root_dir: str):
  root_dir_abs = os.path.join(os.getcwd(), root_dir)
  return [os.path.join(root_dir_abs, sub_dir) for sub_dir in os.listdir(root_dir_abs)]

def format(args):
  str_args = ''
  for k,v in args["args"].items():
    str_args += "{}: {}, ".format(k, v)
  return str_args

def pretty_json(jdict):
  return json.dumps(jdict, indent=4)

def get_cmd_from_script(script, exe: str="python", extra: str=""):
  cwd = os.getcwd()
  script_abs_path = os.path.join(cwd, script)
  cmd = "{} {} {}".format(exe, script_abs_path, extra)
  return cmd

def loop_script(script_rpath: str, root_dir: str="root", extra: str="", exe: str="python"):
  fzf = pyfzf.FzfPrompt("/usr/bin/fzf")
  sub_dirs = get_dirs(root_dir)
  sub_jinfos = [get_jtraining(sub_dir) for sub_dir in sub_dirs]
  train_files = [os.path.join(sub_dir, "logs/train.log") for sub_dir in sub_dirs]
  for i in range(len(sub_dirs)):
    sub_jinfos[i]["args"]["log"] = float(read_lastline(train_files[i]).split(",")[0])

  sub_str_jinfos = [format(sub_jinfo) for sub_jinfo in sub_jinfos]
  dir_index = 0
  proc = None
  while True:
    uinput = input("Enter command (q/n/p/s/i/r): ")
    if uinput == "q":
      if proc != None:
        proc.terminate()
      break
    elif uinput == "n":
      dir_index += 1
    elif uinput == "p":
      dir_index -= 1
    elif uinput == "r":
      pass
    elif uinput == "s":
      selected_args_list = fzf.prompt(sub_str_jinfos)
      for selected_args in selected_args_list:
        dir_index = sub_str_jinfos.index(selected_args)
    elif uinput == "i":
      print(pretty_json(sub_jinfos[dir_index]["args"]))
      continue
    print(pretty_json(sub_jinfos[dir_index]["args"]))
    if proc != None:
      proc.terminate()
    proc = subprocess.Popen(get_cmd_from_script(script_rpath, exe=exe, extra=extra), cwd=sub_dirs[dir_index], shell=True, stdin=sys.stdin)
    proc.wait()
