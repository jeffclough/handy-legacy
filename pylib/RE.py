"""
This module extends Python's re module just a touch, so re will be doing
almost all the work. I love the stock re module, but I want it to
support extensible regular expression syntax.

So that's what I've done. You can register your own RE extensions by
calling

    RE.extend(name,pattern)

Doing so means that "(?E<name>)" will be replaced with "(pattern)", and
"(?E<name>)" will be replaced with "(?P<name>pattern)", in any regular
expressions you use with this module. To keep things compatible with the
common usage of Python's standard re module, it's a good idea to import
RE like this:

    import RE as re

You can then create whatever custom extension you'd like in this way:

    re.extend('last_first',r'([!,]+)\s*,\s*(.*)')

Doing so means that

    re_name=re.compile(r'name:\s+(?E<last_first>)')

becomes exactly the same as

    re_name=re.compile(r'name:\s+(([!,]+)\s*,\s*(.*))')

If you use the extension like this,

    re_name=re.compile(r'name:\s+(?E<name=last_first>)')

with "name=last_first" rather than just "last_first", that translates to

    re_name=re.compile(r'name:\s+(?P<name>([!,]+)\s*,\s*(.*))')

so you can use groupdict() to get the value of "name".

It turns out having a few of these RE extensions predefined for your
code can be a handy little step-saver that also tends to increase its
readability, especially if it makes heavy use of regular expressions.

This module comes with several pre-loaded RE extensions that I've come
to appreciate:

General:
  id      - This matches login account names, programming language
            identifiers (for Python, Java, C, etc., but not SQL or other
            more special-purpose languages). Still '(?<id>)' is a nifty
            way to match account names.
  comment - Content following #, ;, or //, possibly preceded by
            whitespace.

Network:
  ipv4     - E.g. "1.2.3.4".
  ipv6     - E.g. "1:2:3:4:5:6".
  ipaddr   - Matches either ipv4 or ipv6.
  cidr     - E.g. "1.2.3.4/24".
  macaddr  - Looks a lot like ipv6, but the colons may also 
             be dashes or dots instead.
  hostname - A DNS name.
  host     - Matches either hostname or ipaddr.
  email    - Any valid email address. (Well above average, but not
             quite perfect.) There's also an email_localpart extension,
             which is used inside both "email" and "url" (below), but
             it's really just for internal use. Take a look if you're
             curious.
  url      - Any URL consisting of:
               protocol - req (e.g. "http" or "presto:http:")
               designator - req (either "email_localpart@" or "//")
               host - req (anything matching our "host" extension) port - opt (e.g. ":443")
               path - opt (e.g. "/path/to/content.html")
               params - opt (e.g. "q=regular%20expression&items=10")

Time and Date:
  day      -
  month    -
  date_YMD -
  date_YmD -
  date_mD  -
  time_HM  -
  time_HMS -

"""

import re
from re import error,escape,purge,template
from re import I,IGNORECASE,L,LOCALE,M,MULTILINE,S,DOTALL,U,UNICODE,X,VERBOSE,DEBUG

# Public symbols:
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
  "I","IGNORECASE", #   2
  "L","LOCALE",     #   4
  "M","MULTILINE",  #   8
  "S","DOTALL",     #  16
  "U","UNICODE",    #  32
  "X","VERBOSE",    #  64
  "DEBUG",          # 128
]

_extensions={}
_extpat=re.compile(r'(\(\?E<[_A-Za-z][_A-Za-z0-9]*>\))')
_extpat=re.compile(r'(\(\?E<[_A-Za-z][_A-Za-z0-9]*(=[_A-Za-z][_A-Za-z0-9]*)?>\))')

def _apply_extensions(pattern,allow_named=True):
  # Replace any extension RE with the corresponding RE.
  outer=True
  while True:
    extensions=set([r[0] for r in _extpat.findall(pattern)])
    if not extensions:
      break;
    for ref in extensions:
      ext=ref[4:-2]
      #print 'D: ext=%r'%(ext,)
      if not ext:
        raise error('RE extension name is empty')
      if '=' in ext:
        label,ext=ext.split('=')
      else:
        label=None
      #print 'D: label=%r, ext=%r'%(label,ext)
      if ext not in _extensions:
        raise error('Unknown RE extension %r'%(ext,))
      if label and outer and allow_named:
        pattern=pattern.replace(ref,'(?P<%s>%s)'%(label,_extensions[ext]))
      else:
        pattern=pattern.replace(ref,'(%s)'%(_extensions[ext],))
    outer=False
  return pattern

