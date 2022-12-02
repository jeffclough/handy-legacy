"""
A Path is a fairly thin wrapper around str to accommodate this kind of
thing:

    >>> p=Path('alpha','bravo')
    >>> p
    Path('alpha/bravo')
    >>> print(p)
    alpha/bravo
    >>> p/'charlie'
    Path('alpha/bravo/charlie')
    >>> p/='charlie'
    >>> print(p)
    alpha/bravo/charlie
    >>> print(p.split())
    [Path('alpha'), Path('bravo'), Path('charlie')]
    >>> print(p.split(-1))
    [Path('alpha/bravo'), Path('charlie')]
    >>> print(p.split(-1)[0])
    alpha/bravo

The really cool thing (to me) is you can use Python's true division
operator (/) to build to a Path. I think this way is much more pythonic
than os.path.join() (which is also super wordy). You just have to be
sure the operand on the left is a Path object.

    >>> p=Path('/alpha')
    >>> p
    Path('/alpha')
    >>> p/'bravo'/'charlie'
    Path('/alpha/bravo/charlie')

And since Paths are based on Python's str class, a Path object is still
a string object. You can do all the things with a path you've always
done with strings ... but see Path.split()'s docs for how it's different
from str.split().

Splitting a rooted path presents os.sep (e.g. '/') as the first path
component.

    >>> Path('/usr/local/bin').split()
    [Path('/'), Path('usr'), Path('local'), Path('bin')]
    >>> Path('/usr/local/','/bin').split()
    [Path('/'), Path('usr'), Path('local'), Path('bin')]

Here's something closer to a real-world example: Find all the
directories in your current PATH that have an 'etc' directory next to
them.

    import os
    from path import Path

    bins_with_etc=[
      p for p in 
        [Path(x) for x in os.environ['PATH'].split(':')]
      if (p.dirName()/'etc').isDir()
    ]

This code is still very new. There are certainly some buggy edge-cases
to be worked out, but I think the Path class will be very handy for
applications that need to deal with filesystem structures.

By the way, the trickiest part of Path's code is from "Russia Must
Remove Putin" (a.k.a. Aaron C Hall) at StackOverflow. His example of an
effective way to override the str class is excellent.
https://bit.ly/how-to-subclass-str-in-python.
"""

__all__=[
  'Path',
  '__author__',
  '__version__',
]
__author__='Jeff Clough, @jeffclough@mastodon.social'
__version__='0.2.0-2022-11-27'

import os,re
from contextlib import contextmanager
from datetime import datetime

# Splitting paths needs to be able to split on colons (for drive or volume
# names) as well as on whatever's in os.sep.
re_splitter=re.compile(f"{os.sep}?[^:{os.sep}]+[:{os.sep}]?")

class Path(str):
  def __new__(cls,*s):
    """
    >>> Path()
    Path('.')
    >>> Path('a')
    Path('a')
    >>> p=Path('a','b','c')
    >>> p
    Path('a/b/c')
    >>> print(p)
    a/b/c
    >>> print(Path('/a','b','c'))
    /a/b/c
    """

