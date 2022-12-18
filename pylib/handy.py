#!/usr/bin/env python3
import fcntl,fnmatch,os,re,shlex,struct,sys,termios,warnings

class AsciiString(str):
  """This is just like str, but any non-ASCII characters are converted
  (if possible) to ASCII.

  >>> AsciiString('Ábhinav Ñavülurí')
  'Abhinav Navuluri'
  >>> AsciiString('Maxine Petrosíño')
  'Maxine Petrosino'
  >>> AsciiString('Spéncer Chrístensen')
  'Spencer Christensen'
  >>> AsciiString('Spéncer ▀Chrístensen')
  'Spencer ▀Christensen'
  """

    # This is a Unicode-to-ASCII translator.
  utoa=str.maketrans(
    'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿĂăŃńŠšūŽžƒȘșȚț',
    'AAAAAAACEEEEIIIIJNOOOOOOUUUUYBsaaaaaaaceeeeiiiionoooooouuuuybyAaNnSsuZzfSsTt'
  )

  def __new__(cls,val):
    return str.__new__(cls,val.translate(cls.utoa))
    #if not s.isascii():
    #  warnings.warn(
    #  f"{cls.__name__} instance contains non-ASCII content: {s!r}",
    #  UnicodeWarning,
    #  stacklevel=2
    #)
    #return s

class CaselessString(str):
  """This is kind of a lawyerly class for strings. They have no case! :)
  This is just like str, but hashing and comparison ignore case.

  >>> alpha=CaselessString('alpha')
  >>> bravo=CaselessString('Bravo')
  >>> charlie=CaselessString('charlie')
  >>> isinstance(alpha,str)
  True
  >>> print(alpha)
  alpha
  >>> print(bravo)
  Bravo
  >>> alpha<bravo
  True
  >>> bravo<charlie
  True
  >>> l=[bravo,alpha,charlie]
  >>> l
  [CaselessString("'Bravo'"), CaselessString("'alpha'"), CaselessString("'charlie'")]
  >>> l.sort()
  >>> l
  [CaselessString("'alpha'"), CaselessString("'Bravo'"), CaselessString("'charlie'")]
  """

  def __hash__(self):
    return hash(self.lower())

  def __lt__(self,other):
    if isinstance(other,str):
      return self.lower()<other.lower()
    return NotImplemented

  def __le__(self,other):
    if isinstance(other,str):
      return self.lower()<=other.lower()
    return NotImplemented

  def __eq__(self,other):
    if isinstance(other,str):
      return self.lower()==other.lower()
    return NotImplemented

  def __ne__(self,other):
    if isinstance(other,str):
      return self.lower()!=other.lower()
    return NotImplemented

  def __ge__(self,other):
    if isinstance(other,str):
      return self.lower()>=other.lower()
    return NotImplemented

  def __gt__(self,other):
    if isinstance(other,str):
      return self.lower()>other.lower()
    return NotImplemented

  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__,super(self.__class__,self).__repr__())

