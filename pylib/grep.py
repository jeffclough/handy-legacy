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

  def group(self,*args):
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

  def groupObject(self):
    """Return an anonymous object whose attributes are named by the named
    groups in the the RE that created this Match object. If the RE
    failed to match anything, a value of None is returned."""

    if self.match:
      o=type('',(),**self.match.groupdict())
    else:
      o=None
    return o

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
    Tuples returned look like (line,line_number,index_array).
    
    Keyword arguments:
      invert
      match_all

    Exmaples:
    Write to stdout only the lines from stdin that match all of
    our regular expressions.
      
      grep=Grep(array_of_REs)
      for line,n,matches in grep(sys.stdin):
        sys.stdout.write(line)

    Or if you're only going to do this once in your code, you could
    do it this way.

      for line,n,matches in Grep(array_of_REs)(sys.stdin):
        sys.stdout.write(line)

    '''

    find_all=kwargs.get('find_all',False)
    invert=kwargs.get('invert',False)
    match_all=kwargs.get('match_all',False)
  
    r=range(len(self.pats))
    n=0
    for line in input:
      n+=1
      results=[Match(p.search(line)) for p in self.pats]
      lr=len(results)
      matches=[m for m in results if m.match]
      #matches=[i for i in r if results[i].match]
      lm=len(matches)
      if not find_all and (lm==lr if match_all else lm>0)==bool(invert):
        continue
      yield (line,n,matches)

if __name__=='__main__':
  import optparse,sys

  op=optparse.OptionParser()
  op.add_option('--find-all',dest='find_all',action='store_true',default=False,help="Output all lines, including those that do not match any pattern.")
  op.add_option('--match-all',dest='match_all',action='store_true',default=False,help="Matching lines must match all paterns rather than at least one pattern.")
  op.add_option('--matches-only',dest='matches_only',action='store_true',default=False,help="Show only the matching portion(s) of each line.")
  op.add_option('-n',dest='line_numbers',action='store_true',default=False,help="Each output line is preceded by its line number, starting at 1.")
  op.add_option('-v',dest='invert',action='store_true',default=False,help="Output non-matching lines rather than matching ones.")
  opt,args=op.parse_args()

  def die(msg,rc=1):
    if msg:
      sys.stderr.write('%s: %s\n'%(op.get_prog_name(),msg))
    sys.exit(rc)

  if opt.invert and opt.matches_only:
    die('option error: --matches_only and --invert make no sense when used together.')

  # Figure out what the user put on the command line.
  if len(args)>0 and not sys.stdin.isatty():
    inf=sys.stdin
  elif len(args)>1:
    inf=open(args[0])
    del args[0]
  else:
    print 'usage: %s [filename] regular_expression ...'
    sys.exit(1)

  # Work that grep magic.
  grep_options=dict(
    find_all=opt.find_all,
    match_all=opt.match_all,
    invert=opt.invert,
  )
  grep=Grep(args)
  for line,n,matches in grep(inf,**grep_options):
    prefix=''
    if opt.find_all: prefix+=('> ' if matches else '  ')
    if opt.line_numbers: prefix+='%d: '%n
    if opt.matches_only:
      if len(matches)==1:
        sys.stdout.write(prefix+matches[0].group()+'\n')
      else:
        sys.stdout.write(prefix+('-'.join(['<'+m.group()+'>' for m in matches]))+'\n')
    else:
      sys.stdout.write(prefix+line)

