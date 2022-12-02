#!/usr/bin/env python3
"""
This module extends Python's re module just a touch, so re will be doing
almost all the work. I love the stock re module, but I'd also like it to
support extensible regular expression syntax.

So that's what this module does. It is a pure Python wrapper around
Python's standard re module that lets you register your own regepx
extensions by calling

    RE.extend(name,pattern)

Doing so means that "(?E:name)" in regular expressions used with *this*
module will be replaced with "(pattern)", and "(?E:label=name)" will be
replaced with "(?P<label>pattern)", in any regular expressions you use
with this module. To keep things compatible with the common usage of
Python's standard re module, it's a good idea to import RE like this:

    import RE as re

This keeps your code from calling the standard re functions directly
(which will report things like "(?E:anything)" as errors, of course),
and it lets you then create whatever custom extension you'd like in this
way:

    re.extend('last_first',r'([!,]+)\s*,\s*(.*)')

This regepx matches "Flanders, Ned" in this example string:

    name: Flanders, Ned

And you can use it this way:

    re_name=re.compile(r'name:\s+(?E:last_first)')

That statement is exactly the same as

    re_name=re.compile(r'name:\s+(([!,]+)\s*,\s*(.*))')

but it's much easier to read and understand what's going on. If you use
the extension like this,

    re_name=re.compile(r'name:\s+(?E:name=last_first)')

with "name=last_first" rather than just "last_first", that translates to

    re_name=re.compile(r'name:\s+(?P<name>([!,]+)\s*,\s*(.*))')

so you can use the match object's groupdict() method to get the value of
the "name" group.

It turns out having a few of these regepx extensions predefined for your
code can be a handy little step-saver that also tends to increase its
readability, especially if it makes heavy use of regular expressions.

This module comes with several pre-loaded regepx extensions that I've
come to appreciate:

General:
  id      - This matches login account names and programming language
            identifiers (for Python, Java, C, etc., but not SQL or other
            more special-purpose languages). Still '(?E:id)' is a nifty
            way to match account names.
  comment - Content following #, ;, or //, possibly preceded by
            whitespace.

Network:
  ipv4     - E.g. "1.2.3.4".
  ipv6     - E.g. "1234:5678:9abc:DEF0:2:345".
  ipaddr   - Matches either ipv4 or ipv6.
  cidr     - E.g. "1.2.3.4/24".
  macaddr  - Looks a lot like ipv6, but the colons may also 
             be dashes or dots instead.
  hostname - A DNS name.
  host     - Matches either hostname or ipaddr.
  service  - Matches host:port.
  email    - Any valid email address. This RE is well above average, but
             not quite perfect. There's also an email_localpart
             extension, which is used inside both "email" and "url"
             (below), but it's really just for internal use. Take a look
             if you're curious.
  url      - Any URL consisting of:
               protocol - req (e.g. "http" or "presto:http:")
               designator - req (either "email_localpart@" or "//")
               host - req (anything matching our "host" extension)
               port - opt (e.g. ":443")
               path - opt (e.g. "/path/to/content.html")
               params - opt (e.g. "q=regular%20expression&items=10")

Time and Date:
  day      - Day of week, Sunday through Saturday, or any unambiguous
             prefix thereof.
  day3     - Firt three letters of any month.
  DAY      - Full name of day of week.
  month    - January through December, or any unambiguous prefix
             thereof.
  month3   - First three letters of any month.
  MONTH    - Full name of any month.
  date_YMD - [CC]YY(-|/|.)[M]M(-|/|.)[D]D
  date_YmD - [CC]YY(-|/|.)month(-|/|.)[D]D
  date_mD  - "month DD"
  time_HM  - [H]H(-|:|.)MM
  time_HMS - [H]H(-|:|.)MM(-|:|.)SS

Some of these preloaded RE extensions are computed directly in the
module. For instance the day, day3, DAY, month, month3, and MONTH
extensions are computed according to the current locale when this module
loads. The rest are loaded from /etc/RE.rc and/or ~/.RE.rc (in that
order). For this to work, you need to copy the .RE.rc file that came
with this module to your home directory or copy it to /etc/RE.rc. Or
make your own. It's up to you.

"""