class CaselessDict(dict):
  """Just like dict, but string keys are coerced to CaselessString
  values.

  >>> x=CaselessDict(alpha=1,Bravo=2,charlie=3)
  >>> k=list(x.keys())
  >>> type(k[0])
  <class '__main__.CaselessString'>
  >>> k.sort()
  >>> k
  [CaselessString("'alpha'"), CaselessString("'Bravo'"), CaselessString("'charlie'")]
  >>> 'alpha' in x
  True
  >>> 'Alpha' in x
  True
  >>> 'bravo' in x
  True
  >>> 'Bravo' in x
  True
  >>> y=CaselessDict([('Delta',4),('echo',5),('FoxTrot',6)])
  >>> k=list(y.keys())
  >>> type(k[0])
  <class '__main__.CaselessString'>
  >>> k.sort()
  >>> k
  [CaselessString("'Delta'"), CaselessString("'echo'"), CaselessString("'FoxTrot'")]
  >>> z=CaselessDict(dict(x))
  >>> k=list(z.keys())
  >>> type(k[0])
  <class '__main__.CaselessString'>
  >>> k.sort()
  >>> k
  [CaselessString("'alpha'"), CaselessString("'Bravo'"), CaselessString("'charlie'")]
  >>> z.update(dict(y))
  >>> 'ALPHA' in z
  True
  >>> 'bravo' in z
  True
  >>> 'CHARLIE' in z
  True
  >>> 'delta' in z
  True
  >>> 'ECHO' in z
  True
  >>> 'FOXTROT' in z
  True
  >>> x.pop('alpha')
  1
  >>> x.pop('bravo')
  2
  >>> x.setdefault('alpha',1)
  1
  >>> x.setdefault('Bravo',2)
  2
  >>> k=list(x.keys())
  >>> k.sort()
  >>> k
  [CaselessString("'alpha'"), CaselessString("'Bravo'"), CaselessString("'charlie'")]
  >>> 'ALPHA' in x
  True
  >>> 'bravo' in x
  True

  """

  def __init__(self,obj=None,**kwargs):
    "Make sure all string keys go in as CaselessString values."

    if isinstance(obj,(list,tuple)):
      # This had better be a sequence of pairs.
      for k,v in obj:
        self[k]=type(v)(v)
    elif obj!=None:
      # Treat obj as a generic mapping object (which might not be a dict).
      for k in obj:
        self[k]=type(obj[k])(obj[k])
    for k,v in kwargs.items():
      self[k]=type(v)(v)

  def __contains__(self,k):
    "Make sure hash comparisons are done on CaselessString values."

    if type(k)!=CaselessString and isinstance(k,str):
      k=CaselessString(k)
    return super(CaselessDict,self).__contains__(k)

  def __getitem__(self,k):
    if type(k)!=CaselessString and isinstance(k,str):
      k=CaselessString(k)
    return super(CaselessDict,self).__getitem__(k)

  def __setitem__(self,k,val):
    "Make sure all stringish keys are put in as CaselessStrings."

    if type(k)!=CaselessString and isinstance(k,str):
      k=CaselessString(k)
    super(CaselessDict,self).__setitem__(k,val)

  def setdefault(self,k,default=None):
    if k not in self:
      self[k]=default
    return self[k]

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Generally useful stuff.

def first_match(s,patterns):
  """Find the first matching pattern. If found, return the (pattern,
  match) tuple. If not, return (None,None). The "patterns" arugment is
  an itterable of compiled regular expressions, but see the
  compile_filename_patterns() function also in this module for a way to
  make this far more general.

  >>> pats=['2019-*','re:^abc[0-9]{4}.dat$','X*.txt','*.txt',r're:^.*\.doc$']
  >>> pats=compile_filename_patterns(pats)
  >>> p,m=first_match('abc1980.dat',pats)
  >>> p.pattern
  '^abc[0-9]{4}.dat$'
  >>> m.group()
  'abc1980.dat'
  >>> p,m=first_match('X-ray.txt',pats)
  >>> p.pattern
  '(?s:X.*\\\\.txt)\\\\Z'
  >>> m.group()
  'X-ray.txt'
  >>> p,m=first_match('Y-ray.txt',pats)
  >>> p.pattern
  '(?s:.*\\\\.txt)\\\\Z'
  >>> m.group()
  'Y-ray.txt'
  >>> p,m=first_match('2019-10-26.dat',pats)
  >>> p.pattern
  '(?s:2019\\\\-.*)\\\\Z'
  >>> m.group()
  '2019-10-26.dat'
  >>> p,m=first_match('somefile.txt',pats)
  >>> p.pattern
  '(?s:.*\\\\.txt)\\\\Z'
  >>> m.group()
  'somefile.txt'
  >>> p,m=first_match('somefile.doc',pats)
  >>> p.pattern
  '^.*\\\\.doc$'
  >>> m.group()
  'somefile.doc'
  """

  for p in patterns:
    m=p.match(s)
    if m:
      return p,m
  return None,None

def non_negative_int(s):
  "Return the non-negative integer value of s, or raise ValueError."

  try:
    n=int(s)
    if n>=0:
      return n
  except:
    pass
  raise ValueError('%r is not a non-negative integer.'%s)

def positive_int(s):
  "Return the positive integer value of s, or raise ValueError."

  try:
    n=int(s)
    if n>0:
      return n
  except:
    pass
  raise ValueError('%r is not a non-negative integer.'%s)

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Filename and file system helpers.

