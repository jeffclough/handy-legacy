#!/usr/bin/env python3

"""

Facilitate installing, building (if necessary), and installing
executables.

"""

#__all__=[
#  'Command',
#  'Copy',
#  'Error',
#  'TargetHandler',
#  'V',
#  'options',
#  'dir_mode',
#  'DEVNULL',
#  'PIPE',
#  'STDOUT',
#]

import os,re,shlex,shutil,stat,sys,time
from abc import ABC,abstractmethod
from enum import Flag,auto
from functools import reduce
from subprocess import run,DEVNULL,PIPE,STDOUT,CompletedProcess

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

class Options(object):
  def __init__(self):
    self.dryrun=False
    self.force=False
    self.tdir='~/my'
    self.verb=V.OPS

  def __str__(self):
    return f"dryrun={self.dryrun}, force={self.force}, tdir={self.tdir!r} verb={self.verb}"

  def verbFlags(self):
    return str(self.verb)[2:].lower().replace('|','+')

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

def expand_all(filename):
  "Return the filename with ~ and environment variables expanded."

  p=os.path.expandvars(os.path.expanduser(filename))
  if options.verb & V.DEBUG:
    print(f"expand_all({filename!r}) -> {p!r}")
  return p

def filetime(filename,default=0):
  """Return the modification time of the given file in floating point
  epoch seconds. If the file does not exist, return the default value
  (presumably something that represents this file to be VERY old)."""

  try:
    default=os.path.getmtime(filename)
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

  if not os.path.exists(target):
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
    elif not os.path.exists(d):
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

class TargetHandler(ABC):
  """TargetHandler is an abstract base class of classes that know how to
  produce a target file from one or more sources. Tilde- or variable-
  expansion is performed on the target filespec if called for.

  See the Copy class for examples."""

  def __init__(self,target):
    self.target=os.fspath(target) # The file (or symlink) to be created.
    self.perms=None   # Set this with the mode(perms) method.
    self.deps=None    # Set this with the dependsOn(...) method.
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
    
    if args:
      self.deps=args
    else:
      self.deps=None
    return self

  def expand(self):
    "Expand any ~ or $VAR substrings in this target's filename."

    self.target=expand_all(self.target)
    return self

  def owner(self,user=None,group=None):
    "Set the desired owner and/or group of the target."

    if user is not None:
      self.user=user if user else None
    if group:
      self.group=group if group else None
    return self

  def mode(self,perms):
    "Set the permissions of our target file."

    self.perms=perms
    return self

  @abstractmethod
  def __call__(self):
    """Build this target from its dependencies. This method MUST be
    implemented in a subclass."""

    pass

class Folder(TargetHandler):
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

  Example: Same as above, but specify a mode of 0o750.

    Folder('~/my/bin').mode(0o750)()

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

    if os.path.exists(self.target):
      if not os.path.isdir(self.target):
        raise Error(f"Cannot create directory {self.target!r} because it already exists as something else.")
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

class Copy(TargetHandler):
  """Instances of Copy know how to copy a source file to a destination.
  Use Copy(target).as_sysmlink() to configure the Copy instance to
  create a symlink instead of copying the source to the target.

  Instances of Copy must be given exactly one source file (using the
  dependsOn() method).

  Example: Copy file named by src to file named by targ.

    Copy(targ).dependsOn(src)()

  Example: Copy src to targ, setting the mode to 750 and user and
  group ownership to root and wheel, respectively.

    Copy(targ).dependsOn(src).mode(0o750).owner(user='root',group='wheel')()

  Example: Create a symlink to src at targ.

    Copy(targ).dependsOn(src).as_symlink()()
  """

  def __init__(self,target):
    super().__init__(target)
    self.symlink=False  # Change this with the as_symlink() method.

  def as_symlink(self):
    "Configure this target to create a symlink to the its source file."

    self.symlink=True
    return self

  def __call__(self):
    "Perform the copy operation by calling this Copy instance directly."

    # Make sure we have exactly one source file.
    if len(self.deps)!=1:
      raise Error(f"""Class {self.__class__.__name__} MUST have exactly one source file (not {self.deps!r}).""")

    # Get the source file.
    source=self.deps[0]
    if isinstance(source,TargetHandler):
      # Make sure this target is ready to be coppied or linked to.
      source()

    if os.path.isdir(self.target):
      # Compute our actual target path.
      self.target=os.path.join(self.target,os.path.basename(source))

    if self.symlink:
      if os.path.is_symlink(self.target):
        if os.path.abspath(source)!=os.path.realpath(self.target):
          if not options.dryrun:
            os.symlink(source,self.target)
            if options.verb & V.OPS:
              print(f"{source} <-- {self.target}")
    else:
      # Copy source to target, keeping as much metadata as possible.
      if is_newer(source,self.target):
        if options.verb & V.OPS:
          print(f"{source} ==> {self.target}")
        if not options.dryrun:
          # Copy the file.
          self.target=shutil.copy2(source,self.target,follow_symlinks=False)
          # Set the user and or group ownership if this instance is so configured.
          if self.user or self.group:
            shutil.chown(self.target,user=self.user,group=self.group)

    return self