from datetime import date # We use day- and month-names of the current locale.
import re,os
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
  "read_extensions",
  "search",
  "split",
  "sub",
  "subn",
  "template",
#  "Error",
  "I","IGNORECASE", #   2
  "L","LOCALE",     #   4
  "M","MULTILINE",  #   8
  "S","DOTALL",     #  16
  "U","UNICODE",    #  32
  "X","VERBOSE",    #  64
  "DEBUG",          # 128
  "_extensions",
]

#class Error(Exception):
#  pass

# This dictionary holds all extensions, keyed by name.
_extensions={}

# This RE matches an RE extension, possibly in a larger string.
_extpat=re.compile(r'(\(\?E:[_A-Za-z][_A-Za-z0-9]*(=[_A-Za-z][_A-Za-z0-9]*)?\))')

# This RE matches a line in /etc/RE.rc and ~/.RE.rc.
_extdef=re.compile(r'^\s*([_A-Za-z][_A-Za-z0-9]*)\s*([=<])(.*)$')

# This RE matches blank lines and comments in /etc/RE.rc and ~/.RE.rc.
_extcmt=re.compile(r'^\s*(([#;]|//).*)?$')
                                           
def _apply_extensions(pattern,allow_named=True):
  """Return the given pattern with all regexp extension references
  expanded."""

  outer=True
  while True:
    extensions=set([r[0] for r in _extpat.findall(pattern)])
    if not extensions:
      break;
    for ref in extensions:
      ext=ref[4:-1]
      #print('D: ext=%r'%(ext,))
      if not ext:
        raise error('RE extension name is empty')
      if '=' in ext:
        label,ext=ext.split('=')
      else:
        label=None
      #print('D: label=%r, ext=%r'%(label,ext))
      if ext not in _extensions:
        raise error('Unregistered RE extension %r'%(ext,))
      if label and outer and allow_named:
        pattern=pattern.replace(ref,'(?P<%s>%s)'%(label,_extensions[ext]))
      else:
        pattern=pattern.replace(ref,'(%s)'%(_extensions[ext],))
    outer=False
  return pattern

def extend(name,pattern,expand=False):
  """Register an extension regexp pattern that can be referenced with
  the "(?E:name)" extension construct. You can call RE.extend() like
  this:

      RE.extend('id',r'[-_0-9A-Za-z]+')

  This registers a regexp extension named id with a regexp value of
  r'[-_0-9A-Za-z]+'. This means that rather than using r'[-_0-9A-Za-z]+'
  in every regexp where you need to match a username, you can use
  r'(?E:id)' or maybe r'(?E:user=id)' instead. The first form is
  simply expanded to

      r'([-_0-9A-Za-z]+)'

  Notice that parentheses are used so this becomes a regexp group. If
  you use the r'(?E:user=id)' form of the id regexp extension, it is
  expanded to

      r'(?P<user>[-_0-9A-Za-z]+)'

  In addition to being a parenthesized regexp group, this is a *named*
  group that can be retrived by the match object's groupdict() method.

  Normally, the pattern parameter is stored directly in this module's
  extension registry (see RE._extensions). If the expand parameter is
  True, any regexp extensions in the pattern are expanded before being
  added to the registry. So for example,

      RE.extend('cred',r'^\s*cred\s*=\s*(?E:id):(.*)$')

  will simply store that regular expression in the registry labeled as
  "cred". But if you register it this way,

      RE.extend('cred',r'^\s*cred\s*=\s*(?E:id):(.*)$',expand=True)

  this expands the regexp extension before registering it, which means
  this is what's stored in the registry:

      r'^\s*cred\s*=\s*([-_0-9A-Za-z]+):(.*)$'

  The result of using '(?E:cred)' in a regular expression is exactly
  the same in either case.

  If the pattern argument is None, and the value of the name parameter
  is already in the registry, it is de-registered.
  """

  if not pattern:
    # Remove name if it's already defined.
    if name in _extensions:
      del _extensions[name]
  else:
    # Add this named extension.
    if expand:
      pattern=_apply_extensions(pattern)
    _extensions[name]=pattern

