import subprocess

import time
import os

from typing import Optional
from utils import *


def prepare_training(config_filepath, **args):
  cfg = json_read(config_filepath)
  cmds_nmbr = len(cfg["args"])
  rawoptionslist = gen_rawoptionslist(cfg)
  rootdir = "{}-{}".format(cfg["root"], int(time.time()))
  cwds = randsubdirs(rootdir=rootdir, size=cmds_nmbr, **args)
  for cwd in cwds:
    path = os.path.join(os.getcwd(), cwd)
    if not os.path.exists(path):
      os.makedirs(path)
  return (cfg, rawoptionslist, cwds)


def train_jobspoll(config_path: str="debugnn_config.json", executable: str="python", **args):
  cfg, rawoptionslist, cwds = prepare_training(config_path, **args)
  dictoptionslist = get_dictoptionslist(rawoptionslist)
  cmd_prefix = "{} {}".format(executable, os.path.join(os.getcwd(), cfg["filename"]))
  cmds = prepend_prefix(rawoptionslist, prefix=cmd_prefix)
  poll = run_jobspoll(cmds=cmds, cwds=cwds, dictoptionslist=dictoptionslist, num_workers=cfg["num_workers"], shell=True, **args)

  procs = []
  for i, proc in enumerate(poll):
    procs.append(proc)

  while True:
    all_terminated = True
    for i in range(len(procs)):
      if procs[i].poll() == None:
        all_terminated = False

    if all_terminated:
      break
    time.sleep(10)

def run_jobspoll(cmds: list[str], cwds: list[str], dictoptionslist: list[dict], num_workers: int=4, sleep: float=10, test: bool=False, cfg_filename: str="config.json", **args):
  stdinfds, stdoutfds, stderrfds = [], [], []
  procs, exe_cmds = [], 0
  while exe_cmds < len(cmds) or len(procs) > 0:
    if len(procs) < num_workers and exe_cmds < len(cmds):
      if not test:
        stdoutfds.append(open(os.path.join(cwds[exe_cmds], "stdout"), "wa"))
        stderrfds.append(open(os.path.join(cwds[exe_cmds], "stderr"), "wa"))
        stdinfds.append(open(os.path.join(cwds[exe_cmds], "stdin"), "x"))
        json_cfg_filename = os.path.join(cwds[exe_cmds], cfg_filename)
        json_write(dictoptionslist[exe_cmds], json_cfg_filename)
        proc = subprocess.Popen(
            cmds[exe_cmds],
            cwd=cwds[exe_cmds],
            stdin=stdinfds[-1],
            stdout=stdoutfds[-1],
            stderr=stderrfds[-1], **args)
      else:
        proc = subprocess.Popen(
            cmds[exe_cmds],
            cwd=cwds[exe_cmds], **args)
      yield proc
      procs.append(proc)
      exe_cmds += 1
    for proc in procs:
      if proc.poll():
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
        procs.remove(proc)
    time.sleep(sleep)
