#!/usr/bin/env python3

"""

Facilitate installing, building (if necessary), and installing
executables.

"""

__all__=[
  'DEVNULL',
  'PIPE',
  'STDOUT',
  'Command',
  'Error',
  'Path',
  'Target',
  'File',
  'Folder',
  'Path',
  'V',
  'dc',
  'dir_mode',
  'expand_all',
  'parse_verbosity',
  'platform',
  'options',
]

import os,platform,re,shlex,shutil,stat,sys,time
from enum import Flag,auto
from functools import reduce
from subprocess import run,DEVNULL,PIPE,STDOUT,CompletedProcess
from path import Path
from debug import DebugChannel

dc=DebugChannel(
  False,
  sys.stdout,
  fmt="{label}: {basename}:{line} {function}: {indent}{message}\n"
)

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Some constants and configuration variables.

# These verbosity flag values can be combined bitwise in any
# combination in an instance of V.
class V(Flag):
  QUIET=0       # A value that turns all the others off.
  OPS=auto()    # Print file operations we perform.
  DEPS=auto()   # Print dependency logic.
  TIME=auto()   # Print time comparison logic.
  DEBUG=auto()  # Print debug statements.
  FULL=OPS|DEPS|TIME|DEBUG # Way too much!

# These options configure this module's behavior.
class Options(object):
  def __init__(self):
    self.dryrun=False
    self.force=False
    self.tdir=Path('~/my').expandUser()
    self.sdir=Path(sys.argv[0]).dirName().absolute()
    self.verb=V.OPS

  def __str__(self):
    return f"dryrun={self.dryrun}, force={self.force}, sdir={self.sdir!r} tdir={self.tdir!r} verb={self.verb}"

  def verbFlags(self):
    return str(self.verb)[2:].lower().replace('|','+')

# Store some system characteristics.
platform=type('',(),dict(
  arch=platform.machine(),          # 'arm64'
  os=platform.platform(),           # 'macOS-12.6-arm64-arm-64bit'
  system=platform.system(),         # 'Darwin'
  release=platform.uname().release  # '21.6.0'
))

def parse_verbosity(flags):
  """Given a verbosity flags string value, return the corresponding
  options.V value."""

  verb=V.QUIET
  for f in re.findall(r"[-+]?\w+",flags):
    # Figure out what this flag is and what we're doing with it.
    if f[0] in '-+':
      op=f[0]
      f=f[1:]
    else:
      op='+'
    if f=='quiet': v=V.QUIET
    elif f=='ops': v=V.OPS
    elif f=='deps': v=V.DEPS
    elif f=='time': v=V.TIME
    elif f=='debug': v=V.DEBUG
    elif f=='full': v=V.FULL
    else:
      raise ValueError(f"Unrecognized flag {f!r} in {flags!r}.")
    # Either add or subtract the flag v in verb's value.
    if op=='+':
      verb|=v
    else:
      verb&=~v
  # Return the caller's verbosity flags as a V value.
  return verb

options=Options()
#print(f"options: {str(options)}")

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This is this module's main exception type.

class Error(Exception):
  pass

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Some general utility functions.

#def chdir(path):
#  """Chage to the given directory, and return he previous current
#  directory."""
#
#  prev=os.getcwd()
#  os.chdir(path)
#  return prev

def expand_all(filename):
  "Return the filename with ~ and environment variables expanded."

  p=os.path.expandvars(os.path.expanduser(str(filename)))
  dc(f"expand_all({filename!r}) -> {p!r}")
  return p

def filetime(filename,default=0):
  """Return the modification time of the given file in floating point
  epoch seconds. If the file does not exist, return the default value
  (presumably something that represents this file to be VERY old)."""

  try:
    default=os.path.getmtime(str(filename))
    if options.verb & V.TIME:
      print(f"  {filename}\tt={default:0.6f} ({time.strftime('%Y-%m-%d %H:%M:%S.%f',time.localtime(default))})")
  except:
    pass
  return default

def is_newer(src,dst,bias=-0.001):
  """Return true if src names a file that is newer than the file dst
  names (or if dst doesn't exist).

  For the sake of out_of_date()'s efficiency, the dst argument may be a
  (string,float) tuple rather than a string, in which case, the string
  is the name of the file, and the float is its timestamp value.

  The bias argument is the number of seconds to add to the source time
  in order to bias comparison with the time of the destination file. It
  defaults to -0.001 seconds (-1 miliseconds) to avoid needless file
  copies on some operating systems. (I'm looking at you, macOS.)"""

  src=os.fspath(src)
  dst=os.fspath(dst)
  ts=filetime(src,1)+bias
  if isinstance(dst,tuple):
    dst,td=dst
  else:
    td=filetime(dst)
  if options.verb & V.TIME:
    rel='newer' if ts>td else 'older'
    print(f"  {src} is {rel} than {dst}")
  return options.force or (ts>td)