def read_extensions(filename='~/.RE.rc'):
  """Read RE extension definitions from the given file. The default
  file is ~/.RE.rc."""

  filename=os.path.expanduser(filename)
  if os.path.isfile(filename):
    with open(filename) as f:
      count=0
      for line in f:
        count+=1
        if _extcmt.match(line):
          continue;
        m=_extdef.match(line)
        if not m:
          #raise error('%s: Bad extension in line %d: "%s"'%(filename,count,line.rstrip()))
          raise error(f"{filename}: Bad extension in line {count}: {line.rstrip()!r}")
        name,op,pat=m.groups()
        extend(name,pat,expand=op=='<')

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

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Compute some extensions that are a pain to compose manually.

# TODO: Compute the "day" and "month" extensions like we're doing for day3,
# DAY, month3, and MONTH below. The way we're doing it now only kind of works.

# Day, date, and time matching are furtile ground for improvement.
# day = SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY
#       Case doesn't matter, and any distinct beginning of those day names is
#       sufficient to match.
dnames=[date(2001,1,x+7).strftime('%A').lower() for x in range(7)]
extend('day',r'(([Ss][Uu]|[Mm]|[Tt][Uu]|[Ww]|[Tt][Hh]|[Ff]|[Ss][Aa])[AEDIONSRUTYaedionsruty]*)')
extend('day3',r'(%s)'%'|'.join(['(%s)'%''.join(['[%s%s]'%(c.upper(),c) for c in d[:3]]) for d in dnames]))
extend('DAY',r'(%s)'%'|'.join(['(%s)'%''.join(['[%s%s]'%(c.upper(),c) for c in d]) for d in dnames]))
# month = JANUARY|FEBRUARY|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER
#         This works just like the day extension, but for month names.
mnames=[date(2001,x,1).strftime('%B').lower() for x in range(1,13)]
extend('month',r'(([Jj][Aa]|[Ff]|[Mm][Aa][Rr]|[Aa][Pp]|[Mm][Aa][Yy]|[Jj][Uu][Nn]|[Jj][Uu][Ll]|[Aa][Uu]|[Ss]|[Oo]|[Nn]|[Dd])[ACBEGIHMLONPSRUTVYacbegihmlonpsrutvy]*)')
# month3=JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC
extend('month3',r'(%s)'%'|'.join(['(%s)'%''.join(['[%s%s]'%(c.upper(),c) for c in m[:3]]) for m in mnames]))
extend('MONTH',r'(%s)'%'|'.join(['(%s)'%''.join(['[%s%s]'%(c.upper(),c) for c in m]) for m in mnames]))

