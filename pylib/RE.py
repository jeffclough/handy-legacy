#!/usr/bin/env python

"""RE subclasses Python's build-in re module for the purpose of
implementing an extension mechanism for regular expression. For example,
RE extensions for matching account names and IP addresses might be set
up like this:

  import RE as re
  re.extend('account','[-_a-z0-9]+')
  re.extend('ipv4','\d{,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
  re.extend(
    'ipv6',
    '[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}:'
    '[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
  )

Regular expressions could then use these extensions using RE syntax
like '(?X<account>)' and '(?X<ipv4>)'."""

import re,os,sre_compile

# This pattern matches references to extensions.
extension_pattern=re.compile(r'\(\?X<([^>]+)>\)')

# A dictionary of extensions that our compile() function will recognize.
extensions={}

def compile(pattern,flags=0):
  """Compile a regular expression pattern, returning a pattern object.
  
  >>> extend('account',r'[-_a-z0-9]+')
  >>> extend('ipv4',r'\d{,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
  >>> extensions['account']==r'[-_a-z0-9]+'
  True
  >>> extensions['ipv4']==r'\\d{,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}'
  True
  >>> compile(r'^username=(?X<account>) from host (?X<ipv4>)$').pattern
  '^username=[-_a-z0-9]+ from host \\\\d{,3}\\\\.\\\\d{1,3}\\\\.\\\\d{1,3}\\\\.\\\\d{1,3}$'
  """

  # Replace RE extension references with the corresponding expressions.
  extlist=[]
  for m in extension_pattern.finditer(pattern):
    if m.group(1) not in extensions:
      raise sre_compile.error('Undefined RE extension: %r'%(m.group(1)))
    #print 'DEBUG: %r %r %r'%(m.group(1),m.start(),m.end)
    extlist.append(m)
  #print 'DEBUG: extlist=%r'%(extlist,)
  if extlist:
    # Perform the substitutions from right to left.
    extlist.reverse()
    #for m in extlist:
    #  print 'DEBUG: %r %r %r'%(m.group(1),m.start(),m.end)
    for m in extlist:
      pattern=pattern[:m.start()]+extensions[m.group(1)]+pattern[m.end():]

  #print 'DEBUG: compiling %r'%(pattern,)
  return re.compile(pattern,flags)

def extend(extname,pattern):
  """Add a nemed extension to for our regular expression precompiler to
  recognize."""

  extensions[extname]=pattern

# Since we're effectively extending the whole re module, we need to make sure
# that certain module-level functions and classes are provided.

# flags
I = IGNORECASE = re.I
L = LOCALE = re.L
U = UNICODE = re.U
M = MULTILINE = re.M
S = DOTALL = re.S
X = VERBOSE = re.X
T = TEMPLATE = re.T
DEBUG = re.DEBUG

def match(pattern, string, flags=0):
    """Try to apply the pattern at the start of the string, returning a
    match object, or None if no match was found."""

    return compile(pattern, flags).match(string)

def search(pattern, string, flags=0):
    """Scan through string looking for a match to the pattern, returning
    a match object, or None if no match was found."""

    return compile(pattern, flags).search(string)

def sub(pattern, repl, string, count=0, flags=0):
    """Return the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in string by the
    replacement repl.  repl can be either a string or a callable; if a
    string, backslash escapes in it are processed.  If it is a callable,
    it's passed the match object and must return a replacement string to
    be used."""

    return compile(pattern, flags).sub(repl, string, count)

def subn(pattern, repl, string, count=0, flags=0):
    """Return a 2-tuple containing (new_string, number). new_string is
    the string obtained by replacing the leftmost non-overlapping
    occurrences of the pattern in the source string by the replacement
    repl.  number is the number of substitutions that were made. repl
    can be either a string or a callable; if a string, backslash escapes
    in it are processed. If it is a callable, it's passed the match
    object and must return a replacement string to be used."""

    return compile(pattern, flags).subn(repl, string, count)

def split(pattern, string, maxsplit=0, flags=0):
    """Split the source string by the occurrences of the pattern,
    returning a list containing the resulting substrings."""

    return compile(pattern, flags).split(string, maxsplit)

def findall(pattern, string, flags=0):
    """Return a list of all non-overlapping matches in the string.

    If one or more groups are present in the pattern, return a list of
    groups; this will be a list of tuples if the pattern has more than
    one group.

    Empty matches are included in the result."""

    return compile(pattern, flags).findall(string)

def template(pattern, flags=0):
    "Compile a template pattern, returning a pattern object"

    return compile(pattern, flags|T)


_alphnum=re._alphanum
escape=re.escape
purge=re.purge()

# If a ~/.rerc file exists, initialize our RE extensions from it.
try:
  with open(os.path.expanduser("~/.rerc")) as f:
    for s in f:
      s=s.strip()
      if s=='' or s[0]=='#':
        continue
      name,pattern=s.split(':',1)
      extend(name,pattern)
except IOError,e:
  if e.errno!=2:
    raise

if __name__=='__main__':
  import doctest,pprint,sys

  # Test first.
  failed,total=doctest.testmod()
  if failed:
    print 'failed %d of %d tests'%(failed,total)
    sys.exit(1)

  # Then play.
  pprint.pprint(extensions)
  sys.exit(0)
