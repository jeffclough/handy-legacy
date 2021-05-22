#!/usr/bin/env python

import argparse,csv,os,sys

import re
re_doc=re.__doc__
del re
import RE as re

import ansi
from debug import DebugChannel
from loggy import LogStream

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Help the user to grasp what a wonderful situation he's in.
#

def show_extensions():
  "List all RE extensions."

  names=re._extensions.keys()
  names.sort()
  for name in names:
    print("%s=%s"%(name,re._extensions[name]))

  sys.exit(0)

def show_syntax():
  """Send an excerpt of re's and RE's doc strings to standard output.
  Then terminate."""

  # Standard Python regular express syntax.
  print("PYTHON REGULAR EXPRESSION SYNTAX:")
  started=False
  url=None
  for line in re_doc.split('\n'):
    if started:
      if 'This module exports' in line:
        break;
      print(line)
    else:
      if 'Regular expressions can contain both' in line:
        print(line)
        started=True
      elif not url and 'https://docs.python.org' in line:
        url=line.strip()
  if url:
    print("""

You can read an expanded treatment of Python's regular expression
syntax at:
    %s#regular-expression-syntax

"""%(url,))

  # Regular expression extension syntax from RE.py.
  print("""- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

REGULAR EXPRESSION EXTENSIONS:
See the -x and --extensions options for how to register a new RE extension or
list all currently-registered RE extensions, but here's the gist. REs have a
pretty powerful syntax for expressing a text pattern to match, but these
expressions can also become cumbersome and error-prone when they get
complicated. Such regular expressions can be "registered" with this program
and then referred to by name whenever you need them. Here's an example:

Let's say you're scanning log files for client IP addresses. You could do
something like

    re find "client=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
or
    re find "client=(?P<client>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

to find the IP address as the first matched group or group named "client",
respectively. But wouldn't it be easier, less error-prone, and much more
readable to write

    re find "client=(?E:ipv4)"
or
    re find "client=(?E:client=ipv4)"

instead? The first method above captures the client IP address in the first
matching group. The second method captures it in a group named "client".

This type of RE extension syntax is available for any of the extensions listed
when you run

    re --extensions

That will list all extensions that are defined internally in this code, in
/etc/RE.rc, in ~/.RE.rc, or passed to the -x option of this command, where
each of those sources supersedes the one before it. Put extensions that should
be available to all users of this machine into /etc/RE.rc. Put extensions that
are just for your own use into ~/.RE.rc. If you just want to use an extension
for the current command, that's what the -x option is for.
""")

  sys.exit(0)

def show(opt):
  if opt.what=='extensions':
    show_extensions()
  elif opt.what=='syntax':
    show_syntax()
  else:
    assert False,"How did we get here?!"

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Run in grep mode.
#

def find(opt):
  "Find all matching content according to the given argparse namespace."

  def output(line,tgroups,dgroups):
    "This sub-function helps us implement the -v option."

    if not (opt.count or opt.list):
      # Show each match.
      if opt.fmt and (tgroups or dgroups):
        line=opt.fmt.format(line,*tgroups,**dgroups)
      if opt.tuple or opt.dict:
        print('')
      if opt.tuple:
        print(repr(m.groups()))
      if opt.dict:
        print('{%s}'%', '.join([
          '"%s": "%s"'%(k,v) for k,v in sorted(dgroups.items())
        ]))
      if show_filename:
        print('%s: %s'%(fn,line))
      else:
        print(line)

    opt.re_flags=0
    if opt.ignore_case:
      opt.re_flags|=re.IGNORECASE
    if bug:
      bug('Options').indent(1)
      bug('count=%r'%(opt.count,))
      bug('fmt=%r'%(opt.fmt,))
      bug('tuple=%r'%(opt.tuple,))
      bug('dict=%r'%(opt.dict,))
      bug('ignore_case=%r'%(opt.ignore_case,))
      bug('invert=%r'%(opt.invert,))
      bug('ext=%r'%(opt.ext,))
      bug('extensions=%r'%(opt.extensions,))
      bug('re_flags=%r'%(opt.re_flags,))
      bug.indent(-1)('Aguements').indent(1)
      bug('args=%r'%(opt.args,))
      bug.indent(-1)

    all_matches=0 # Total matches over all scanned input files.
    pat=compile(opt.args.pop(0),opt.re_flags)
    opt.args=[a for a in opt.args if not os.path.isdir(a)]
    show_filename=False
    if len(opt.args)<1:
      opt.args.append('-')
    elif len(opt.args)>1 and not opt.one:
      show_filename=True

    for fn in opt.args:
      matches=0 # Matches found in this file.
      if fn=='-':
        fn='stdin'
        f=sys.stdin
      else:
        f=file(fn)
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
            print('%s: %d'%(fn,matches))
          else:
            print('%d'%matches)
        elif opt.list:
          print(fn)
      all_matches+=matches
      if fn!='-':
        f.close()

    sys.exit((0,1)[all_matches==0])

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Run in mark mode.
#

