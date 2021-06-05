#!/usr/bin/env python3

import os

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
##
## DirWalkerBase
##

class DirWalkerBase(object):
  """This abstract base class traverses all paths beginning with root,
  calling its visit(path,files) method at each directory it encounters,
  including root. If the constructor's follow_links parameter is True,
  symbolic links are followed as well, and measures are taken to prevent
  visiting the same "real" directory twice, so infinite loops are not a
  problem.

  As an abstract base class, DirWalkerBase will not allow itself to be
  instantiated directly. You must subclass DirWalkerBase, providing your
  own implementation of the constructor and visit methods. This gives
  you great flexability in a way that fits the Python language very
  naturally. DirWalkerBase.walk(root,follow_links) is the main engine of
  this class and must be called if overridden in a subclass."""

  def __init__(self):
    if self.__class__.__name__=='DirWalkerBase':
      raise NotImplementedError('%s is an abstract base class and must not be instantiated directly.'%(self.__class__.__name__,))

  def walk(self,root,follow_links=True):
    """Start walking the subdirectory tree at root, safely following
    symlinks if follow_links is True (the default). For each path
    visited, call the visit method with the name of the path and a list
    of directory entries. The visit method may modify the list of
    directory entries to cull them, but it must do so "in place"."""

    self.root=root
    self.been_here=set([])
    self.follow_links=follow_links
    self._walk(self.root)

  def _walk(self,path):
    "For internal use only. Keep your mitts off this one."

    # Protection for infinite symlink loops.
    p=os.path.realpath(path)
    if p in self.been_here:
      return
    self.been_here.add(p)

    # Process this directory.
    flist=os.listdir(path)
    self.visit(path,flist)
    for fn in flist:
      p=os.path.join(path,fn)
      if os.path.isdir(p):
        if self.follow_links or not os.path.islink(p):
          self._walk(p)

  def visit(self,path,files):
    raise NotImplementedError('%s.visit() may not be called directly. Implement this method in a subclass.'%(self.__class__.__name__,))

if __name__=='__main__':
  import argparse,fnmatch,re,sys
  from debug import DebugChannel

  dbg=DebugChannel(True,label='D',stream=sys.stdout)

  ap=argparse.ArgumentParser()
  ap.add_argument('pat',metavar='FILESPEC',nargs='?',default='*',help="""Find files matching this FILESPEC. (default: %(default)s)""")
  opt=ap.parse_args()

  # Separate our search directory from the filespec itslef.
  dir,fs=os.path.split(opt.pat)
  if not dir:
    dir='.'
  if not fs:
    fs='*'
  dbg(f"dir={dir}, fs={fs}")
  # Translate our filespec to an regular expression, and compile it.
  fs=re.compile(fnmatch.translate(fs))
  dbg(f"fs.pattern={fs.pattern}")

  class DirWalker(DirWalkerBase):
    def visit(self,path,files):
      dbg(f"visit({repr(path)},{repr(files)})").indent()
      dirname=os.path.split(os.path.abspath(path))[1]
      dbg(f"dirname={repr(dirname)}")
      if not dirname.startswith('.'):
        for filename in files:
          if fs.match(filename):
            print(os.path.join(path,filename))
      dbg.undent()(f"visit({repr(path)},{repr(files)}) returns")

  walker=DirWalker()
  walker.walk(dir)