def compile_filename_patterns(pattern_list):
  """Given a sequence of filespecs, regular expressions (prefixed with
  're:'), and compiled regular expressions, convert them all to compiled
  RE objects. The original pattern_list is not modified. The compiled
  REs are returned in a new list.

  >>> pats=['2019-*','re:^abc[0-9]{4}.dat$','X*.txt','*.txt',r're:\A.*\.doc\Z']
  >>> pats=compile_filename_patterns(pats)
  >>> pats[0].pattern
  '(?s:2019\\\\-.*)\\\\Z'
  >>> pats[1].pattern
  '^abc[0-9]{4}.dat$'
  >>> pats[2].pattern
  '(?s:X.*\\\\.txt)\\\\Z'
  >>> pats[3].pattern
  '(?s:.*\\\\.txt)\\\\Z'
  >>> pats[4].pattern
  '\\\\A.*\\\\.doc\\\\Z'
  """

  pats=list(pattern_list)
  for i in range(len(pats)):
    if isinstance(pats[i],str):
      if pats[i].startswith('re:'):
        pats[i]=pats[i][3:]
      else:
        pats[i]=fnmatch.translate(pats[i])
      pats[i]=re.compile(pats[i])
  return pats

def file_walker(root,**kwargs):
  """This is a recursive iterator over the files in a given directory
  (the root), in all subdirectories beneath it, and so forth. The order
  is an alphabetical and depth-first traversal of the whole directory
  tree.
  
  If anyone cares: While the effect of this function is to recurse into
  subdirectories, the function itself is not recursive.

  Keyword Arguments:
    depth        (default: None) The number of directories this
                 iterator will decend below the given root path when
                 traversing the directory structure. Use 0 for only
                 top-level files, 1 to add the next level of
                 directories' files, and so forth.
    follow_links (default: True) True if symlinks are to be followed.
                 This iterator guards against processing the same
                 directory twice, even if there's a symlink loop, so
                 it's always safe to leave this set to True.
    prune        (default: []) A list of filespecs, regular
                 expressions (prefixed by 're:'), or pre-compiled RE
                 objects. If any of these matches the name of an
                 encountered directory, that directory is ignored.
    ignore       (default: []) This works just like prune, but it
                 excludes files rather than directories.
    report_dirs  (default: False) If True or 'first', each directory
                 encountered will be included in this iterator's values
                 immediately before the filenames found in that
                 directory. If 'last', they will be included immediatly
                 after the the last entry in that directory. In any
                 case, directory names end with the path separator
                 appropriate to the host operating system in order to
                 distinguish them from filenames. If the directory is
                 not descended into because of depth-limiting or
                 pruning, that directory will not appear in this
                 iterator's values at all. The default is False, meaning
                 only non-directory entries are included."""

  # Get our keyword argunents, and do some initialization.
  max_depth=kwargs.get('depth',None)
  if max_depth==None:
    max_depth=sys.maxsize # I don't think we'll hit this limit in practice.
  follow_links=kwargs.get('follow_links',True)
  prune=compile_filename_patterns(kwargs.get('prune',[]))
  ignore=compile_filename_patterns(kwargs.get('ignore',[]))
  report_dirs=kwargs.get('report_dirs',False)
  if report_dirs not in (False,True,'first','last'):
    raise ValueError("report_dirs=%r is not one of False, True, 'first', or 'last'."%(report_dirs,))
  stack=[(0,root)] # Prime our stack with root (at depth 0).
  been_there=set([os.path.abspath(os.path.realpath(root))])
  dir_stack=[] # Stack of paths we're yielding after exhausting those directories.

  while stack:
    depth,path=stack.pop()
    if report_dirs in (True,'first'):
      yield path+os.sep
    elif report_dirs=='last':
      dir_stack.append(path+os.sep)
    flist=os.listdir(path)
    flist.sort()
    dlist=[]
    # First, let the caller iterate over these filenames.
    for fn in flist:
      p=os.path.join(path,fn)
      if os.path.isdir(p):
        # Just add this to this path's list of directories for now.
        dlist.insert(0,fn)
        continue
      pat,mat=first_match(fn,ignore)
      if not pat:
        yield p
    # Don't dig deeper than we've been told to.
    if depth<max_depth:
      # Now, let's deal with the directories we found.
      for fn in dlist:
        p=os.path.join(path,fn)
        # We might need to stack this path for our fake recursion.
        if os.path.islink(p) and not follow_links:
          # Nope. We're not following symlinks.
          continue
        rp=os.path.abspath(os.path.realpath(p))
        if rp in been_there:
          # Nope. We've already seen this path (and possibly processed it).
          continue
        m=None
        pat,mat=first_match(fn,prune)
        if pat:
          # Nope. This directory matches one of the prune patterns.
          continue
        # We have a keeper! Record the path and push it onto the stack.
        been_there.add(rp)
        stack.append((depth+1,p))
  while dir_stack:
    yield dir_stack.pop()

