#!/usr/bin/env python2

import ConfigParser,os,sys

class Conf(object):
  "Make using and updating a config file simple and natural."

  class Error(Exception):
    "This is the type of exception Conf objects raise."

    pass

  def __init__(self,**kwargs):
    """Read our config data from the given file. If none is given, use
    the path to and name of the currently running program to find our
    config file, and read that.
    
    Keyword Arguments:
    defaults:  If given, this dict value initializes dictionary of
               intrinsic defaults. See ConfigParser for details.
               (default: None)
    filename:  If given, this the name of the file from which config
               values are read to to which they are written. (default:
               None)
    extension: If given, this is the file extension (including the '.')
               to be used when searching for the current executable's
               conf file based on its. (default: '.conf')
    read_from: If given, this must be an already-open file-like object
               from which valid configuration data is ready to be read.
               (default: None)
    """

    # Initialize our keyword arguments.
    self.extension='testing'
    for var in ('defaults','filename','extension','read_from'):
      setattr(self,var,kwargs.get(var))
    if self.extension==None:
      self.extension='.conf'

    # Read our conf file.
    self.conf=ConfigParser.SafeConfigParser(self.defaults)
    if self.read_from:
      self.conf.readfp(self.read_from)
    else:
      if not self.filename:
        self.filename=self._find_conf_file()
      self.conf.read(self.filename)

  def __getitem__(self,key):
    return self.get(key)

  def __setitem__(self,key,val):
    self.set(key,val)

  def get(self,key,default=None):
    sect,opt=key.split('/',1)
    val=self.conf.get(sect,opt)
    if val==None:
      val=default
    return val
      
  def _find_conf_file(self):
    """Bend over backward to find and return the full path to our conf
    file.

    Search from the location of the current executable for its .conf
    file. Look first in the same directory, then in alternate
    directories at that location (secure, conf, conf.d, and etc in that
    order). If not found, then look one directory closer to / and repeat
    the search until we get to the root directory. Raise Conf.Error on
    utter and complete failure. Otherwise return the full path to the
    conf file."""

    # If we have no information about where this executable lives, all
    # hope is lost.
    if not sys.argv[0]:
      raise Conf.Error("Cannot figure out what conf file to read.")

    # Get the real path to where *this* executable lives.
    prev,path='',sys.argv[0]
    while prev!=path:
      prev,path=path,os.path.realpath(path)

    # Find the .conf file that goes with this executable.
    path,filename=os.path.split(path)
    filename+=self.extension

    # Start searching for our conf file.
    cfn0=cfn=os.path.join(path,filename)
    path=os.path.join(cfn,'foo') # Priming our loop.
    while True:
      # Back path up one directory level (toward /) and keep trying.
      path=os.path.dirname(path)
      cfn=os.path.join(path,filename)

      # Can we find the conf file here?
      if os.path.exists(cfn) and stat.S_ISREG(os.stat(cfn)[0]):
        break;
      found=True
      for alternate in ('secure','conf','conf.d','etc'):
        fn=os.path.join(path,alternate,filename)
        if os.path.exists(fn) and stat.S_ISREG(os.stat(fn)[0]):
          cfn=fn
          break;
      else:
        found=False
      if found:
        break; # Ugly, but effective.
      if cfn==cfn0 or path=='/':
        raise Conf.Error("Failed to find %s"%(filename,))
      cfn0=cfn

    # Success!
    return cfn

if __name__=='__main__':
  import doctest,StringIO

  conf_file=StringIO.StringIO("""
[main]
var1=5
var2=2.5
var3=foo
var4=foo bar
var5=This is a longer value that
 spans two lines in the conf data.

[foo]
a=testing
""")

  failed,total=doctest.testmod()
  if failed:
    sys.exit(1)

  conf=Conf(read_from=conf_file)
  print conf.get('main/var1')
  print conf['main/var5']
  print conf['foo/a']