def out_of_date(target,*deps):
  """Return True if any of the other filename arguments identifies a
  file with a later modification time than target. The "deps" arguments
  can be either filenames or lists or tuples of fileanmes."""

  if not target.exists():
    if options.verb & V.DEPS:
      print(f"  {target} is out of date because it's missing.")
    return True

  if options.force:
    if options.verb & V.DEPS:
      print(f"  {target} is being forced out of date.")
    return True

  t=filetime(target)

  for d in deps:
    if isinstance(d,(list,tuple)):
      if outOfDate(target,*d):
        return True
    elif not d.exists():
      # Return True for a non-existant dependency to provoke an error
      # when that file isn't found.
      if options.verb & V_DEPS:
        print(f"  {target} depends on {d}, which is missing.")
      return True
    elif is_newer(d,(target,t)):
      if options.verb & V_DEPS:
        print(f"  {target} depends on {d}, which is newer.")
      return True
  return False

def expand_wildcards(filespec):
  """Return a list of all the files matching filespec. If there is no
  such file, return a list with only the filespec in it."""

  files=glob(filespec)
  if not files:
    files=[filespec]
  return files

def dir_mode(file_mode):
  """Given a file mode (of the shell variety), return a mode value
  appropriate for creating a directory to hold such a file. For instance,
  dir_mode(0o640) will return 0o750. The idea is to enable directory
  searching for every permission group with read or write access."""

  # Yes, I could have used a loop, but isn't this easier to read?
  m=file_mode
  if m & 0o600: m|=0o100
  if m & 0o060: m|=0o010
  if m & 0o006: m|=0o001 
  return m

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# File permission mode values used by Unix shell commands (rwxrwxrwx) are not
# necessarily the same values used by the stat structure, though it seems they
# often are. So use stat_mode() to convert from a Unix shell mode value like
# 0o600 to (stat.S_IRUSR | stat.S_IWUSR). It's a little like the ntohs() and
# htons() network functions. You might get by without them if you're on a
# big-endian platform Linux, but it's much safer to use them.
#
# There's also a stat_mode() function to convert mode values in the other
# direction.

# We need a couple of maps between Unix file modes and stat file modes.
shell_to_stat_values={
  0o4000:stat.S_ISUID,
  0o2000:stat.S_ISGID,
  0o1000:stat.S_ISVTX,
  0o400:stat.S_IRUSR,
  0o200:stat.S_IWUSR,
  0o100:stat.S_IXUSR,
  0o040:stat.S_IRGRP,
  0o020:stat.S_IWGRP,
  0o010:stat.S_IXGRP,
  0o004:stat.S_IROTH,
  0o002:stat.S_IWOTH,
  0o001:stat.S_IXOTH,
}

# This is the reverse look-up dictionary. If you have some bitwise
# combination of stats.I[RWX](USR|GRP|OTH) values, this map will give
# you the equivalent Unix shell numeric permssion value.
stat_to_shell_values={v:k for k,v in shell_to_stat_values.items()}

def stat_mode(mode):
  "Converto mode from the Unix shell world to the stat world."

  return reduce(
    (lambda accumulator,bit: accumulator | shell_to_stat_values[bit]),
    [n for n in shell_to_stat_values.keys() if n & mode],
    0
  )

def shell_mode(mode):
  "Convert mode from the stat world to the Unix shell world."

  return reduce(
    (lambda accumulator,bit: accumulator | stat_to_shell_values[bit]),
    [n for n in stat_to_shell_values.keys() if n & mode],
    0
  )

