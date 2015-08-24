#!/usr/bin/env python

import re
import addict

class Match(object):
  """This is a fairly thin wrapper around the normal _sre.SRE_Match
  object returned by _sre.SRE_Pattern's match() and search() methods.
  I've replaced groupdict() with groupDict(), which returns addict's
  Dict object rather than a standard Python dictionary."""

  def __init__(self,match):
    self.match=match

  def group(*args):
    """Same as normal group(*args) method except that a value of None is
    returned if there was no match."""

    if self.match:
      return self.match.group(*args)
    return None

  def groups(self,default=None):
    """Same as the normal groups([default]) method except that an empty
    tuple is returned if there was no match."""

    if self.match:
      return self.match.groups(default)
    return ()

  def groupDict(self):
    """Return a Dict of named groups in this Match except that an empty
    dictionary is returned if there was no match."""
    
    if self.match:
      d=self.match.groupdict()
    else:
      d={}
    return addict.Dict(d)

  def start(self,group=0):
    """Same as the normal start([group]) method except that a value of -1
    is return ed is there was no match."""

    if self.match:
      return self.match.start(group)
    return -1

  def end(self,group=0):
    """Same as the normal end([group]) method except that a value of -1 is
    return ed is there was no match."""

    if self.match:
      return self.match.end(group)
    return -1

  def span(self,group=0):
    """Same as the normal end([span]) method except that the tuple (-1,-1)
    is return ed is there was no match."""

    if self.match:
      return self.match.span(group)
    return (-1,-1)


class Grep(object):

  dummy_pattern=re.compile('dummy')

  def __init__(self,arg=None,flags=0):
    '''Initialize this object from a regular expression string, a
    compiled regular expression object, or a list or tuple of either (or
    both) of those things. The flags argument is the same as the re
    module's flags arguments.'''

    self.pats=[]
    self.flags=flags

    if isinstance(arg,Grep):
      self.pats=list(arg.pats)
      self.flags=arg.flags
    elif isinstance(arg,basestring):
      self.pats.append(re.compile(arg,flags))
    elif isinstance(arg,type(Grep.dummy_pattern)):
      self.path.append(arg)
    elif isinstance(arg,list) or isinstance(arg,tuple):
      for a in arg:
        if isinstance(a,basestring):
          self.pats.append(re.compile(a,flags))
        elif isinstance(a,re.RegexObject):
          self.path.append(a)

  def __repr__(self):
    '''Return a string that Python can evaluate to recreate this object.'''

    return 'Grep([%s],%d)'%(
      ','.join([repr(p.pattern) for p in self.pats]),
      self.flags
    )

  def __call__(self,input,**kwargs):
    '''An iterator that returns all matches from the input iterable.
    Tuples returned look like (line,index_array).
    
    Keyword arguments:
      invert
      match_all
    '''

    invert=kwargs.get('invert',False)
    match_all=kwargs.get('match_all',False)
  
    r=range(len(self.pats))
    for line in input:
      results=[Match(p.search(line)) for p in self.pats]
      matches=[i for i in r if results[i].match]
      if bool(matches)==bool(invert):
        continue
      yield (line,results)

if __name__=='__main__':
  import sys

  # Figure out what the user put on the command line.
  if len(sys.argv)>1 and not sys.stdin.isatty():
    f=sys.stdin
  elif len(sys.argv)>2:
    f=open(sys.argv[1])
    del sys.argv[1]
  else:
    print 'usage: %s [filename] regular_expression ...'
    sys.exit(1)

  # Work that grep magic.
  for line,results in Grep(sys.argv[1:])(f):
    sys.stdout.write(line)