def mark(opt):
  "Copy input text to standard output, coloring matching text as we go."

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Figure out what the user wants to do.
#

ap=argparse.ArgumentParser()
ap.add_argument('-d',metavar='TARGET',dest='debug',action='store',help="""Enable debug messages. TARGET can be either a filename (use - for standard output) or a syslog facility. It the later case, the argument must be in the form of "target=FACILITY". Using "target=local0" is usually a good choice.""")
ap.add_argument('-x',dest='extend',action='append',default=[],help="""Add a "name=pattern" RE extension. Use as many -x options as you need.""")
ap.add_argument('--extensions',action='store_true',help="List all RE extensions and terminate.")
ap.add_argument('--syntax',dest='re_help',action='store_true',default=False,help='''Display a brief description of Python regular expressions and our own RE extension syntax. Then quit.''')
sp=ap.add_subparsers()

ap_show=sp.add_parser('show',description="Output either regular express syntax help or our list of available RE extensions.")
ap_show.set_defaults(func=show)
ap_show.add_argument('what',action='store',choices=('extensions','syntax'))

ap_find=sp.add_parser('find',description="This works a lot like grep.")
ap_find.set_defaults(func=find)
ap_find.add_argument('-1',dest='one',action='store_true',help="Do not output names of files containing matches, even if more than one file is to be scanned.")
ap_find.add_argument('-c',dest='count',action='store_true',help="Output only the number of matching lines of each file scanned.")
ap_find.add_argument('-f',dest='fmt',action='store',help="Use standard Python template syntax to format output with groups as positional arguments and named groups as keyword arguments.")
ap_find.add_argument('-g',dest='tuple',action='store_true',help='Output the tuple of matching groups above each matching line.')
ap_find.add_argument('-G',dest='dict',action='store_true',help='Output the dictionary of matching groups above each matching line.')
ap_find.add_argument('-i',dest='ignore_case',action='store_true',help="Ignore the case of alphabetic characters when scanning.")
ap_find.add_argument('-l',dest='list',action='store_true',help="Output only the name of each file scanned where a match occurs. (Trumps -1.)")
ap_find.add_argument('-v',dest='invert',action='store_true',help="Output (or count) non-matching lines rather than matching lines.")
ap_find.add_argument('args',action='store',nargs='+',help="A regular expression, optionally followed by one or more names of files to be scanned.")

