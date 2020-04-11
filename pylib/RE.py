"""
This module extends Python's re module just a touch, so re will be doing
almost all the work. I love the stock re module, but I want it to
support extensible regular expression syntax.

For example: I want to be able to use things like '(?X<account>)' and
'(?X<ipv4>)' to match account names and IP addresses.

    import RE as re
    re.extend('account','[-_a-z0-9]+')
    re.extend('ipv4','\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    re.extend('ipv6',':'.join(['[0-9A-Fa-f]{1,4}']*6))
    re.extend('ipaddr','(?X<ipv4>)|(?X<ipv6>)')

And then with these "extensions" in place, we can do things like this:

    log_parser=re.compile('user=(?X<account>), client=(?X<ipaddr>)')
    with open('someapp.log') as f:
      for s in f:
        m=log_parser.search(s)
        if m:
          d=m.groupdict()
          print('user=%s, client=%s'%(d['user'],d['ipaddr']))

If you use '(?x<some_name>)' rather than '(?X<some_name>)', the
extension replacement will be simply '(pattern)' rather than
'(?P<some_name>pattern)'. This is also true of "inner" extensions, as is
the case for the "ipaddr" extension defined above. '(?X<ipaddr>)'
becomes '(?P<ipaddr>(ipv4_pattern|ipv6_pattern))'. This avoids having
named groups defined within named groups.

It turns out having a few of these RE extensions predefined for your
code can be a handy little step-saver, and being able to add your own
extensions can increase the readability of code that makes heavy use of
regular expressions.

"""
from re import error
from re import compile as _re_compile
from re import escape
from re import findall as _re_findall
from re import match as _re_match
from re import purge
from re import search as _re_search
from re import split as _re_split
from re import sub as _re_sub
from re import subn as _re_subn
from re import template
from re import I,L,M,S,X,U,IGNORECASE,LOCALE,MULTILINE,DOTALL,VERBOSE

# public symbols
__all__=[
  "compile",
  "error",
  "escape",
  "extend",
  "findall",
  "match",
  "purge",
  "search",
  "split",
  "sub",
  "subn",
  "template",
  "DOTALL",
  "I",
  "IGNORECASE",
  "L",
  "LOCALE",
  "M",
  "MULTILINE",
  "S",
  "U",
  "UNICODE",
  "VERBOSE",
  "X",
]

_extensions={}
_extpat=_re_compile(r'(\(\?[Xx]<[_A-Za-z][_A-Za-z0-9]*>\))')

def _apply_extensions(pattern):
  # Replace any named extensions with the corresponding REs.
  inner=False
  while True:
    extensions=set(_extpat.findall(pattern))
    if not extensions:
      break;
    for ref in extensions:
      x=ref[4:-2]
      if not x:
        raise error('RE extension name is empty')
      if x not in _extensions:
        raise error('Unknown RE extension %r'%(x,))
      if ref[2]=='x' or inner:
        pattern=pattern.replace(ref,'(%s)'%(_extensions[x],))
      else:
        pattern=pattern.replace(ref,'(?P<%s>%s)'%(x,_extensions[x]))
      print pattern
    inner=True
  return pattern

def extend(name,pattern):
  """
  Register an extension RE pattern that can be referenced with the
  "(?X<name>)" construct. You can call RE.extend() like this:

      RE.extend('account_name','[-_a-z0-9]+')

  And then, anytime you want to match an account name, you can simply
  use the '(?X<account_name>)' extension RE, making your code more
  readable and less prone to errors in regular expressions. Such
  references are replaced by '(?P<account_name>[-_a-z0-9]+)' by the time
  the stock re module gets control, so any match can be extracted by
  group number or group name.

  """

  _extensions[name]=pattern

def compile(pattern,flags=0):
  "Compile a regular expression pattern, returning a pattern object."

  return _re_compile(_apply_extensions(pattern),flags)

def findall(pattern,s,flags=0):
  """Return a list of all non-overlapping matches in the string.

  If one or more groups are present in the pattern, return a list of
  groups; this will be a list of tuples if the pattern has more than one
  group.

  Empty matches are included in the result."""

  return _re_findall(_apply_extensions(pattern),s,flags)

def finditer(pattern,s,flags=0):
  """Return an iterator over all non-overlapping matches in the string.
  For each match, the iterator returns a match object.

  Empty matches are included in the result."""
  
  return _re_finditer(_apply_extensions(pattern),s,flags)

def match(pattern,s,flags=0):
  """Try to apply the pattern at the start of the string, returning a
  match object, or None if no match was found."""

  return _re_match(_apply_extensions(pattern),s,flags)

def search(pattern,s,flags=0):
  """Scan through string looking for a match to the pattern, returning a
  match object, or None if no match was found."""

  return _re_search(_apply_extensions(pattern),s,flags)

def split(pattern,s,maxsplit=0,flags=0):
  """Split the source string by the occurrences of the pattern,
  returning a list containing the resulting substrings."""

  return _re_split(_apply_extensions(pattern),s,maxsplit,flags)

def sub(pattern, repl, string, count=0, flags=0):
  """Return the string obtained by replacing the leftmost
  non-overlapping occurrences of the pattern in string by the
  replacement repl. repl can be either a string or a callable; if a
  string, backslash escapes in it are processed. If it is a callable,
  it's passed the match object and must return a replacement string to
  be used."""

  return _re_sub(_apply_extensions(pattern),repl,s,count,flags)

def subn(pattern, repl, string, count=0, flags=0):
  """Return a 2-tuple containing (new_string, number). new_string is the
  string obtained by replacing the leftmost non-overlapping occurrences
  of the pattern in the source string by the replacement repl. number
  is the number of substitutions that were made. repl can be either a
  string or a callable; if a string, backslash escapes in it are
  processed. If it is a callable, it's passed the match object and must
  return a replacement string to be used."""

  return _re_subn(_apply_extensions(pattern),repl,s,count,flags)

# Start the user off with some useful RE extensions.
extend('username','[-_a-z0-9]+')
extend('ipv4','\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
extend('ipv6',':'.join(['[0-9A-Fa-f]{1,4}']*6))
extend('ipaddr','(?X<ipv4>)|(?X<ipv6>)')