#    return str.__new__(cls,os.sep.join(
#      [x.strip(os.sep) if i>0 else x.rstrip(os.sep)
#        for i,x in enumerate([os.path.normpath(str(y)) for y in s])
#      ]
    return str.__new__(cls,os.path.normpath(os.sep.join(s)))

  def __repr__(self):
    return f"{type(self).__name__}({super().__repr__()})"

  def __getattribute__(self,meth):
    if meth not in ('rsplit','split') and meth in dir(str):
      def m(self,*args,**kwargs):
        val=getattr(super(),meth)(*args,**kwargs)
        if isinstance(val,str): return type(self)(val)
        if isinstance(val,list): return [type(self)(v) for v in val]
        if isinstance(val,tuple): return tuple(type(self)(v) for v in value)
        return val
      return m.__get__(self)
    else:
      return super().__getattribute__(meth)

  def __truediv__(self,other):
    "Support / operator on Path objects and strings."

    return Path(f"{str(self)}{os.sep}{str(other)}")

  def split(self,n=None):
    """
    >>> Path('a','b','c').split()
    [Path('a'), Path('b'), Path('c')]
    >>> Path('a','b','c').split(1)
    [Path('a'), Path('b/c')]
    >>> Path('/a/b/c').split()
    [Path('/'), Path('a'), Path('b'), Path('c')]
    >>> Path('a','b','c').split(-1)
    [Path('a/b'), Path('c')]
    >>> Path('a','b','c','d').split(-2)
    [Path('a/b'), Path('c'), Path('d')]
    >>> Path('/a','b','c').split(-1)
    [Path('/a/b'), Path('c')]
    >>> Path('/a/b/c').dirName()
    Path('/a/b')
    >>> Path('/a/b/c').baseName()
    Path('c')
    >>> Path('a').dirName()
    Path('.')
    >>> Path('a').baseName()
    Path('a')
    >>> Path('/a').dirName()
    Path('/')
    >>> Path('/a').baseName()
    Path('a')
    """

    items=re_splitter.findall(self)
    if items and items[0].startswith(os.sep):
      items[:1]=[os.sep,items[0][1:]]
    if n is None:
      # No further treatment is needed.
      pass
    elif n>=0:
      # Rejoin all but the left-most n items.
      items=items[:n]+[''.join(items[n:])]
    else:
      l=len(items)
      items=[''.join(items[:l+n])]+items[l+n:]
    return [Path(x) for  x in items]

  # Steal some functionality from os and os.path.
  def absolute(self,reference=None):
    """Unless this is already an absolute (rooted) path, compute and
    return this Path instance's absolute path. If the "reference"
    argument is given, it will be used (rather than the current working
    directory) as the base directory _this_ directory is relative to."""

    if self.isAbsolute():
      return self

    # Get the path _this_ path is relative to.
    if reference:
      if isinstance(reference,Path):
        p=reference
      else:
        p=Path(str(reference))
    else:
      p=self.getCwd()

    # Return the absolute path.
    return (p/self).normal()

  def relative(self,start=os.curdir): return Path(os.path.relpath(str(self),str(start)))
  def normal(self): return Path(os.path.normpath(str(self)))
  def real(self): return Path(os.path.realpath(str(self)))

  def baseName(self): return self.split(-1)[1]
  def dirName(self): return self.split(-1)[0]

  def expandAll(self): return Path(os.path.expanduser(os.path.expandvars(str(self))))
  def expandUser(self): return Path(os.path.expanduser(str(self)))
  def expandVars(self): return Path(os.path.expandvars(str(self)))

  def exists(self): return os.path.exists(str(self))
  def isAbsolute(self): return os.path.isabs(str(self))
  def isDir(self): return os.path.isdir(str(self))
  def isFile(self): return os.path.isfile(str(self))
  def isLink(self): return os.path.islink(str(self))
  def isMount(self): return os.path.ismount(str(self))

  def aTime(self): return datetime.fromtimestamp(os.path.getatime(str(self)))
  def cTime(self): return datetime.fromtimestamp(os.path.getctime(str(self)))
  def mTime(self): return datetime.fromtimestamp(os.path.getmtime(str(self)))
  def size(self): return os.path.getsize(str(self))

  def remove(self):
    "Delete this file and return a reference to this Path object."

    os.remove(str(self))
    return self

  @classmethod
  def getCwd(cls):
    """Return the current working directory as a Path object. This is a
    class method, so call it as Path.getCwd()."""

    return cls(os.getcwd())

  @contextmanager
  def chdir(self):
    """This method changes the current directory to this directory. It
    can also be used as a context manager, in which case the previously
    current directory is restored after the "with" block. Example:

        with Path('/some/dir').chdir() as d:
          # Path d is now the CWD.
          ...

        # Now the previous CWD is in effect.
    """

    prev=Path.getCwd()  # Remember the previous directory.
    os.chdir(str(self)) # Change to the new directory.
    try:
      yield self        # "Return" this Path instance.
    finally:
      prev.chdir()      # Restore the previous current directory.

  def touch(self,*,atime=None,mtime=None,ref=None):
    """Set the atime and mtime of this file. Return a reference to this
    Path object."""

    # Get the atime and mtime to be set for this Path's file.
    if ref:
      if not isinstance(ref,Path):
        ref=Path(str(ref))
      atime=ref.aTime()
      mtime=ref.mTime()
    if isinstance(atime,datetime): atime=atime.timestamp()
    if isinstance(mtime,datetime): mtime=mtime.timestamp()

    # Set the atime and mtime for this file.
    os.utime(str(self),(atime,mtime))

    return self