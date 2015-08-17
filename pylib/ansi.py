#!/usr/bin/env python

"""
Use this module to output ANSI escape sequences that control the
attributes a terminal uses when printing text. Attributes include things
like bold, italics, underline, and reverse as well as foreground and
background color.

You can use the low-level function color(attrib,foreground,background)
to get the ANSI escape string for those attributes. Any of them may be
None to leave them unspecified.

Example: Output some text in bold red on yellow.

    import ansi
    print ansi.color('bold','red','yellow')+'Error message'+ansi.norm


You could use the mid-level parseColor(spec) function to do the same
thing like this:

    import ansi,sys
    sys.stdout.write(ansi.color(*ansi.parseColor('bold red on yellow')))
    print 'Error message'+ansi.norm


The general syntax parseColor()'s spec argument is "[ATTR] FG [on BG]",
so that the attribute and background are optional, while the foreground
color is required.

There's also the notion of a color palette that you can create with the
parsePalette(spec) function. The spec argument of this function is the
same as for parseColor(spec), but there are commas between the entries.
For example:

    import ansi

    palette=ansi.parsePalette(
      'norm green on black, bold yellow, white on red'
    )
    NORM,WARN,ERROR=0,1,2

    def paint(color,message):
      print palette[color]+message+ansi.norm

    paint(NORM,"This is normal text.")
    paint(WARN,"This is only a warning ... this time.")
    paint(ERROR,"This is an error message. No soup for you!")


Notice that when specifying a palette all at once, attribute and
background are persistent from the previous entry. We start by giving
everything about the NORM text (normal attribute, green foreground, and
black background). The next entry, WARN, specifies a bold yellow
foreground and keeps the black background from the first entry. The last
entry, ERROR, keeps "bold" from the WARN entry and then specifies a
white foreground on a red background.

Another option for parsePalette(spec) is us specify either "dark" or
"light". The author is very lazy, usually uses terminals with dark
backgrounds, and likes to be able to call ansi.parsePalette('dark') to
set things up. The 'light' spec is supposed to work well with
light-background terminals, but ... why would anyone need that? There's
also an ansi.default_palette list, also the product of laziness and
abuse of position as author.

"""

# ANSI color escape sequences:
attr=dict(
normal='0',
bold='1',
faint='2',
italics='3',
underline='4',
blink='5',
fastblink='6',
reverse='7',
hidden='8',
strikethrough='9',
)
foreground=dict(
black='30',
red='31',
green='32',
yellow='33',
blue='34',
magenta='35',
cyan='36',
white='37',
)
background=dict(
black='40',
red='41',
green='42',
yellow='43',
blue='44',
magenta='45',
cyan='46',
white='47',
)
norm='\033['+attr['normal']+'m'

dark='norm red on black,green,yellow,bold blue,norm magenta,cyan,white'
light='norm red on white,green,blue,magenta,black'

class AnsiException(Exception):
  pass

def englishList(l,conj='and'):
  "Return a string listing all elements of l in English."

  if len(l)<1:    s=''
  elif len(l)==1: s=str(l[0])
  elif len(l)==2: s='%s %s %s'%(l[0],conj,l[1])
  else:           s='%s %s %s'%(', '.join(l[:-1]),conj,l[-1])
  return s

def complete(word,wordlist):
  'Return a list of words from wordlist that begin with word.'

  l=[x for x in wordlist if x.startswith(word)] # Find anything that might fit.
  if len(l)<1:
    raise AnsiException("I don't understand %r. Choices are %s"%(word,englishList(wordlist)))
  if len(l)>1:
    raise AnsiException("%r is ambiguous. Choose from %s"%(word,englishList(l)))
  return l[0]

def parseColor(spec):
  '''Return the (attr,foreground,background) components from the colorspec.
  
  The spec argument is of the form "[ATTR] FG [on BG]", specifying
  attribute values of normal, bold, faint, italics, underline, blink,
  fastblink, reverse, hidden, or strikethrough and foreground and
  background values of black, red, green, yellow, blue, magenta, cyan,
  or white. The foreground is the only required part of the spec string.
  (Note that not all terminals will recognize all attribute values.)'''

  # Set up defaults, and lower-case our colorspec.
  a=f=b=None
  spec=spec.lower()

  # Separate the attribute and foreground from the background.
  l=spec.strip().split('on')
  if len(l)>2:
    raise AnsiException('bad colorspec "%s"'%spec)
  if len(l)>1:
    f,b=[x.strip() for x in l]
  else:
    f=l[0]

  # Separate the attribute and foreground.
  l=f.split()
  if len(l)>2:
    raise AnsiException('bad colorspec "%s"'%spec)
  if len(l)>1:
    a,f=l
  elif len(l)==1:
    f=l[0]
  else:
    raise AnsiException('bad colorspec "%s"'%spec)

  # Complete any partial attribute or color names.
  if a!=None:
    a=complete(a,attr.keys())
  f=complete(f,foreground.keys())
  if b!=None:
    b=complete(b,background.keys())

  # Return our triplet of tokens.
  return (a,f,b)

def color(attrib,fg,bg):
  '''Return the ANSI color escape sequence that yields the given
  attribute, foreground, and background. Setting any of these to None
  excludes that component from being expressed in the returned string.
  
  >>> color('normal','white','black')=='\x1b[0;37;40m'
  True
  >>> color(None,'white','black')=='\x1b[37;40m'
  True
  >>> color('normal',None,'black')=='\x1b[0;40m'
  True
  >>> color('normal','white',None)=='\x1b[0;37m'
  True
  >>> color('normal',None,None)=='\x1b[0m'
  True
  >>> color(None,'white',None)=='\x1b[37m'
  True
  >>> color(None,None,'black')=='\x1b[40m'
  True
  '''

  s='\x1b['
  s+=';'.join([
    d[k] for d,k in (
      (attr,attrib),
      (foreground,fg),
      (background,bg)
    ) if d.get(k)
  ])
  s+='m'
  return s

def parsePalette(spec):
  '''Return a list of (attr,fg,bg) tuples for as many comma-separated
  ANSI color specs as are found in the spec string argument.'''

  palette=[]
  if spec=='dark':
    spec=dark
    prev_attr,prev_fg,prev_bg='normal','white','black'
  elif spec=='light':
    spec=light
    prev_attr,prev_fg,prev_bg='normal','black','white'
  for color_spec in spec.split(','):
    a,f,b=parseColor(color_spec)
    if not a: a=prev_attr
    if not f: f=prev_fg
    if not b: b=prev_bg
    palette.append('\x1b[%s;%s;%sm'%(attr[a],foreground[f],background[b]))
    prev_attr,prev_fg,prev_bg=a,f,b
  return palette

default_palette=parsePalette('dark')

if __name__=='__main__':
  import doctest,sys
  failed,total=doctest.testmod()
  if len(sys.argv)>1:
    a,f,b=parseColor(' '.join(sys.argv[1:]))
    c=color(a,f,b)
    sys.stdout.write(c)
  if not sys.stdin.isatty():
    for line in sys.stdin:
      sys.stdout.write(line)
  sys.stdout.write(norm)
