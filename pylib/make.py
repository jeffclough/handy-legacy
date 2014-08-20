#!/usr/bin/env python
import optparse,os,platform,shlex,shutil,sys,time
from glob import glob

"""
This module is intended to span the gap between Makefile and setup.py,
bringing the power and versatility of Python to the basic functionality
of make.

"""

# Get some system parameters
OS_NAME,HOST,KERNEL,PLATFORM,MACHINE,PROCESSOR=platform.uname()
if OS_NAME=='Darwin':
  OS_VER=platform.mac_ver()[0]
else:
  OS_VER=KERNEL

DISTRO_NAME,DISTRO_VER,dummy=('','','')
if OS_NAME=='Linux':
  if 'linux_distribution' in platform.__dict__:
    DISTRO_NAME,DISTRO_VER,dummy=platform.linux_distribution()
  elif 'dist' in platform.__dict__:
    DISTRO_NAME,DISTRO_VER,dummy=platform.dist()
del dummy


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Command line set-up.

op=optparse.OptionParser(
  usage="%prog [OPTIONS] target ..."
)
op.add_option('--cc',dest='cc',action='store',default=os.environ.get('CC','cc'),help="Specify what C compiler to use. (default: %default)")
op.add_option('-n','--dryrun',dest='dryrun',action='store_true',default=False,help="Go through all the usual steps, but don't actually build, install, or delete anything. (default:%default)")
op.add_option('--prefix',dest='prefix',action='store',default=None,help="This is the directory where things like bin, etc, lib, man, and sbin go. (default: %default)")
op.add_option('--sysinfo',dest='sysinfo',action='store_true',default=False,help="Show system information values and terminate.")
op.add_option('-v',dest='verbosity',action='count',default=0,help="Give the user a peek behind the curtain. Pull the curtain back a little farther for each -v option given.")
opt,args=op.parse_args()

if not args:
  args=['all']

if opt.sysinfo:
  for var in sorted("OS_NAME HOST KERNEL PLATFORM MACHINE PROCESSOR OS_VER DISTRO_NAME DISTRO_VER".split()):
    print '%s=%r'%(var,eval(var))
  sys.exit(0)

# These are our verbosity levels. The values incidate the number of -v options
# that turn on that level of verbosity.
V_DEPS=1
V_TIME=2

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Low-level functions.
#

def build_command(*args):
  '''Return a string containing all our arguments in a form that can be
  executed by os.system().'''

  # Get all the parts of the command in a single list.
  parts=[x.strip() for x in flatten(*args)]
  # Quote any parts that contain a space character.
  for i in range(len(parts)):
    if ' ' in parts[i]:
      if '\'' in parts[i]:
        parts[i]='"'+parts[i]+'"'
      else:
        parts[i]="'"+parts[i]+"'"
  # Return it all as a single string.
  cmd=' '.join(parts)
  print cmd
  return cmd

def expand_all(filename):
  "Return the filename with ~ and environment variables expanded."
  return os.path.expandvars(os.path.expanduser(filename))

def filetime(filename,default=0):
  """Return the modification time of the given file in floating point
  epoch seconds. If the file does not exist, return the default value."""

  try:
    default=os.path.getmtime(filename)
  except:
    pass
  if opt.verbosity>=V_TIME:
    print '  %s:\t%s'%(filename,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(default)))
  return default

def isnewer(src,dst):
  """Return true if src names a file that is newer than the file dst
  names (or if dst doesn't exist)."""

  return filetime(src,1)>filetime(dst)

def flatten(*args):
  '''Return a list of all arguments, breaking out elements of any tuples
  or lists encountered.'''

  l=[]
  for arg in args:
    if isinstance(arg,list) or isinstance(arg,tuple):
      l.extend([str(x).strip() for x in arg])
    else:
      l.append(str(arg).strip())
  return l