def rmdirs(path):
  """Just like os.rmdir(), but this fuction takes care of recursively
  removing the contents under path for you."""

  for f in file_walker(path,follow_links=False,report_dirs='last'):
    if f[-1]==os.sep:
      if f!=os.sep:
        #print "os.rmdir(%r)"%(f[:-1],)
        os.rmdir(f[:-1])
    else:
      #print "os.remove(%r)"%(f,)
      os.remove(f)

def shellify(val):
  """Return the given value quotted and escaped as necessary for a Unix
  shell to interpret it as a single value.

  >>> print(shellify(None))
  ''
  >>> print(shellify(123))
  123
  >>> print(shellify(123.456))
  123.456
  >>> print(shellify("This 'is' a test of a (messy) string."))
  'This '"'"'is'"'"' a test of a (messy) string.'
  >>> print(shellify('This "is" another messy test.'))
  'This "is" another messy test.'
  """

  if val==None:
    s=''
  elif not isinstance(val,str):
    s=str(val)
  else:
    return shlex.quote(val)
  return shlex.quote(s)

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
#   Main program module helpers.

class ProgInfo(object):
  """This prog object is required by die() and gripe(), but it's
  generally useful as well.
  
  Attributes:
    name      - basename of the current script's main file.
    pid       - numeric PID (program ID) of this script.
    dir       - full, absolute dirname of this script.
    real_name - like name, but with any symlinks resolved.
    real_dir  - like dir, bu with symlinks resolved.
    tempdir   - name of this system's main temp directory.
    temp      - full name of this script's temp file or temp directory."""

  def __init__(self,cmd=sys.argv[0]):
    """Set up this object's data according to cmd, which defaults to the
    name of the main file of the calling script."""

    # Name of the current script's main file without the directory.
    self.name=os.path.basename(sys.argv[0])

    # The numeric PID (program ID) of the currently running script.
    self.pid=os.getpid()

    # The full, absolute path to the directory given when the current
    # script was run.
    self.dir=os.path.abspath(os.path.dirname(sys.argv[0]))

    # Like name and dir, but these follow any symlinks to find the real name.
    # Also, real_dir holds the full, absolute path.
    self.real_dir,self.real_name=os.path.split(os.path.realpath(sys.argv[0]))

    # A decent choice of temp file or directory for this program, if
    # needed.
    self.tempdir=self.findMainTempDir()
    self.temp=os.path.join(self.tempdir,'%s.%d'%(self.name,self.pid))

    # Get the terminal width and and height, or default to 25x80.
    self.getTerminalSize()

  def __repr__(self):
    d=self.__dict__
    alist=list(self.__dict__.keys())
    alist.sort()
    return '%s(%s)'%(
      self.__class__.__name__,
      ','.join([
        '%s=%r'%(a,d[a])
          for a in alist
            if not a.startswith('_') and not callable(getattr(self,a))
    ]))

  def getTerminalSize(self):
    """Return a (width,height) tuple for the caracter size of our
    terminal. Also update our term_width and term_height members."""

    # Let the COLUMNS and LINES environment variables override any actual terminal
    # dimensions.
    self.term_width=os.environ.get('COLUMNS')
    if self.term_width:
      self.term_width=int(self.term_width)
    self.term_height=os.environ.get('LINES')
    if self.term_height:
      self.term_height=int(self.term_height)

    # Get terminal dimensions from the terminal device IFF needed.
    for f in sys.stdin,sys.stdout,sys.stderr:
      if f.isatty():
        th,tw,_,_=struct.unpack(
          'HHHH',
          fcntl.ioctl(f.fileno(),termios.TIOCGWINSZ,struct.pack('HHHH',0,0,0,0))
        )
        if not self.term_width:
          self.term_width=tw
        if not self.term_height:
          self.term_height=tw
        break
    else:
      # Lame though it is, use 80x25 for terminal dimensions if we can't figure
      # anything else out.
      if not self.term_width:
        self.term_width=80
      if not self.term_height:
        self.term_height=25

    return self.term_width,self.term_height

  def findMainTempDir(self,perms=None):
    """Return the full path to a reasonable guess at what might be a
    temp direcory on this system, creating it if necessary using the
    given permissions. If no permissions are given, we'll base the perms
    on the current umask."""

    # Let the environment tell us where our temp directory is, or ought
    # to be, or just use /tmp if the enrionment lets us down.
    d=os.path.abspath(
      os.environ.get('TMPDIR',
      os.environ.get('TEMP',
      os.environ.get('TMP',os.path.join(os.sep,'tmp'))
    )))

    # Ensure our temp direcory exists.
    if not os.path.isdir(d):
      # If no permissions were given, then just respect the current umask.
      if perms==None:
        m=os.umask(0)
        os.umask(m)
        perms=m^0o777
      # Set the 'x' bit of each non-zero permission tripplet
      # (e.g. 0640 ==> 0750).
      perms=[p|(p!=0) for p in [((mode>>n)&7) for n in (6,3,0)]]
      os.path.mkdirs(d,perms)

    # If all went well, return the full path of this possibly new directory.
    return d

  def makeTempFile(self,perms=0o600,keep=False):
    """Open (and likely create, but at least truncate) a temp file for
    this program, and return the open (for reading and writing) file
    object. See the our "temp" attribute for the name of the file.
    Remove this file at program termination unless the "keep" argument
    is False."""

    fd=os.open(self.temp,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_TRUNC,perms)
    f=os.fdopen(fd,'w+') 
    if not keep:
      atexit.register(os.remove,self.temp)
    return f

  def makeTempDir(self,perms=0o700,keep=False):
    """Create a directory for this program's temp files, and register a
    function with the atexit module that will automatically removed that
    whole directory if when this program exits (unless keep=True is
    given as one of the keyword arguments)."""

    os.mkdirs(self.temp,perms)
    if not keep:
      atexit.register(rmdirs,self.temp)
    return self.temp

