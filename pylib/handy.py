#!/usr/bin/env python
import fnmatch,os,pipes,re,sys
from argparse import ArgumentTypeError

def non_negative_int(s):
  "Return the non-negative integer value of s, or raise ArgumentTypeError."

  try:
    n=int(s)
    if n>=0:
      return n
  except:
    pass
  raise ArgumentTypeError('%r is not a non-negative integer.'%s)

def positive_int(s):
  "Return the positive integer value of s, or raise ArgumentTypeError."

  try:
    n=int(s)
    if n>0:
      return n
  except:
    pass
  raise ArgumentTypeError('%r is not a non-negative integer.'%s)

def first_match(s,patterns,flags=0):
  """Find the firsts pattern in the patterns sequence that matches s. If
  found, return the (pattern,match) tuple. Otherwise, return
  (None,None)."""

  for p in patterns:
    m=p.match(s,flags)
    if m:
      return p,m
  return None,None

def compile_filename_patterns(pattern_list):
  """Given a sequence of filespecs, regular expressions (prefixed with
  're:'), and compiled regular expressions, convert them all to compiled
  RE objects. The original pattern_list is not modified. The compiled
  REs are returned in a new list."""

  pats=list(pattern_list)
  for i in range(len(pats)):
    if isinstance(pats[i],basestring):
      if pats[i].startswith('re:'):
        pats[i]=pats[i][2:]
      else:
        pats[i]=fnmatch.translate(pats[i])
      pats[i]=re.compile(pats[i])
  return pats

def file_walker(root,**kwargs):
  """This is a recursive iterator over the files in a given directory
  (the root), in all subdirectories beneath it, and so forth. The order
  is an alphabetical and depth-first traversal of the whole directory
  tree.

  Keyword Arguments:
    depth         (default: None) The number of directories this
                  iterator will decend below the given root path when
                  traversing the directory structure. Use 0 for only
                  top-level files, 1 to add the next level of
                  directories' files, and so forth.
    follow_links  (default: True) True if symlinks are to be followed.
                  This iterator guards against processing the same
                  directory twice, even if there's a symlink loop, so
                  it's always safe to leave this set to True.
    prune         (default: []) A list of filespecs, regular
                  expressions (prefixed by 're:'), or pre-compiled RE
                  objects. If any of these matches the name of an
                  encountered directory, that directory is ignored.
    ignore        (default: []) This works just like prune, but it
                  excludes files rather than directories.
    include_dirs  (default: False) True if each directory encountered is
                  to be included in this iterator's values immediately before
                  the filename found in that directory. Directory names end
                  with the path separator appropriate to the host operating
                  system in order to distinguish them from filenames. If the
                  directory is not descended into because of depth-limiting or
                  pruning, that directory will not appear in this iterator's
                  values at all. The default is False, so that only
                  non-directory entries are included. 
  """

  # Get our keyword argunents, and do some initialization.
  max_depth=kwargs.get('depth',None)
  if max_depth==None:
    max_depth=sys.maxsize # I don't think we'll hit this limit in practice.
  follow_links=kwargs.get('follow_links',True)
  prune=compile_filename_patterns(kwargs.get('prune',[]))
  ignore=compile_filename_patterns(kwargs.get('ignore',[]))
  include_dirs=kwargs.get('include_dirs',False)
  stack=[(0,root)] # Prime our stack with root (at depth 0).
  been_there=set([os.path.abspath(os.path.realpath(root))])

  while stack:
    depth,path=stack.pop()
    if include_dirs:
      yield path+os.sep
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

def shellify(val):
  """Return the given value quotted and escaped as necessary for a Unix
  shell to interpret it as a single value.

  >>> print shellify(None)
  ''
  >>> print shellify(123)
  123
  >>> print shellify(123.456)
  123.456
  >>> print shellify("This 'is' a test of a (messy) string.")
  'This '"'"'is'"'"' a test of a (messy) string.'
  >>> print shellify('This "is" another messy test.')
  'This "is" another messy test.'
  """

  if val==None:
    return "''"
  if isinstance(val,int) or isinstance(val,float):
    return val
  if not isinstance(val,basestring):
    val=str(val)
  return pipes.quote(val)

class TitleCase(str):
  """A TitleCase value is just like a str value, but it gets title-cased
  when it is created.

  >>> TitleCase('')
  ''
  >>> TitleCase('a fine kettle of fish')
  'A Fine Kettle of Fish'
  >>> TitleCase('    another     fine     kettle     of     fish    ')
  'Another Fine Kettle of Fish'
  >>> t=TitleCase("to remember what's yet to come")
  >>> t
  "To Remember What's Yet to Come"
  >>> t.split()
  ['To', 'Remember', "What's", 'Yet', 'to', 'Come']
  >>> str(type(t)).endswith(".TitleCase'>")
  True
  """
  
  # Articles, conjunctions, and prepositions are always lower-cased, unless
  # they are the first word of the title.
  lc=set("""
    a an the
    and but nor or
    is
    about as at by circa for from in into of on onto than till to until unto via with
  """.split())

  def __new__(cls,value=''):
    # Divide this string into words, and then process it that way.
    words=[w for w in value.lower().split() if w]

    # Join this sequence of words into a title-cased string.
    value=' '.join([
      words[i].lower() if words[i] in TitleCase.lc and i>0 else words[i].capitalize()
        for i in range(len(words))
    ])

    # Now become our immutable value as a title-cased string.
    return str.__new__(cls,value)

if __name__=='__main__':
  import argparse,doctest,sys

  import argparse
  ap=argparse.ArgumentParser()
  sp=ap.add_subparsers()

  sp_test=sp.add_parser('test',help="Run all doctests for this module.")
  sp_test.set_defaults(cmd='test')

  sp_find=sp.add_parser('find',help="Call file_walker() with the given path and options.")
  sp_find.set_defaults(cmd='find')
  sp_find.add_argument('path',action='store',default='.',help="The path to be searched.")
  sp_find.add_argument('--depth',action='store',type=non_negative_int,default=sys.maxsize,help="The number of directories to decend below the given path when traversing the directory structure.")
  sp_find.add_argument('--follow',action='store_true',help="Follow symlinks to directories during recursion. This is done in a way that's safe from symlink loops.")
  sp_find.add_argument('--prune',metavar='DIR',action='store',nargs='*',default=[],help="A list of filespecs and/or regular expressions (prefixed with 're:') that itentify directories NOT to be recursed into.")
  sp_find.add_argument('--dirs',action='store_true',help="Output the path (with a %s suffix) immediately before listing the files in that directory. Directory names are ordinarilly suppressed.")

  opt=ap.parse_args()
  print repr(opt)

  if opt.cmd=='test':
    t,f=doctest.testmod()
    if f>0:
      sys.exit(1)
  elif opt.cmd=='find':
    for fn in file_walker(opt.path,depth=opt.depth,follow_links=opt.follow,prune=opt.prune,include_dirs=opt.dirs):
      print fn