class Command(object):
  def __init__(self,cmd,input=None,stdin=None,stdout=None,stderr=None):
    "Initialize this Command instance."

    self.cmd=cmd
    self.input=input
    self.stdin=stdin
    self.stdout=stdout
    self.strerr=stderr
    self.result=None

  def __call__(self):
    """Run the command the caller has set up. Return this Command
    instance."""

    if options.verb & V.OPS:
      print(cmd)
    if options.dryrun:
      # Put together a "fake" CompletedProcess result with a return code of 0
      # and empty stdout and stderr values.
      self.result=CompletedProcess(shlex.split(cmd),0,"","")
    else:
      # Run our command, capturing it stdout and stderr output as string values.
      r=self.result=run(self.cmd,text=True,stdin=self.stdin,stdout=self.stdout,stderr=self.stderr)
    if r.returncode or options.verb & V.OPS:
      if r.stdout: print(r.stdout)
      if r.stderr: print(r.stderr,file=sys.stderr)
      if r.returncode:
        raise Error(f"Non-zero return code ({r.returncode}): {self.cmd}")
    return self

if __name__=='__main__':
  import argparse,atexit,platform

  # Regardless of how this code terminates, put the PWD back like we found it.
  atexit.register(os.chdir,os.getcwd())
  # But for now, use this program's directory as the default.
  os.chdir(os.path.dirname(sys.argv[0]))

  ap=argparse.ArgumentParser(
    #formatter_class=argparse.RawDescriptionHelpFormatter,
    description=f"""\
Install the "handy" scripts to the given (with --dir) or default ({options.tdir}) base directory.
 
The --verbosity (-v) flags are any of quiet, ops, deps, time, and debug. The "quiet" flags turns all the others off. Flags can be combined joined with + or - characters to add or remove those flags. The first flag listed is assumed to be added unless preceded by -. There are no spaces in --verbosity's value.
"""
  )
  ap.add_argument('--dir',dest='tdir',action='store',type=expand_all,default=options.tdir,help="Set the base of the target directory structure. Subdirectories like bin, doc, etc, include, lib, man, and sbin will be created here if and when needed. (default: %(default)r)")
  ap.add_argument('--force',action='store_true',help="Rather than comparing the timestamps of source and target files, copy the former to the latter unconditionally.")
  ap.add_argument('--dryrun','-n',action='store_true',help="Go through all the motions, but don't do any work.")
  ap.add_argument('--test',action='store_true',help="Run internal tests, report the results, and terminate.")
  ap.add_argument('-v','--verbosity',action='store',default=options.verbFlags(),help="""Verbosity flags. See description text above for details. (default: %(default)r)""")
  ap.add_argument('--debugger',action='store_true',help="Engage pdb within this script once we get through the setup. This is not for the uninitiated. See https://docs.python.org/3/library/pdb.html#debugger-commands for a command summary.")
  ap.add_argument('files',metavar='FILE',action='store',nargs='*',help="This is one of more files to be installed.")
  opt=ap.parse_args()

  # Parse our verbosity flags first.
  options.verb=parse_verbosity(opt.verbosity)

  # Update our Options instance (options) with our command line option values.
  options.dryrun=opt.dryrun
  options.force=opt.force
  options.tdir=opt.tdir

  if options.verb & V.DEBUG:
    print(f"options: {options}")

  if opt.debugger:
    import pdb
    pdb.set_trace()

  if opt.test:
    import doctest

    def test_mode_conversion():
      """
      >>> stat_mode(0o700)==stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR
      True
      >>> stat_mode(0o070)==stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP
      True
      >>> stat_mode(0o007)==stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
      True
      >>> shell_mode(stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)==0o700
      True
      >>> shell_mode(stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP)==0o070
      True
      >>> shell_mode(stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH)==0o007
      True
      >>> dir_mode(0o640)==0o750
      True
      >>> dir_mode(0o400)==0o500
      True
      """

      pass

    failed,total=doctest.testmod()
    if failed:
      print(f"Failed {failed} of {total} tests.")
      sys.exit(1)
    print(f"Passed all {total} tests!")
    sys.exit(0)

  mac_scripts=[
    'alex',
  ]
  scripts=[
    'ad-userAccountControl',
    'ansi',
    'args',
    'ascii',
    'backup-volume',
    'base',
    'base16',
    'base32',
    'base64',
    'beyondpod',
    'certmon',
    'chronorename',
    'columnate',
    'csv',
    'datecycle',
    'decode16',
    'decode32',
    'decode64',
    'dump',
    'encode16',
    'encode32',
    'encode64',
    'factors',
    'fib',
    'freq',
    'gensig',
    'ind',
    'ip2host',
    'json',
    'json2csv',
    'keeplast',
    'ldif',
    'mark',
    'mazer',
    'mix',
    'names',
    'not',
    'now',
    'numlines',
    'patch-cal',
    'pg',
    'ph',
    'portname',
    'pretty-json',
    'prime',
    'progress',
    'pwgen',
    'pygrep',
    'randword',
    're',
    'reduce',
    'secdel',
    'slice',
    'strftime',
    'strptime',
    'timeout',
    'timeshift',
    'title-case',
    'tread',
    'ts',
  ]

  Folder(options.tdir).expand()
  bin_dir=Folder(os.path.join(options.tdir,'bin'))()
  Folder(os.path.join(options.tdir,'etc'))()
  Folder(os.path.join(options.tdir,'include'))()
  Folder(os.path.join(options.tdir,'lib'))()
  Folder(os.path.join(options.tdir,'lib','python'))()

  Copy(os.path.join(bin_dir,'mark')).dependsOn('mark')()

  #if platform.system()=="Darwin":
  #  for s in mac_script:
  #    Copy(
  #for s in scripts:
  #  Copy(s).to('bin').dependsOn(s)()