def outOfDate(target,*args):
  '''Return True if any of the other filename arguments identifies a
  file with a later modification time than target. (Otherwise, return
  False.)'''

  if os.path.exists(target):
    t=filetime(target)
  else:
    if opt.verbosity>=V_DEPS:
      print '  %s is out of date because it\'s missing'%target
    return True
  for d in args:
    if isinstance(d,list) or isinstance(d,tuple):
      if outOfDate(target,*d):
        return True
    elif not os.path.exists(d):
      # Return True for non-existant dependency in order to provoke an
      # error when the dependency is not found.
      if opt.verbosity>=V_DEPS:
        print '  %s depends on %s, which doesn\'t exist'%(target,d)
      return True
    elif filetime(d)>t:
      if opt.verbosity>=V_DEPS:
        print '  %s depends on %s, which is newer'%(target,d)
      return True
  return False

def expand_wildcards(filespec):
  '''Return a list of all the files matching filespec. If there are no
  such files, return a list with only filespec in it.'''

  files=glob(filespec)
  if not files:
    files=[filespec]
  return files

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Classes for different types of targets.
#

class Error(Exception):
  pass


class Target(object):
  """This is the base class of all Target subclasses. In addition to
  performing initialization that's common to all Target objects, it also
  maintains a list of all extant Target instances in a class attribute."""
  
  instances=[] # This is a list of all Target objects.

  def __init__(self,filename):
    """Remember the name of this target, mark it as yet-to-be-built, and
    add it to the list of Target instances."""

    self.built=False
    self.filename=filename
    Target.instances.append(self)

  def __del__(self):
    "Remove this Target from Target.instances."

    Target.instances.remove(self)

  def build(self):
    """Once this target has been built, it must be marked as such. This
    mechanism is used to ensure that mutual dependencies do not cause
    infinite recursion (so it's very important)."""

    if self.__class__.__name__=='Target':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True

class DependentTarget(Target):
  """Use this class to represent targets that are dependent on other files
  but which are not built from source. Such targets will not be remvoed
  by the clean() function."""

  def __init__(self,filename,*deps):
    "The target depends on all dependencies."

    Target.__init__(self,filename)
    self.deps=[]
    if deps:
      for d in flatten(*deps):
        self.deps.extend(expand_wildcards(d))

  def build(self):
    "Build all out-of-date dependencies."

    if self.built:
      return
    if opt.verbosity>=V_DEPS:
      if self.deps:
        print '  %s depends on %s'%(self.filename,' '.join(self.deps))
      else:
        print '  %s depends on nothing'%(self.filename)
    if self.deps:
      t=filetime(self.filename,0)
      for d in self.deps:
        tlist=getTargetsByName(d)
        if tlist:
          for t in tlist:
            t.build()
        elif t<filetime(d,1):
          for target in Target.instances:
            if not target.built and target.filename==d:
              target.build()
    if self.__class__.__name__=='DependentTarget':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


class DependentTargetFromSource(DependentTarget):
  """This class is exactly like DependentTarget, but targets built from
  instances of this class are removed (deleted from disk) by the this
  module's clean() function."""

  def __init__(self,filename,*deps):
    DependentTarget.__init__(self,filename,*deps)

  def build(self):
    "Build all out-of-date dependencies."

    # Call our Parent's build() method.
    super(DependentTargetFromSource,self).build()
    if self.__class__.__name__=='DependentTargetFromSource':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


class CExecutable(DependentTargetFromSource):
  "Objects of this class compile executables from C source files."

  def __init__(self,filename,source,*deps,**kwargs):
    """Specify how target should be built from source. Keyword argument
    may be:

    cc:   The name of the C compiler (default: cc).
    opts: A sequence of compiler options.
    objs: A sequence of object files to be linked with the executable."""

    DependentTargetFromSource.__init__(self,filename,*deps)
    self.deps=[source]+list(deps)
    self.source=source
    self.cc=opt.cc
    self.opts=kwargs.get('opts','')
    self.objs=kwargs.get('objs','')

  def build(self):
    if self.built:
      return
    # Build all dependencies first (including our object files).
    if self.objs:
      self.deps.append(self.objs)
    # Call the build() method of our parent class.
    super(CExecutable,self).build()

    # Compile this target.
    if outOfDate(self.filename,self.source,self.deps):
      print '\n%s:'%self.filename
      cmd=build_command(
        self.cc,
        COPTS,
        self.opts.split(),
        self.source,
        self.objs,
        '-o',
        self.filename
      )
      if not opt.dryrun:
        os.system(cmd)
    if self.__class__.__name__=='CExecutable':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