prog=ProgInfo()

def die(msg,output=sys.stderr,progname=prog.name,rc=1):
  """Write '<progname>: <msg>' to output, and terminate with code rc.

  Defaults:
    output:   sys.stderr
    progname: basename of the current program (from sys.argv[0])
    rc:       1

  If rc==None the program is not actually terminated, in which case
  this function simply returns."""

  output.write('%s: %s\n'%(progname,msg))
  if rc!=None:
    sys.exit(rc)

def gripe(msg,output=sys.stderr,progname=prog.name):
  "Same as die(...,rc=None), so the program doesn't terminate."

  die(msg,output,progname,rc=None)

class Spinner(object):
  """Instantiate this class with any sequence, the elements of which
  will be returned iteratively every time that instance is called.

  Example:
  >>> spinner=Spinner('abc')
  >>> spinner=Spinner('abc')
  >>> spinner()
  'a'
  >>> spinner()
  'b'
  >>> spinner()
  'c'
  >>> spinner()
  'a'

  Each next element of the given sequence is returned every time the
  instance is called, which repeats forever. The default sequence is
  r'-\|/', which are the traditional ASCII spinner characters. Try this:

    import sys,time
    from handy import Spinner
    spinner=Spinner()
    while True:
      sys.stderr.write(" It won't stop! (%s) \\r"%spinner())
      time.sleep(0.1)

  It's a cheap trick, but it's fun. (Use ^C to stop it.)

  By the way, ANY indexable sequence can be used. A Spinner object
  instantiated with a tuple of strings will return the "next" string
  every time that instance is called, which can be used to produce
  multi-character animations. The code below demonstrates this and uses
  yoyo=True to show how that works as well.

    import sys,time
    from handy import Spinner
    spinner=Spinner(Spinner.cylon,True)
    while True:
      sys.stderr.write(" The robots [%s] are coming. \\r"%spinner())
      time.sleep(0.1)

  Bear in mind instantiating Spinner with a mutable sequence (like a
  list) means you can modify that last after the fact. This raises some
  powerful, though not necessarily intended, possibilities.
  """

  cylon=tuple('''
-        
 -       
  =      
  =+=    
   <*>   
    =+=  
      =  
       - 
        -
'''.strip().split('\n'))

  def __init__(self,seq=r'-\|/',yoyo=False):
    """Set the sequence for this Spinner instance. If yoyo is True, the
    sequence items are returned in ascending order than then in
    descending order, and so on. Otherwise, which is the default, the
    items are returned only in ascending order."""

    self.seq=seq
    self.ndx=-1
    self.delta=1
    self.yoyo=yoyo

  def __call__(self):
    """Return the "next" item from the sequence this object was
    instantiated with. If yoyo was True when this objecect was created,
    items will be returned in ascending and then descending order."""

    self.ndx+=self.delta
    if not 0<=self.ndx<len(self.seq):
      if self.ndx>len(self.seq):
        self.ndx=len(self.seq) # In case this sequence has shrunk.
      if self.yoyo:
        self.delta*=-1
        self.ndx+=self.delta*2
      else:
        self.ndx=0
    return self.seq[self.ndx]