def chmod(path,mode,dir_fd=None,follow_symlinks=True):
  """Just like os.chmod, but mode is the a simple integer whose bits 
  match those of a Linux shell's chmod command. Be sure to use proper
  octal notation (0o755) if when calling this function.

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

  os.chmod(path,stat_mode(mode),dir_fd=dir_fd,follow_symlinks=follow_simlinks)

def getmod(path,dir_fd=None,follow_symlinks=True):
  """Return the Unix shell mode of the given file (which might be a
  directory. From os.stat ...

  Get the status of a file or a file descriptor. Perform the equivalent
  of a stat() system call on the given path. path may be specified as
  either a string or bytes – directly or indirectly through the PathLike
  interface – or as an open file descriptor. Return a stat_result
  object.

  This function normally follows symlinks; to stat a symlink add the
  argument follow_symlinks=False."""

  return shell_mode(os.stat(path,dir_fd=dir_fd,follow_symlinks=follow_symlinks).st_mode)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Command(object):
  def __init__(self,cmd,stdin=None,stdout=None,stderr=None,quiet=False):
    "Initialize this Command instance."

    if isinstance(cmd,str):
      self.cmd=shlex.split(cmd)
    elif isinstance(cmd,(list,tuple)):
      self.cmd=list(cmd)
    else:
      raise ValueError(f"Command must be a string or sequence, not {cmd!r}.")
    self.stdin=stdin
    self.stdout=stdout
    self.stderr=stderr
    self.result=None
    self.quiet=quiet

  def __call__(self,*args,quiet=None):
    """Run the command the caller has set up. Return this Command
    instance."""

    if quiet is None:
      quiet=self.quiet

    if isinstance(args,str):
      # Convert this string to an args list.
      args=shlex.split(args)
    elif isinstance(args,(list,tuple)):
      args=list(args)
    else:
      raise ValueError(f"Command arguments must be a string or sequence, not {args!r}.")
    if options.verb & V.OPS and not quiet:
      print(shlex.join(self.cmd+args))
    if options.dryrun:
      # Put together a "fake" CompletedProcess result with a return code of 0
      # and empty stdout and stderr values.
      r=CompletedProcess(self.cmd+args,0,"","")
    else:
      # Run our command, capturing it stdout and stderr output as string values.
      dc(f"run({self.cmd+args},text=True,stdin={self.stdin},stdout={self.stdout},stderr={self.stderr})")
      r=run(self.cmd+args,text=True,stdin=self.stdin,stdout=self.stdout,stderr=self.stderr)
    self.result=r.returncode
    self.stdout=r.stdout
    self.stderr=r.stderr
    if self.result or (options.verb & V.OPS and not quiet):
      if self.stdout: print(self.stdout)
      if self.stderr: print(self.stderr,file=sys.stderr)
      if self.result:
        raise Error(f"Non-zero return code ({self.result}): {shlex.join(self.cmd+args)}")
    return self

class Target(object):
  """Target is an abstract base class of classes that know how to
  produce a target file from one or more sources. Tilde- or variable-
  expansion is performed on the target filespec if called for.

  See the File class for examples."""

  def __init__(self,target):
    # Remember the file to be created.
    if not isinstance(target,Path):
      target=Path(target)
    if target.isAbs():
      self.target=target
    else:
      self.target=options.tdir/target
    self.target=self.target.normal()
    self.mode=None   # Set this with the mode(perms) method.
    self.deps=[]     # Set this with the dependsOn(...) method.
    # If setting both owner and group, you MAY do so with a single call to the
    # owner(user='someone',group='some_group') method.
    self.user=None    # Set this with the owner(user='some_account') method.
    self.group=None   # Set this with the owner(group='some_group') method.

  def __fspath__(self):
    "Return the string version of this target."

    return self.target

  def __str__(self):
    "Return the string version of this target."

    return self.target

  def dependsOn(self,*args):
    "Configure one or more source files for our target."
    
    self.deps.extend([
      x if isinstance(x,(Target,Path)) else Path(x) for x in args
    ])
    return self

  def expand(self):
    "Expand any ~ or $VAR substrings in this target's filename."

    self.target=self.target.expandAll()
    return self

  def owner(self,user=None,group=None):
    "Set the desired owner and/or group of the target."

    if user is not None:
      self.user=user if user else None
    if group:
      self.group=group if group else None
    return self

  def chmod(self,mode):
    """Set the permissions of our target file. It's simplest to use
    octal for the mode number, just like you'd do with the chmod command
    from a shell prompt. For example:

        target.chmod(0o755)"""

    self.mode=mode
    return self

  def __call__(self):
    """Create this target from its dependencies. This method MUST be
    implemented in each instantiable subclass."""

    # In theis base class, we ensure all dependencies are up to date.
    # It's up to the subclass to build the target.
    for d in self.deps:
      if isinstance(d,Target):
        d()

    return self

class File(Target):
  """An instance of File is ... a filename."""

  def __init__(self,target):
    """Set the filename of this File object's target file."""

    super().__init__(target)
    self.source=None
    self.links=[]
    self.force_links=False
    self.follow=False

  def __call__(self):
    """After making sure all our dependencies are up to date, perform any
    copy and/or symlink operations the caller has set up for this File
    object. Return a reference to this File object."""

    # Target.__call__() handles any dependencies.
    super().__call__()

    if self.source:
      # Copy our source file to our target file.
      if is_newer(self.source,self.target):
        if options.verb & V.OPS:
          print(f"{self.source} ==> {self.target}")
        if not options.dryrun:
          # Copy the file.
          self.target=shutil.copy2(self.source,self.target,follow_symlinks=self.follow)
          # Set the user and or group ownership if this instance is so configured.
          if self.user or self.group:
            shutil.chown(self.target,user=self.user,group=self.group)

    if self.links:
      # Because we do our best to create relative symlinks, we have to change
      # the current current directory to where the link will be created and
      # then create using the relative path to our target.

      org_dir=Path.getCwd()
      try:
        for l in self.links:
          # Preparation ...
          org_dir.chdir() # We have to start in with our original CWD.
          ldir,lfile=l.absolute().split(-1)
          ldir.chdir()    # Now we switch to the link's directory.
          t=self.target.relative() # This is our relative link.
          # Execution ...
          if lfile.isLink() and lfile.real()==self.target:
            continue
          if l.exists() and not l.isDir() and self.force_links:
            if options.verb & V.OPS: print(f"rm {l}")
            if not options.dryrun: l.remove()
          if not l.exists():
            if options.verb & V.OPS: print(f"{l} --> {t}")
            if not options.dryrun: os.symlink(t,l)
      finally:
        # TODO: Make Path.getCwD and Path.chdir() viable Python context
        # managers so we can get away from the try ... finally pattern.
        org_dir.chdir()   # Restore our original CWD.

    return self

  def link(self,*args,link_dir=None,force=None):
    """Prepare to create one or more symlinks (args_ to this target
    file. Non-absolute paths are relative to link_dir if given, or our
    target's directory otherwise.

    The force argument defaults to None but is interpreted as boolean if
    it's anything else. Normally, symlinks won't replace an existing
    file or simlink, but force=True means the new symlink will be
    creeated unless it already exists as a symlink and points to this
    File object's target.

    The link(s) won't be created until this File instance is called. The
    link(...) method just sets things up.

    Return a reference to this File object."""

    self.links.extend([
      x if isinstance(x,(Path,Target)) else Path(x) for x in args
    ])
    if link_dir:
      self.link_dir=link_dir
    if force is not None:
      self.force_links=force
    return self

  def copy(self,source,follow=False):
    """Prepare to copy the source file to our target file. Non-absolute
    paths in links are relative to the path in install.options.sdir,
    which is initially set to the directory the installer script is in.
    The source file also becomes this target's sole dependency.

    The copy will not be performed until this File instance is called.

    Return a referece to this File object."""

    s=source if isinstance(source,(Path,Target)) else Path(source)
    if not s.isAbs():
      s=(options.sdir/s).normal()
    self.deps=[s] # Make sure our source file is a dependency.
    self.source=s
    self.follow=follow
    return self

class Folder(Target):
  """A Folder instance will create a given directory if doesn't already
  exist, createting any missing intermediate directories along the way,
  or it will raise an exception if it already exists as something other
  than a directory. (It does follow symlinks.) The default mode of the
  new directory is 0o755.

  Tilde- and variable-expansion are performed on the name of the path
  first.

  Example: Make sure our target folder exists before attempting to
  install files there.

    Folder('~/my/bin')() # Configure and create in one step.

  Example: Same as above, but also set rwxr-x--- file permissions.

    Folder('~/my/bin').chmod(0o750)()

  Example: Create a directory and get the expanded path to the created
  (or existing) directory.

    libs=Folder('~/my/lib') # Set up the folder we need.
    print(f"Making sure {libs.target} exists ...")
    libs() # You have to "call" this Folder instance to do the work.
  """

  def __init__(self,target):
    super().__init__(target)
    self.mode=0o755

  def __call__(self):
    "Create any missing parts of our directory."

    super().__call__()

    if self.target.exists():
      if not self.target.isDir():
        raise Error(f"Cannot create directory {self} because it already exists as something else.")
    else:
      # Oddly, os.mkdirs() uses the umask to set permissions on any intermediate
      # directories it creates. It uses its mode parameter only when creating
      # the leaf directory.
      if options.verb & V.OPS:
        print(f"mkdir {self.target}")
      if not options.dryrun:
        orig_umask=os.umask(stat_mode(self.mode^0o777))
        os.makedirs(self.target,mode=stat_mode(self.mode))
        os.umask(orig_umask)

    return self

  def __str__(self):
    """Return the name of the directory this Folder instance creates,
    whether it's already done so, or wether it's even possible to create
    that directory."""

    return self.target

  def __repr__(self):
    return f"{self.__class__.__name__}({repr(self.target)})"

  def __truediv__(self,other):
    """Return a filesystem path joining this target and the other."""

    return self.target/other