ap_mark=sp.add_parser('mark',description="Color matching text from a single input source against one or more patterns.")
ap_mark.set_defaults(func=mark)
ap_mark.add_argument('-b','--background',dest='background',choices=ansi.background.keys(),default='black',help='''Sets the assumed background color, which defaults to %(default)s. ASNI codes to effect the background color that's aready assumed will not be output.''')
ap_mark.add_argument('-C',dest='comment_mode',action='store_true',default=False,help='''Turns on comment mode, which inserts the comment pattern (see --comment-format) at the start of the pattern list. This marks any line whose first non-space character is '#', which is very commonly a comment line. Use the --comment option to change the pattern used to idententify comments.''')
ap_mark.add_argument('--columns',dest='columns',action='store',default=None,help='''This option turns on fixed-column mode and accepts a comma-separated list of column numbers as its argument. Each given column number identifies the beginning of a column in each line of the input data. This option cannot be used with other highlighting modes. The first column is numbered 1.''')
ap_mark.add_argument('--comment-format',dest='comment_format',action='store',default='^\s*(#|;|--|//).*',help='''Specifies the pattern used to identify comment lines, which is '%(default)s' by default.''')
ap_mark.add_argument('--after-context',dest='after',action='store',type=int,default=None,help='''Print NUM lines of leading context before matching lines. Places a line containing -- between contiguous groups of matches.''')
ap_mark.add_argument('--before-context',dest='before',action='store',type=int,default=None,help='''Print NUM lines of trailing context before matching lines. Places a line containing -- between contiguous groups of matches.''')
ap_mark.add_argument('--context',dest='context',action='store',type=int,default=None,help='''Print NUM lines of leading and trailing context before matching lines. Places a line containing -- between contiguous groups of matches. The context options are only useful in combination whth the --grep option.''')
ap_mark.add_argument('--csv',dest='csv',action='store_true',default=False,help='''For use with -f, this option specifies that the data is in CSV format.''')
ap_mark.add_argument('-d','--delimiter',dest='delim',default=None,help='''For use with -f, this option specifies a regular expression that matches field delimiters. The default is '\s+', which matches one or more whitespace characters.''')
ap_mark.add_argument('-D','--diff',dest='diff',action='store_true',default=False,help='''Turns on diff mode, which colors lines removed differently from lines added.''')
ap_mark.add_argument('--discard',dest='discard',metavar='RE',action='store',default=None,help='''Discards any lines matching the given RE and keeps all others. Discarding lines of CSV data has not yet been implemented. This option is for filtering only and has no effect on colarization. (Cannot be used with --keep.)''')
ap_mark.add_argument('-f','--fields',dest='fields',action='store',default=None,help='''Specifies which fields are to be marked. Field ranges are separated by commas and take the form "m[-[n]]" or "[[m]-]n" where m is the first column in the range (counted from 1) and n is the last. Each field *range* gets its own color. E.g., "-f 1-3,6" says to mark fields 1-3 with the first color in the current palette and to color field 6 with the second. See --csv and -d for data parsing options.''')
ap_mark.add_argument('--file',dest='file',action='store',default=None,help='''Read from the given file rather than standard input.''')
ap_mark.add_argument('-g','--grep',dest='grep',action='store_true',default=False,help='''Output only lines that match at least one color filter.''')
ap_mark.add_argument('-i',dest='ignore_case',action='store_true',default=False,help='''Ignore case when matching patterns. This applies both to RE arguments to be matched and to any argument to --discard or --keep.''')
ap_mark.add_argument('-I','--input',dest='input_from',action='store',choices=('diff','du'),default=None,help='''Use sets of pattern known to be helpful for marking the output of certain programs. Valid values are diff and du.''')
ap_mark.add_argument('--keep',dest='keep',metavar='RE',action='store',default=None,help='''Keep any lines matching the given RE and discards all others. Keeping lines of CSV data has not yet been implemented. This option is for filtering only and has no effect on colarization. (Cannot be used with --discard.)''')
ap_mark.add_argument('-L',dest='log_mode',action='store_true',default=False,help='''Turns on log mode, which marks error, warning, info, and debug output in addition to the time, host, and process conent. Also see --log-format. NOT YET FULLY IMPLEMENTED.''')
ap_mark.add_argument('--palette',dest='palette',action='store',default='dark',help='''Comma-delimited list of color specifications to use to highlight matches for patterns. Each spec is of the form "[ATTR] FG [on BG]" where ATTR is any of bold, italics, underscore, or strikethrough, and FG and BG may be any of black, red, green, yellow, blue, magenta, cyan, or white. Two other possible values for a colorspec can be "normal" and "reverse", which don't make sence with other ATTR, FB, or BG values. You should also know that ATTR, FG, and BG values are persistent from one spec to the next, so, for example "red on black,green,yellow" specifies that matches for the first pattern should be red, second pattern are green, third are yellow, and that all have black backgrounds. Since the palette syntax tends to be verbose, you can also use --palette=dark or --palette=light to use colors generally suitable for dark or light terminal backgrounds, respectively. Since only red, blue, and magenta are used on light backgrounds, using -w is often a good idea with --palette=light. The default setting is "%(default)s".''')
ap_mark.add_argument('-r','--reverse',dest='reverse',action='store_true',default=False,help='''Reverse foreground and background colors of highlighted sections.''')
ap_mark.add_argument('-s','--stanzas',dest='stanzas',action='store_true',default=False,help='''In "stanzas" mode, the the RE arguments are matched against input lines. Output lines are colored according to the most recent RE matched. If only one RE is given, output lines will alternate between the first two colors in thte palette every time the input line matches the RE.'''),
ap_mark.add_argument('--stripe',metavar='N',dest='stripe',type=int,default=None,help='''Color each group of N lines of text a different color, rotating through the default or given pallete as we go.''')
ap_mark.add_argument('--traffic',dest='traffic',action='store_true',default=False,help='''Mark instances of the words red, yellow, and green in their respective colors.''')
ap_mark.add_argument('-w',dest='wrap',action='store_true',default=False,help='''Turn on color wrapping mode. By default, for n colors in the palette, the match for any pattern beyond the nth pattern simply uses the last color in the palette. Wrapping mode changes this behavior so the first color is used for the n+1st pattern, the second for the n+2nd, and so on.''')
ap_mark.add_argument('--debug',dest='debug',action='store_true',default=False,help='''Turn on debug mode. Unless you're modifying the code for this command, you don't need this.''')
ap_mark.add_argument('patterns',nargs=argparse.REMAINDER)

# Parse our command line, and initialize whatever kind of debugging is called for.
opt=ap.parse_args()
if opt.debug:
  if 'facility=' in opt.debug:
    # Log to whatever syslog facility the user has requested.
    x=opt.debug[opt.debug.find('=')+1:]
    #print 'x=%r'%(x,)
    x=LogStream(facility=x,level='debug')
    #print 'x=%r'%(x,)
    bug=DebugChannel(True,x)
    bug.setFormat('{line}: {indent}{message}')
  elif opt.debug=='-':
    # Log to standard output.
    bug=DebugChannel(True,sys.stdout,label='D')
  else:
    # Log to whatever file the user has requested.
    bug=DebugChannel(True,open(opt.debug,'a+'))
    bug.setFormat('{line}: {indent}{message}')
else:
  bug=DebugChannel(False)

# Register RE extensions from any -x options we might find.
if opt.extend:
  for x in opt.extend:
    if '=' in x:
      x,y=x.split('=',1)
    re.extend(x,y)

# Run whatever function the user chose with whatever command line options were given.
opt.func(opt)