if False: # These are defined in ~/.RE.rc now.
  # Account names.
  extend('id',r'[-_0-9A-Za-z]+')
  # Python (Java, C, et al.) identifiers.
  extend('ident',r'[_A-Za-z][_0-9A-Za-z]+')

  # Comments may begin with #, ;, or // and continue to the end of the line.
  # If you need to handle multi-line comments ... feel free to roll your own
  # extension for that. (It CAN be done.)
  extend('comment',r'\s*([#;]|//).*')

  # Network
  extend('ipv4',r'\.'.join([r'\d{1,3}']*4))
  extend('ipv6',':'.join([r'[0-9A-Fa-f]{1,4}']*8))
  extend('ipaddr',r'(?E:ipv4)|(?E:ipv6)')
  extend('cidr',r'(?E:ipv4)/\d{1,2}')
  extend('macaddr48','(%s)|(%s)|(%s)'%(
    '[-:]'.join(['([0-9A-Fa-f]{2})']*6),
    '[-:]'.join(['([0-9A-Fa-f]{3})']*4),
    r'\.'.join(['([0-9A-Fa-f]{4})']*3)
  ))
  extend('macaddr64','(%s)|(%s)'%(
    '[-:.]'.join(['([0-9A-Fa-f]{2})']*8),
    '[-:.]'.join(['([0-9A-Fa-f]{4})']*4)
  ))
  extend('macaddr',r'(?E:macaddr48)|(?E:macaddr64)')
  extend('hostname',r'[0-9A-Za-z]+(\.[-0-9A-Za-z]+)*')
  extend('host','(?E:ipaddr)|(?E:hostname)')
  extend('service','(?E:host):\d+')
  extend('hostport','(?E:host)(:(\d{1,5}))?') # Host and optional port.
  extend('filename',r'[^/]+')
  extend('path',r'/?(?E:filename)(/(?E:filename))*')
  extend('abspath',r'/(?E:filename)(/(?E:filename))*')
  extend('email_localpart',
    r"(\(.*\))?" # Comments are allowed in email addresses. Who knew!?
    r"([0-9A-Za-z!#$%&'*+-/=?^_`{|}~]+)"
    r"(\.([0-9A-Za-z!#$%&'*+-/=?^_`{|}~])+)*"
    r"(\(.*\))?" # The comment is either before or after the local part.
    r"@"
  )
  extend('email',r"(?E:email_localpart)(?E:hostport)")
  extend('url_scheme',r'([A-Za-z]([-+.]?[0-9A-Za-z]+)*:){1,2}')
  extend('url',
    r'(?E:url_scheme)'             # E.g. 'http:' or 'presto:http:'.
    r'((?E:email_localpart)|(//))' # Allows both 'mailto:addr' and 'http://host'.
    r'(?E:hostport)?'              # Host (required) and port (optional).
    r'(?E:abspath)?'               # Any path that MIGHT follow all that.
    r'(\?'                         # Any parameters that MIGHT be present.
      r'((.+?)=([^&]*))'
      r'(&((.+?)=([^&]*)))*'
    r')?'
  )
     #r'(([^=]+)=([^&]*))'
     #r'(&(([^=]+)=([^&]*)))*'

  # date_YMD = [CC]YY(-|/|.)[M]M(-|/|.)[D]D
  #            Wow. the BNF format is uglier than the regexp. Just think YYYY-MM-DD
  #            where the dashes can be / or . instead.
  extend('date_YMD',r'(\d{2}(\d{2})?)([-/.])(\d{1,2})([-/.])(\d{1,2})')
  # date_YmD is basically "[CC]YY-mon-DD" where mon is the name of a month as
  # defined by the "month" extension above.
  extend('date_YmD',r'(\d{2}(\d{2})?)([-/.])((?E:month))([-/.])(\d{1,2})')
  # date_mD is basically "mon DD" where mon is the name of a month as defined by
  # the "month" extension above.
  extend('date_mD',r'(?E:month)\s+(\d{1,2})')
  # time_HMS = HH:MM:SS
  # time_HM = HH:MM
  #            12- or 24-hour time will do, and the : can be . or - instead.
  extend('time_HM',r'(\d{1,2})([-:.])(\d{2})')
  extend('time_HMS',r'(\d{1,2})([-:.])(\d{2})([-:.])(\d{2})')

# TODO: Parse https://www.timeanddate.com/time/zones/ for TZ data, and hardcode
# that into a regexp extension here.