class CObjectFile(CExecutable):
  """Objects of this class compile object files from C source files. This
  is exactly like CExecutable, but the -c compiler option is forced."""

  def __init__(self,filename,source,*deps,**kwargs):
    CExecutable.__init__(self,filename,source,*deps,**kwargs)
    self.opts+=' -c'

  def build(self):
    "Build all out-of-date dependencies."

    # Call our Parent's build() method.
    super(CObjectFile,self).build()
    if self.__class__.__name__=='CObjectFile':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


class Installer(DependentTarget):
  "Copy all dependencies to installation directory."

  def __init__(self,filename,dir,*deps):
    DependentTarget.__init__(self,filename,*deps)
    self.dir=dir

  def build(self):
    # Build all dependencies (which are what this class installs).
    #print 'DEBUG: building dependencies for %s'%self.dir
    super(Installer,self).build()
    #print 'DEBUG: finished building dependencies for %s'%self.dir

    # Create the target directory if necessary.
    if not os.path.exists(self.dir):
      print 'mkdir %s'%self.dir
      sys.stdout.flush()
      if not opt.dryrun:
        os.makedirs(self.dir)
      print 'chmod 755 %s'%self.dir
      sys.stdout.flush()
      if not opt.dryrun:
        os.chmod(self.dir,0755)
    elif not os.path.isdir(self.dir):
      raise Error('%s exists but is not a directory.'%self.dir)

    # Copy each dependency to the given directory.
    for dep in self.deps:
      dest=os.path.join(self.dir,os.path.basename(dep))
      #print 'DEBUG: self.dir=%r dep=%r dest=%r'%(self.dir,dep,dest)
      if isnewer(dep,dest):
        print '%s ==> %s'%(dep,self.dir)
        sys.stdout.flush()
        if not opt.dryrun:
          shutil.copy2(dep,dest)
    if self.__class__.__name__=='Installer':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


class EasyInstall(Target):
  '''Run easy_install to install the package to the given directory, but
  only if it's not already installed.'''

  def __init__(self,package,dir):
    filename=os.path.join(dir,package)
    Target.__init__(self,filename)
    self.package=package
    self.dir=dir

  def build(self):
    if self.built:
      return
    if opt.verbosity>=V_DEPS:
      print '  Python package %s depends on %s*'%(self.package,self.filename)
    try:
      # If we're already able to load the module, we don't need to install it.
      mod=__import__(self.package)
      del mod
    except ImportError:
      # OK. So we need to install it.
      print '\n%s:'%self.package
      cmd=build_command('easy_install','--install-dir',self.dir,self.package)
      if not opt.dryrun:
        os.system(cmd)
    if self.__class__.__name__=='EasyInstall':
      # Mark this target as "built," but only if not called from a subclass.
      # This logic is needed in order to make calling super(...).build() safe.
      self.built=True


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def clean():
  "Delete all targets that are built from source."

  for t in Target.instances:
    if isinstance(t,DependentTargetFromSource):
      if os.path.isdir(t.filename):
        print 'rm -r %s'%t.filename
        sys.stdout.flush()
        if not opt.dryrun:
          os.rmtree(t.filename)
      elif os.path.exists(t.filename):
        print 'rm %s'%t.filename
        sys.stdout.flush()
        if not opt.dryrun:
          os.remove(t.filename)

def getTargetsByName(name):
  """Return a list of all Targets instances matching the given name."""

  if name=='all':
    tlist=list(Target.instances)
  else:
    tlist=[t for t in Target.instances if t.filename==name]
  return tlist

def make(target_name):
  """Call the build() method of all Target objects whose filename
  matches target_name."""

  for target in getTargetsByName(target_name):
    target.build()

# I'd like to be able to call make.path() rather than os.path.join() ...
# so here you go.
path=os.path.join

