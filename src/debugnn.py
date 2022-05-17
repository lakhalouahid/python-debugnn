import subprocess
import json
import time
import copy
import os
import random, string



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
    cmd = "{} {} {}".format(prefix, jcfg['filename'], dargs)
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
      proc = subprocess.Popen(cmds[ecmds], cwd=cwds[ecmds], stdout=fds[-1], stderr=subprocess.DEVNULL, **args)
      yield proc
      procs.append(proc)
      ecmds += 1
    for proc in procs:
      if proc.poll() != None:
        del fds[procs.index(proc)]
        procs.remove(proc)
    time.sleep(sleep)