read_extensions('/etc/RE.rc')
read_extensions()

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Behave like a command if we're being called as one.
#
if __name__=='__main__':
  import argparse,os,sys
  from debug import DebugChannel
  from doctest import testmod
  from english import nounf
  from handy import ProgInfo,die

  prog=ProgInfo()

  def grep(opt):
    "Find all matching conent according to the given argparse namespace."

    def output(line,tgroups,dgroups):
      "This sub-function helps us implement the -v option."

      if not (opt.count or opt.list):
        # Show each match.
        if opt.fmt and (tgroups or dgroups):
          line=opt.fmt.format(line,*tgroups,**dgroups)
        if opt.tuple or opt.dict:
          print('')
        if opt.tuple:
          print((repr(m.groups())))
        if opt.dict:
          print(('{%s}'%', '.join([
            f'"{k}": "{v}"' for k,v in sorted(dgroups.items())
          ])))
        if show_filename:
          print(f"{fn}: {line}")
        else:
          print(line)

    opt.re_flags=0
    if opt.ignore_case:
      opt.re_flags|=re.IGNORECASE
    if dc:
      dc('Options').indent(1)
      dc('count=%r'%(opt.count,))
      dc('fmt=%r'%(opt.fmt,))
      dc('tuple=%r'%(opt.tuple,))
      dc('dict=%r'%(opt.dict,))
      dc('ignore_case=%r'%(opt.ignore_case,))
      dc('invert=%r'%(opt.invert,))
      dc('ext=%r'%(opt.ext,))
      dc('extensions=%r'%(opt.extensions,))
      dc('re_flags=%r'%(opt.re_flags,))
      dc.indent(-1)('Aguements').indent(1)
      dc('pattern=%r'%(opt.pattern,))
      dc('filenames=%r'%(opt.filenames,))
      dc.indent(-1)

    all_matches=0 # Total matches over all scanned input files.
    if not opt.pattern:
      die("No regular expression given.")
    pat=compile(opt.pattern,opt.re_flags)
    opt.filenames=[a for a in opt.filenames if not os.path.isdir(a)]
    show_filename=False
    if len(opt.filenames)<1:
      opt.filenames.append('-')
    elif len(opt.filenames)>1 and not opt.one:
      show_filename=True

    for fn in opt.filenames:
      matches=0 # Matches found in this file.
      if fn=='-':
        fn='stdin'
        f=sys.stdin
      else:
        f=open(fn)
      for line in f:
        if line[-1]=='\n':
          line=line[:-1]
        m=pat.search(line)
        if bool(m)!=bool(opt.invert):
          matches+=1
          if m:
            output(line,m.groups(),m.groupdict())
          else:
            output(line,(),{})
      if matches:
        if opt.count:
          if show_filename:
            print(('%s: %d'%(fn,matches)))
          else:
            print(('%d'%matches))
        elif opt.list:
          print(fn)
      all_matches+=matches
      if fn!='stdin':
        f.close()

    sys.exit((0,1)[all_matches==0])

  def test(opt):
    """
    >>> # Just to make testing dict result values predictable ...
    >>> def sdict(d):print('{%s}'%(', '.join(['%r: %r'%(k,v) for k,v in sorted(d.items())])))
    >>> # Basic expansion of a registered extension.
    >>> _apply_extensions(r'user=(?E:user=id)')
    'user=(?P<user>[-_0-9A-Za-z]+)'
    >>> _apply_extensions(r'user=(?E:id)')
    'user=([-_0-9A-Za-z]+)'
    >>> # "id"
    >>> s='    user=account123, client=123.45.6.78     '
    >>> m=search(r'user=(?E:user=id)',s)
    >>> m.groups()
    ('account123',)
    >>> b,e=m.span()
    >>> s[b:e]
    'user=account123'
    >>> # "id" combined wih "ipv4"
    >>> m=search(r'user=(?E:user=id),\s*client=(?E:client=ipv4)',s)
    >>> m.groups()
    ('account123', '123.45.6.78')
    >>> sdict(m.groupdict())
    {'client': '123.45.6.78', 'user': 'account123'}
    >>> s='x=5 # This is a comment.    '
    >>> m=search(r'(?E:comment)',s)
    >>> s[:m.span()[0]]
    'x=5'
    >>> # "cidr"
    >>>
    match(r'subnet=(?E:net=cidr)','subnet=123.45.6.78/24').groupdict()['net']
    '123.45.6.78/24'
    >>> # "ipv6"
    >>> s='client=2001:0db8:85A3:0000:0000:8a2e:0370:7334'
    >>> p=compile(r'client=(?E:client=ipv6)')
    >>> m=p.match(s)
    >>> m.groups()
    ('2001:0db8:85A3:0000:0000:8a2e:0370:7334',)
    >>> m.groupdict()['client']==m.groups()[0]
    True
    >>> b,e=m.span()
    >>> s[b:e]==s
    True
    >>> # "ipaddr". This really starts to show off how powerful these
    >>> # extensions can be. If you don't believe what a step-saver this is,
    >>> # run RE._expand_extensions the regexp that's compiled below.
    >>> s='server=2001:0db8:85A3:0000:0000:8a2e:0370:7334, client=123.45.6.78'
    >>> p=compile(r'server=(?E:srv=ipaddr),\s*client=(?E:cli=ipaddr)')
    >>> m=p.match(s)
    >>> m.groups()
    ('2001:0db8:85A3:0000:0000:8a2e:0370:7334', None, '2001:0db8:85A3:0000:0000:8a2e:0370:7334', '123.45.6.78', '123.45.6.78', None)
    >>> sdict(m.groupdict())
    {'cli': '123.45.6.78', 'srv': '2001:0db8:85A3:0000:0000:8a2e:0370:7334'}
    >>> # "macaddr48"
    >>> s='from 01:23:45:67:89:aB to 012-345-678-9aB via 0123.4567.89aB'
    >>> p=r'from\s+(?E:from=macaddr48)\s+to\s+(?E:to=macaddr48)\s+via\s+(?E:mid=macaddr48)'
    >>> sdict(search(p,s).groupdict())
    {'from': '01:23:45:67:89:aB', 'mid': '0123.4567.89aB', 'to': '012-345-678-9aB'}
    >>> # "macaddr64"
    >>> s='from 01:23:45:67:89:ab:cd:EF to 0123.4567.89ab.cdEF'
    >>> p=r'from\s+(?E:from=macaddr64)\s+to\s+(?E:to=macaddr64)'
    >>> sdict(match(p,s).groupdict())
    {'from': '01:23:45:67:89:ab:cd:EF', 'to': '0123.4567.89ab.cdEF'}
    >>> # "macaddr". Again, this is a pretty big regexp that we're getting for
    >>> # very little effort.
    >>> s='from 01:23:45:67:89:ab:cd:EF to 01:23:45:67:89:aB'
    >>> p=r'from\s+(?E:src=macaddr)\s+to\s+(?E:dst=macaddr)'
    >>> sdict(search(p,s).groupdict())
    {'dst': '01:23:45:67:89:aB', 'src': '01:23:45:67:89:ab:cd:EF'}
    >>> # "hostname". This should match any valid DNS name.
    >>> p='\s*host\s*[ :=]?\s*(?E:host=hostname)'
    >>> match(p,'host=this.is.a.test').groupdict()['host']
    'this.is.a.test'
    >>> # "host". Matches "ipaddr" or "hostname".
    >>> p='\s*host\s*[ :=]?\s*(?E:host=host)'
    >>> match(p,'host=this.is.a.test').groupdict()['host']
    'this.is.a.test'
    >>> s='host=123.45.6.78'
    >>> match(p,'host=123.45.6.78').groupdict()['host']
    '123.45.6.78'
    >>> # "hostport". Just like "host", but you can specify a port.
    >>> p='\s*host\s*[ :=]\s*(?E:host=hostport)'
    >>> match(p,'host=this.is.a.test').groupdict()['host']
    'this.is.a.test'
    >>> match(p,'host=123.45.6.78').groupdict()['host']
    '123.45.6.78'
    >>> match(p,'host=this.is.a.test:123').groupdict()['host']
    'this.is.a.test:123'
    >>> match(p,'host=123.45.6.78:99').groupdict()['host']
    '123.45.6.78:99'
    >>> # "filename"
    >>> p='\s*file\s*[ :=]\s*(?E:file=filename)'
    >>> search(p,'file=.file-name.EXT').groupdict()['file']
    '.file-name.EXT'
    >>> # "path"
    >>> p='\s*file\s*[ :=]\s*(?E:file=path)'
    >>> search(p,'file=.file-name.EXT').groupdict()['file']
    '.file-name.EXT'
    >>> search(p,'file=dir1/dir2/file-name.EXT').groupdict()['file']
    'dir1/dir2/file-name.EXT'
    >>> search(p,'file=/dir1/dir2/file-name.EXT').groupdict()['file']
    '/dir1/dir2/file-name.EXT'
    >>> # "abspath"
    >>> p='\s*file\s*[ :=]\s*(?E:file=abspath)'
    >>> search(p,'file=/dir1/dir2/file-name.EXT').groupdict()['file']
    '/dir1/dir2/file-name.EXT'
    >>> print(search(p,'file=dir1/dir2/file-name.EXT'))
    None
    >>> # "email_localpart"
    >>> p='from: (?E:from=email_localpart)'
    >>> match(p,'from: some.person@').groupdict()['from']
    'some.person@'
    >>> match(p,'from: (comment)some.person@').groupdict()['from']
    '(comment)some.person@'
    >>> match(p,'from: some.person(comment)@').groupdict()['from']
    'some.person(comment)@'
    >>> # "email"
    >>> p='from: (?E:from=email)'
    >>> match(p,'from: some.person@someplace').groupdict()['from']
    'some.person@someplace'
    >>> match(p,'from: (comment)some.person@someplace').groupdict()['from']
    '(comment)some.person@someplace'
    >>> match(p,'from: some.person(comment)@someplace').groupdict()['from']
    'some.person(comment)@someplace'
    >>> # "url_scheme"
    >>> p='(?E:proto=url_scheme)'
    >>> match(p,'http:').groupdict()['proto']
    'http:'
    >>> match(p,'ht-tp:').groupdict()['proto']
    'ht-tp:'
    >>> match(p,'h.t-t+p:').groupdict()['proto']
    'h.t-t+p:'
    >>> print(match(p,'-http:'))
    None
    >>> print(match(p,'http-:'))
    None
    >>> match(p,'presto:http:').groupdict()['proto']
    'presto:http:'
    >>> # "url"
    >>> p='(?E:url=url)'
    >>> search(p,'mailto:some.person@someplace.com').groupdict()['url']
    'mailto:some.person@someplace.com'
    >>> search(p,'mailto:some.person@someplace.com?to=me').groupdict()['url']
    'mailto:some.person@someplace.com?to=me'
    >>> search(p,'mailto:some.person@someplace.com?to=me&subject=testing').groupdict()['url']
    'mailto:some.person@someplace.com?to=me&subject=testing'
    >>> search(p,'ftp://vault.com').groupdict()['url']
    'ftp://vault.com'
    >>> search(p,'ftp://vault.com:500').groupdict()['url']
    'ftp://vault.com:500'
    >>> search(p,'ftp://vault.com:500/file').groupdict()['url']
    'ftp://vault.com:500/file'
    >>> search(p,'ftp://vault.com/file').groupdict()['url']
    'ftp://vault.com/file'
    >>> search(p,'ftp://vault.com/path/to/file').groupdict()['url']
    'ftp://vault.com/path/to/file'
    >>> search(p,'ftp://vault.com/path/to/file?encrypt=1').groupdict()['url']
    'ftp://vault.com/path/to/file?encrypt=1'
    >>> search(p,'ftp://vault.com/path/to/file?encrypt=1&compress=0').groupdict()['url']
    'ftp://vault.com/path/to/file?encrypt=1&compress=0'
    >>> # There's somethin screwey with they way we're matching URL parameters.
    >>> # Maybe we need a url_path (rather than abs_path) that rejects ? as a
    >>> # valid character. (And of course, we're not handling escaping at all,
    >>> # but I'm not sure that can even be expressed regularly.)
    >>> #search(p,'ftp://vault.com/path/to/file?encrypt=1&compress=0').groups()
    >>> p='(?E:day=day)'
    >>> search(p,'Sunday').groupdict()['day']
    'Sunday'
    >>> search(p,'Sun').groupdict()['day']
    'Sun'
    >>> search(p,'M').groupdict()['day']
    'M'
    >>> search(p,'m').groupdict()['day']
    'm'
    >>> search(p,'tuesday').groupdict()['day']
    'tuesday'
    >>> search(p,'tu').groupdict()['day']
    'tu'
    >>> p='(?E:day=day3)'
    >>> search(p,'Sun').groupdict()['day']
    'Sun'
    >>> search(p,'sun').groupdict()['day']
    'sun'
    >>> search(p,'tu')==None
    True
    >>> p='(?E:month=month)'
    >>> search(p,'January').groupdict()['month']
    'January'
    >>> search(p,'ja').groupdict()['month']
    'ja'
    >>> search(p,'May').groupdict()['month']
    'May'
    >>> search(p,'D').groupdict()['month']
    'D'
    >>> p='(?E:month=month3)'
    >>> search(p,'Jan').groupdict()['month']
    'Jan'
    >>> search(p,'ja')==None
    True
    >>> search(p,'May').groupdict()['month']
    'May'
    >>> search(p,'Dec').groupdict()['month']
    'Dec'
    """

    f,t=testmod(report=False)
    if f>0:
      print("---------------------------------------------------------------------\n")
    print(("Passed %d of %s."%(t-f,nounf('test',t))))
    sys.exit((1,0)[f==0])

   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # Parse our command line using an ArgumentParser instance with subparsers. If
  # This command was symlinked to the name of one of the subparsers, then allow
  # only the options for that subparser.

  dc=DebugChannel(label='D',enabled=True)

  ap=argparse.ArgumentParser()
  ap.add_argument('--debug',action='store_true',help="Turn on debug messages.")
  ap.add_argument('-x',dest='ext',action='append',default=[],help="""Add a "name=pattern" RE extension. Use as many -x options as you need.""")
  ap.add_argument('--extensions',action='store_true',help="List our RE extensions.")

  if prog.name==prog.real_name:
    sp=ap.add_subparsers()
    ap_find=sp.add_parser('grep',description="This works a lot like grep.")
    ap_test=sp.add_parser('test',description="Just run internal tests and report the result.")
  elif prog.name=='pygrep':
    ap_find=ap # Add "find" subparser's opttions to the main parser.
    ap_find.description="This works a lot like grep (but without so many features."
  elif prog.name=='test':
    ap_test=ap
  
  if prog.name in (prog.real_name,'pygrep'):
    ap_find.set_defaults(func=grep)
    ap_find.add_argument('-1',dest='one',action='store_true',help="Do not output names of files containing matches, even if more than one file is to be scanned.")
    ap_find.add_argument('-c',dest='count',action='store_true',help="Output only the number of matching lines of each file scanned.")
    ap_find.add_argument('-f',dest='fmt',action='store',help="Use standard Python template syntax to format output.")
    ap_find.add_argument('-g',dest='tuple',action='store_true',help='Output the tuple of matching groups above each matching line.')
    ap_find.add_argument('-G',dest='dict',action='store_true',help='Output the dictionary of matching groups above each matching line.')
    ap_find.add_argument('-i',dest='ignore_case',action='store_true',help="Ignore the case of alphabetic characters when scanning.")
    ap_find.add_argument('-l',dest='list',action='store_true',help="Output only the name of each file scanned. (Trumps -1.)")
    ap_find.add_argument('-v',dest='invert',action='store_true',help="Output (or count) non-matching lines rather than matching lines.")
    ap_find.add_argument('pattern',metavar='RE',action='store',nargs='?',help="A regular expression of the Python dialect, which can also include RE extensions.")
    ap_find.add_argument('filenames',metavar='FILENAME',action='store',nargs='*',help="Optional filenames to scan for the given pattern.")
  if prog.name in (prog.real_name,'test'):
    ap_test.set_defaults(func=test)

  #from pprint import pprint
  #pprint(ap.__dict__)
  opt=ap.parse_args()
  dc.enable(opt.debug)
  
  for x in opt.ext:
    name,pat=x.split('=',1)
    dc('Registering RE %r as "%s"'%(name,pat))
    extend(name,pat)
  if opt.extensions:
    print(('\n'.join(['%s=%s'%(n,p) for n,p in sorted(_extensions.items())])))
    sys.exit(0)

   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # Do whatever our command line says.
  if hasattr(opt,'func'):
    opt.func(opt)
