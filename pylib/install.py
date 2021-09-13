#!/usr/bin/env python3

import os,shlex,stat,sys,time
from functools import reduce

# Let me call "run('some command with arguments',stdout=PIPE,stderr=PIPE)".
from subprocess import run,DEVNULL,PIPE,STDOUT

# We need a couple of maps between Unix file modes and Python file modes.
unix_mode_to_python={
  0o4000:stat.S_ISUID,
  0o2000:stat.S_ISGID,
  0o1000:stat.S_ISVTX,
  0o200:stat.S_IWUSR,
  0o100:stat.S_IXUSR,
  0o040:stat.S_IRGRP,
  0o020:stat.S_IWGRP,
  0o010:stat.S_IXGRP,
  0o004:stat.S_IROTH,
  0o002:stat.S_IWOTH,
  0o001:stat.S_IXOTH,
}

python_mode_to_unix={v:k for k,v in unix_mode_to_python.items()}

def u2p_mode(mode):
  "Converto mode from the Unix shell world to the Python world."

  return reduce(
    (lambda accumulator,bit: accumulator | unix_mode_to_python[bit]),
    [2**b for b in range(12)], # First 12 single-1-bit values.
    0                          # Our initializer.
  )

def p2u_mode(mode):
  "Converto mode from the Python world to the Unix shell world."

  return reduce(
    (lambda accumulator,bit: accumulator | python_mode_to_unix[bit]),
    [
      stat.S_ISUID,
      stat.S_ISGID,
      stat.S_ISVTX,
      stat.S_IWUSR,
      stat.S_IXUSR,
      stat.S_IRGRP,
      stat.S_IWGRP,
      stat.S_IXGRP,
      stat.S_IROTH,
      stat.S_IWOTH,
      stat.S_IXOTH,
    ],
    0
  )

def chmod(path,mode,dir_fd=None,follow_symlinks=True):
  """Just like os.chmod, but mode is the a simple integer whose bits 
  match those of a Linux shell's chmod command.

  [The text below was stolen from some man page, which was likely stolen
  from some other man page, and so on.]

  4000  (the setuid bit). Executable files with this bit set will run
        with effective uid set to the uid of the file owner. Directories
        with this bit set will force all files and sub-directories
        created in them to be owned by the directory owner and not by
        the uid of the creating process, if the underlying file system
        supports this feature: see chmod(2) and the suiddir option to
        mount(8).
  2000  (the setgid bit). Executable files with this bit set will run
        with effective gid set to the gid of the file owner.
  1000  (the sticky bit). See chmod(2) and sticky(7).
  0400  Allow read by owner.
  0200  Allow write by owner.
  0100  For files, allow execution by owner. For directories, allow the
        owner to search in the directory.
  0040  Allow read by group members.
  0020  Allow write by group members.
  0010  For files, allow execution by group members. For directories,
        allow group members to search in the directory.
  0004  Allow read by others.
  0002  Allow write by others.
  0001  For files, allow execution by others. For directories allow
        others to search in the directory."""

  os.chmod(path,u2p_mode(mode),dir_fd=dir_fd,follow_symlinks=follow_simlinks)

def getmod(path,dir_fd=None,follow_symlinks=True):
  "Return the Unix shell version of fthe given files's mode."

  return p2u_mode(os.stat(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks).st_mode)

class Builder(object):
  "Instances of builder know how to build targets from source."

  def __init__(self,command):
    """Instantiate this Builder object with the command it will use to
    build targets from source files."""

    self.command=command

  def build(self,sources,output,options=None,verbose=False):
    "Run our build command on our sources to produce out output."

    # Make sure our sources argument is a sequence.
    if isinstance(sources,str):
      sources=shlex.split(sources)
    elif not isinstance(sources,(list,tuple)):
      sources=[sources]

    # Make sure any Target instances among our sources are up to date.
    for s in sources:
      if isinstance(s,Target):
        s.build()

    # Continue only if any of our sources is newer than our target file.
    if os.path.exists(output):
      t_target=os.stat(output).st_mtime
      if not [1 for s in sources if os.stat(str(s)).st_mtime<t_target]:
        if verbose:
          print(f"Target is up to date: {output}")
        return 0 # Nothing to do, and all is well.

    # So we're running the command.
    if isinstance(sources,(list,tuple)):
      sources=shlex.join(sources)
    elif not isinstance(sources,str):
      sources=str(sources)
    if not isinstance(output,str):
      output=str(output)
    if not isinstance(options,str):
      options=str(options)
    cmd=self.command.format(sources=sources,output=output,options=options)

    if verbose:
      arg_input=f"{len(input)} characters" if isinstance(input,(str,bytes)) else str(input)
      arg_stdin='PIPE' if stdin==PIPE else 'STDOUT' if stdin==STDOUT else 'DEVNULL' if stdin==DEVNULL else str(stdin)
      arg_stdout='PIPE' if stdout==PIPE else 'STDOUT' if stdout==STDOUT else 'DEVNULL' if stdout==DEVNULL else str(stdin)
      arg_stderr='PIPE' if stderr==PIPE else 'STDOUT' if stderr==STDOUT else 'DEVNULL' if stderr==DEVNULL else str(stdin)
      print(f"""{cmd}
    input: {arg_input}
    stdin: {arg_stdin}
    stdout: {arg_stdout}
    stderr: {arg_stderr}
    ... running ...""")
      t0=time.time()
    proc=run(self.cmd.format(sources=sources,output=output,options=options))
    if verbose:
      t=time.time()
      arg_stdout='None' if proc.stdout is None else f"{len(proc.stdout)} characters"
      arg_stderr='None' if proc.stderr is None else f"{len(proc.stderr)} characters"
      print(f"""\
    elapsed: {t-t0:0.3f} seconds
    return code: {proc.returncode}
    stdout: {arg_stdout}
    stderr: {arg_stderr}""")

    if proc.stdout:
      print(proc.stdout)

    if proc.returncode or pro.stderr:
      print(f"Error {pro.returncode} on target {output}",file=sys.stderr)
      if proc.stderr:
        print(proc.stderror,file=sys.stderr)

    return proc.returncode

class Target(object):
  "This is a single file (with possible symlinks) to be installed."

  def __init__(self,source,destination,mode=None,symlinks=None,dependencies=None,build_with=None):
    self.source=source
    self.destination=destination
    self.mode=mode
    self.symnlinks=symnlinks
    self.dependencies=dependencies
    self.build_with=build_with

    if self.mode is None:
      self.mode=getmod(source)

  def __str__(self):
    return self.destination