def extend(name,pattern,expand=False):
  """
  Register an extension RE pattern that can be referenced with the
  "(?E<name>)" construct. You can call RE.extend() like this:

      RE.extend('id','[-_0-9A-Za-z]+')

  And then, anytime you want to match an account name, you can simply
  use the '(?E<id>)' extension RE, making your code more readable and
  less prone to errors in regular expressions. Also, there are certainly
  other ways to accomplish this, a natural side-effect of this is that
  the RE for an account name only exists in one place in your code if it
  ever needs to be updated. Such references are replaced by
  '([-_0-9A-Za-z]+)' by the time the stock re module gets control. If
  you want to refer to matched groups by name, use the '(?E<user=id>)'
  form which be substituted with '(?P<user>[-_0-9A-Za-z]+)'.

  """

  if expand:
    pattern=_apply_extensions(pattern)
  _extensions[name]=pattern

def compile(pattern,flags=0):
  "Compile a regular expression pattern, returning a pattern object."

  return re.compile(_apply_extensions(pattern),flags)

def findall(pattern,s,flags=0):
  """Return a list of all non-overlapping matches in the string.

  If one or more groups are present in the pattern, return a list of
  groups; this will be a list of tuples if the pattern has more than one
  group.

  Empty matches are included in the result."""

  return re.findall(_apply_extensions(pattern),s,flags)

def finditer(pattern,s,flags=0):
  """Return an iterator over all non-overlapping matches in the string.
  For each match, the iterator returns a match object.

  Empty matches are included in the result."""
  
  return re.finditer(_apply_extensions(pattern),s,flags)

def match(pattern,s,flags=0):
  """Try to apply the pattern at the start of the string, returning a
  match object, or None if no match was found."""

  return re.match(_apply_extensions(pattern),s,flags)

def search(pattern,s,flags=0):
  """Scan through string looking for a match to the pattern, returning a
  match object, or None if no match was found."""

  return re.search(_apply_extensions(pattern),s,flags)

def split(pattern,s,maxsplit=0,flags=0):
  """Split the source string by the occurrences of the pattern,
  returning a list containing the resulting substrings."""

  return re.split(_apply_extensions(pattern),s,maxsplit,flags)

def sub(pattern, repl, string, count=0, flags=0):
  """Return the string obtained by replacing the leftmost
  non-overlapping occurrences of the pattern in string by the
  replacement repl. repl can be either a string or a callable; if a
  string, backslash escapes in it are processed. If it is a callable,
  it's passed the match object and must return a replacement string to
  be used."""

  return re.sub(_apply_extensions(pattern),repl,s,count,flags)

def subn(pattern, repl, string, count=0, flags=0):
  """Return a 2-tuple containing (new_string, number). new_string is the
  string obtained by replacing the leftmost non-overlapping occurrences
  of the pattern in the source string by the replacement repl. number
  is the number of substitutions that were made. repl can be either a
  string or a callable; if a string, backslash escapes in it are
  processed. If it is a callable, it's passed the match object and must
  return a replacement string to be used."""

  return re.subn(_apply_extensions(pattern),repl,s,count,flags)

# Account names.
extend('id',r'[-_0-9A-Za-z]+')
# Python (Java, C, et al.) identifiers.
extend('ident',r'[_A-Za-z][_0-9A-Za-z]+')

# Comments may begin with #, ;, or // and continue to the end of the line.
# If you need to handle multi-line comments ... feel free to roll your own
# extension for that. (It CAN be done.)
extend('comment',r'\s*([#;]|//).*')