wheel_spinner=Spinner(r'-\|/')
cylon_spinner=Spinner(Spinner.cylon,yoyo=True)

def getch(prompt=None,echo=False):
  """Read a single keystroke from stdin. The user needn't press Enter.
  This function returns the character as soon has it is typed. The
  character is not echoed to the screen unless the "echo" argument is
  True.

  If "prompt" is some true value, write that string to standard output
  before getting the input character, and then after the input, write a
  newline character to standard output."""

  import termios
  import sys, tty
  def _getch():
    fd = sys.stdin.fileno()
    old_settings=termios.tcgetattr(fd)
    try:
      tty.setraw(fd)
      ch = sys.stdin.read(1)
    finally:
      termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
    return ch

  if prompt:
    sys.stdout.write(prompt)
  ch=_getch()
  if echo:
    sys.stdout.write(ch)
  if prompt:
    sys.stdout.write('\n')
  return ch

if __name__=='__main__':
  import doctest,sys
  from pprint import pprint

  import argparse

  ap=argparse.ArgumentParser()
  sp=ap.add_subparsers()

  sp_find=sp.add_parser('find',help="Call file_walker() with the given path and options.")
  sp_find.set_defaults(cmd='find')
  sp_find.add_argument('path',action='store',default='.',help="The path to be searched.")
  sp_find.add_argument('--depth',action='store',type=non_negative_int,default=sys.maxsize,help="The number of directories to decend below the given path when traversing the directory structure.")
  sp_find.add_argument('--follow',action='store_true',help="Follow symlinks to directories during recursion. The method used is safe from symlink loops.")
  sp_find.add_argument('--ignore',metavar='FILE',action='store',nargs='+',default=[],help="A list of filespecs and/or regular expressions (prefixed with 're:') identifying files NOT to be reported.")
  sp_find.add_argument('--prune',metavar='DIR',action='store',nargs='+',default=[],help="A list of filespecs and/or regular expressions (prefixed with 're:') identifying directories NOT to be recursed into.")
  sp_find.add_argument('--dirs',dest='dirs',action='store',default='False',choices=('true','false','first','last'),help="If 'true' or 'first', output the path (with a %s suffix) immediately before listing the files in that directory. If 'last', output the path immediately after all files and other directories under that path have been output. Directory names are suppressed by default."%os.sep)

  sp_test=sp.add_parser('test',help="Run all doctests for this module.")
  sp_test.set_defaults(cmd='test')

  opt=ap.parse_args()
  if opt.cmd=='test': # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    print(f"prog.getTerminalSize(): {prog.getTerminalSize()}")
    print(f"prog.name: {prog.name}")
    print(f"prog.pid: {prog.pid}")
    print(f"prog.dir: {prog.dir}")
    print(f"prog.real_name: {prog.real_name}")
    print(f"prog.real_dir: {prog.real_dir}")
    print(f"prog.tempdir: {prog.tempdir}")
    print(f"prog.temp: {prog.temp}")
    print("Running doctests...")
    f,t=doctest.testmod()
    print(f"Passed {t-f} of {t} tests.")
    sys.exit(f>0)
  elif opt.cmd=='find': # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Whip opt.dirs into shape with a quick lookup.
    opt.dirs=opt.dirs.lower()
    opt.dirs=dict(false=False,true=True).get(opt.dirs,opt.dirs)
    # Expand ~ or environment variables in our path.
    opt.path=os.path.expandvars(os.path.expanduser(opt.path))
    # Put file_walker through its paces.
    for fn in file_walker(opt.path,depth=opt.depth,follow_links=opt.follow,prune=opt.prune,ignore=opt.ignore,report_dirs=opt.dirs):
      print(fn)
