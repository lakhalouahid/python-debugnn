import subprocess

import time
import sys
import os

from typing import Optional
from utils import *
from pyfzf import FzfPrompt


fzf = FzfPrompt("/usr/bin/fzf")

def prepare_training(config_filepath):
  cfg = json_read(config_filepath)
  rawoptionslist = gen_rawoptionslist(cfg)
  cmds_nmbr = len(rawoptionslist)
  rootdir = cfg["root"]
  cwds = randsubdirs(rootdir=rootdir, size=cmds_nmbr)
  for cwd in cwds:
    path = os.path.join(os.getcwd(), cwd)
    if not os.path.exists(path):
      os.makedirs(path)
  return (cfg, rawoptionslist, cwds)


def train_jobspoll(config_path: str="debugnn_config.json", executable: str="python", **args):
  cfg, rawoptionslist, cwds = prepare_training(config_path)
  dictoptionslist = get_dictoptionslist(rawoptionslist)
  cmd_prefix = "{} {}".format(executable, os.path.join(os.getcwd(), cfg["filename"]))
  cmds = prepend_prefix(rawoptionslist, prefix=cmd_prefix)
  poll = run_jobspoll(cmds=cmds, cwds=cwds, dictoptionslist=dictoptionslist, num_workers=cfg["num_workers"], shell=True, **args)

  procs = []
  for proc in poll:
    procs.append(proc)

  while True:
    all_terminated = True
    for i in range(len(procs)):
      if procs[i].poll() == None:
        all_terminated = False

    if all_terminated:
      break
    time.sleep(1)

def run_jobspoll(cmds: list[str], cwds: list[str], dictoptionslist: list[dict], num_workers: int=4, sleep: float=1, test: bool=False, cfg_filename: str="config.json", **args):
  stdinfds, stdoutfds, stderrfds = [], [], []
  procs, exe_cmds,ncmd = [], 0, len(cwds)
  cfg_filepaths = append_basename(cwds, cfg_filename)
  dictoptionslist = set_keyvaldicts(dictoptionslist, repeat("cmd", ncmd), cmds)
  dictoptionslist = set_keyvaldicts(dictoptionslist, repeat("train-started", ncmd), repeat(False, ncmd))
  dictoptionslist = set_keyvaldicts(dictoptionslist, repeat("train-ended", ncmd), repeat(False, ncmd))
  json_writelist(dictoptionslist, cfg_filepaths)
  while exe_cmds < ncmd or len(procs) > 0:
    if len(procs) < num_workers and exe_cmds < len(cmds):
      if not test:
        stdoutfds.append(open(os.path.join(cwds[exe_cmds], "stdout"), "x"))
        stderrfds.append(open(os.path.join(cwds[exe_cmds], "stderr"), "x"))
        stdinfds.append(open(os.path.join(cwds[exe_cmds], "stdin"), "x+"))
        json_cfg_filename = os.path.join(cwds[exe_cmds], cfg_filename)
        cfg_dict = dictoptionslist[exe_cmds]
        cfg_dict["train-started"] = True
        json_write(cfg_dict, json_cfg_filename)
        proc = subprocess.Popen(
            cmds[exe_cmds],
            cwd=cwds[exe_cmds],
            stdin=stdinfds[-1],
            stdout=stdoutfds[-1],
            stderr=stderrfds[-1],
            shell=True)
      else:
        print(cmds[exe_cmds],cwds[exe_cmds])
        proc = subprocess.Popen(
            cmds[exe_cmds],
            cwd=cwds[exe_cmds],
            stdout=subprocess.DEVNULL,
            shell=True)
      yield proc
      procs.append(proc)
      exe_cmds += 1
    for proc in procs:
      if proc.poll() != None:
        pidx = procs.index(proc)
        if not test:
          stdoutfds[pidx].close()
          stderrfds[pidx].close()
          stdinfds[pidx].close()
          stdoutfds.pop(pidx)
          stderrfds.pop(pidx)
          stdinfds.pop(pidx)
        else:
          proc.wait()
        procs.pop(pidx)
        cfg_path = os.path.join(cwds[pidx], "config.json")
        cfg_dict = json_read(cfg_path)
        cfg_dict["train-ended"] = True
        json_write(cfg_dict, cfg_path)
    time.sleep(sleep)
  if test:
    runlist(cwds, os.rmdir)