# Network
extend('ipv4','.'.join([r'\d{1,3}']*4))
extend('ipv6',':'.join([r'[0-9A-Fa-f]{1,2}']*6))
extend('ipaddr',r'(?E<ipv4>)|(?E<ipv6>)')
extend('cidr',r'(?E<ipv4>)/\d{1,2}')
extend('macaddr',r'[-:.]'.join(['([0-9A-Fa-f]{1,2})']*6))
extend('hostname',r'[0-9A-Za-z]+(\.[-0-9A-Za-z]+)*')
extend('host','(?E<ipaddr>)|(?E<hostname)')
extend('hostport','(?E<host>)(:(\d{1,5}))?') # Host and optional port.
extend('filename',r'[~/]+')
extend('path',r'/?(?E<filename>)(/?E<filename>)*')
extend('abspath',r'/(?E<filename>)(/?E<filename>)*')
extend('email_localpart',
  r"\([!(]*\)?" # Comments are allowed in email addresses. Who knew!?
  r"([0-9A-Za-z!#$%&'*+-/=?^_`{|}~]+)"
  r"(\.([0-9A-Za-z!#$%&'*+-/=?^_`{|}~)+)*"
  r"\([!(]*\)?" # The comment is either before or after the local part.
  r"@"
)
extend('email',r"(?E<email_localpart>)(?E<hostport>)")
extend('url_scheme',r'([A-Za-z][-+.0-9A-Za-z]*:){1,2}')
extend('url',
  r'(?E<url_scheme>)'            # E.g. 'http:' or 'presto:http:'.
  r'((?E<email_localpart)|(//))' # Allows both 'mailto:addr' and 'http://host'.
  r'((?E<hostport>)(:\d+)?)'     # Host (required) and port (optional).
  r'(?E<abspath>)?'              # Any path that MIGHT follow all that.
  r'(\?'                         # Any parameters that MIGHT be present.
    r'(([!=]+)=([!&]*))'
    r'(&(([!=]+)=([!&]*)))*'
  r')?'
)

# Day, date, and time matching are furtile ground for improvement.
# day = SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY
#       Case doesn't matter, and any distince beginning of those day names is
#       sufficient to match.
extend('day',r'(?i((su)|(m)|(tu)|(w)|(th)|(f)|(sa))[aedionsruty]*)')
# month = JANUARY|FEBRUARY|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER
#         This works just like the day extension, but for month names.
extend('month',r'(?i((ja)|(f)|(mar)|(ap)|(may)|(jun)|(jul)|(au)|(s)|(o)|(n)|(d))[acbegihmlonpsrutvy]*)')
# date_YMD = [[CC]Y]Y(-|/|.)[M]M(-|/|.)[D]D
#            Wow. the BNF format is uglier than the RE. Just think YYYY-MM-DD
#            where the dashes can be / or . instead.
extend('date_YMD',r'((\d{2,4})([-/.])(\d{1,2})([-/.])(\d{1,2}))')
# date_YmD is basically "YYYY-mon-DD" where mon is the name of a month as
# defined by the "month" extension above.
extend('date_YmD',r'((\d{2,4})([-/.])((?E<month>))([-/.])(\d{1,2}))')
# date_mD is basically "mon DD" where mon is the name of a month as defined by
# the "month" extension above.
extend('date_mD',r'(?E<month>\s+(\d{1,2}))')
# time_HMS = HH:MM:SS
# time_HM = HH:MM
#            12- or 24-hour time will do, and the : can be . or - instead.
extend('time_HM',r'(\d{1,2})([-:.])(\d{2})')
extend('time_HMS',r'(\d{1,2})([-:.])(\d{2})([-:.])(\d{2})')

# TODO: Parse https://www.timeanddate.com/time/zones/ for TZ data, and hardcode
# that into an RE extension here.

if __name__=='__main__':
  import sys
  from doctest import testmod
  from english import nounf

  def tests():
    """
    >>> _apply_extensions(r'user=(?E<user=id>)')
    'user=(?P<user>[-_a-z0-9]+)'
    >>> _apply_extensions(r'user=(?E<id>)')
    'user=([-_a-z0-9]+)'
    >>> s='    user=account123, client=123.45.6.78     '
    >>> m=search(r'user=(?E<user=id>)',s)
    >>> m.groups()
    ('account123',)
    >>> b,e=m.span()
    >>> s[b:e]
    'user=account123'
    >>> m=search(r'user=(?E<user=id>),\s*client=(?E<client=ipv4>)',s)
    >>> m.groups()
    ('account123', '123.45.6.78')
    >>> m.groupdict()
    {'client': '123.45.6.78', 'user': 'account123'}
    >>> s='x=5 # This is a comment.    '
    >>> m=search(r'(?E<comment>)',s)
    >>> s[:m.span()[0]]
    'x=5'
    >>> s='subnet=123.45.6.78/24'
    >>> p=compile(r'subnet=(?E<net=cidr>)')
    >>> m=p.match(s)
    >>> m.groupdict()['net']
    '123.45.6.78/24'
    """

  if True:
    f,t=testmod(report=False)
    if f>0:
      print '*********************************************************************\n'
    print "Passed %d of %s."%(t-f,nounf('test',t))
    sys.exit((1,0)[f==0])