def run_scriptover(script: str, root: str="root", executable: str="python", options: str="", othercfgsfunc = None):
  sub_dirs = get_subdirs(root)
  sub_cfgsfiles = append_basename(sub_dirs, "config.json")
  sub_cfgslist = maplist(sub_cfgsfiles, json_read)
  sub_othercfgslist = othercfgsfunc(sub_dirs)
  n, idx, proc = len(sub_dirs), 0, None
  for i in range(n):
    for k, v in sub_othercfgslist[i].items():
      sub_cfgslist[i][k] = v

  sub_cfgsliststr = maplist(sub_cfgslist, dict_formatfzf)
  while True:
    uinput = input("Enter command (q/n/p/s/i/r): ")
    if uinput == "q":
      if proc != None:
        proc.terminate()
      break
    elif uinput == "n":
      idx += 1
    elif uinput == "p":
      idx -= 1
    elif uinput == "r":
      pass
    elif uinput == "s":
      selected_args_list = fzf.prompt(sub_cfgsliststr)
      for selected_args in selected_args_list:
        idx = sub_cfgsliststr.index(selected_args)
    elif uinput == "i":
      print(dict_pretty_print(sub_cfgslist[idx]))
      continue
    print(dict_pretty_print(sub_cfgslist[idx]))
    if proc != None:
      proc.terminate()
    cmd = script2cmd(script, executable=executable, options=options)
    proc = subprocess.Popen(cmd, cwd=sub_dirs[idx], stdin=sys.stdin, shell=True)
    proc.wait()

def resume_training(root: str, num_workers: int, cfg_filename: str = "config.json", resume_option: str = "--resume", sleep: float = 1):
  cwds = get_subdirs(root)
  cfg_filepaths = append_basename(cwds, "config.json")
  dictoptionslist = maplist(cfg_filepaths, json_read)
  cmds = get_valdicts(dictoptionslist, "cmd")
  stdinfds, stdoutfds, stderrfds = [], [], []
  procs, _cwds, exe_cmds, skip_cmds = [], [], 0, 0
  while exe_cmds < len(cmds) or len(procs) > 0:
    json_cfg_filename = os.path.join(cwds[exe_cmds + skip_cmds], cfg_filename)
    cfg_dict = dictoptionslist[exe_cmds + skip_cmds]
    if not cfg_dict["train-ended"]:
      if len(procs) < num_workers and exe_cmds < (len(cmds) - skip_cmds):
        _cwds.append(cwds[exe_cmds + skip_cmds])
        if not cfg_dict["train-started"]:
          stdoutfds.append(open(os.path.join(_cwds[-1], "stdout"), "x"))
          stderrfds.append(open(os.path.join(_cwds[-1], "stderr"), "x"))
          stdinfds.append(open(os.path.join(_cwds[-1], "stdin"), "x+"))
          cfg_dict["train-started"] = True
          json_write(cfg_dict, json_cfg_filename)
          proc = subprocess.Popen(
              cmds[exe_cmds + skip_cmds],
              cwd=_cwds[-1],
              stdin=stdinfds[-1],
              stdout=stdoutfds[-1],
              stderr=stderrfds[-1],
              shell=True)
        else:
          stdoutfds.append(open(os.path.join(_cwds[-1], "stdout"), "a"))
          stderrfds.append(open(os.path.join(_cwds[-1], "stderr"), "a"))
          stdinfds.append(open(os.path.join(_cwds[-1], "stdin"), "r"))
          _cmd = "{} {}".format(cmds[exe_cmds + skip_cmds], resume_option)
          proc = subprocess.Popen(
              _cmd,
              cwd=_cwds[-1],
              stdin=stdinfds[-1],
              stdout=stdoutfds[-1],
              stderr=stderrfds[-1],
              shell=True)
        yield proc
        procs.append(proc)
        exe_cmds += 1
      for proc in procs:
        if proc.poll() != None:
          pidx = procs.index(proc)
          stdoutfds[pidx].close()
          stderrfds[pidx].close()
          stdinfds[pidx].close()
          stdoutfds.pop(pidx)
          stderrfds.pop(pidx)
          stdinfds.pop(pidx)
          procs.pop(pidx)
          cfg_path = os.path.join(_cwds[pidx], "config.json")
          cfg_dict = json_read(cfg_path)
          cfg_dict["train-ended"] = True
          json_write(cfg_dict, cfg_path)
      time.sleep(sleep)
    else:
      skip_cmds += 1
