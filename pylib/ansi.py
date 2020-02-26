#!/usr/bin/env python2

"""
This module is all about sending colored text to an ANSI-compatibe
terminal. You can control attributes (e.g. bold, italics, and
underscore), foreground color, and background color. Foreground and
background colors may be any of the strings: black, red, green, yellow,
blue, magenta, cyan, or white.

There are different ways to send colored text to the terminal. Calling
an instance of the Color class as a function returns a string with the
proper prefix to color the text and the proper suffix to turn that color
back off.

    import ansi
    print ansi.Color('bold','red','yellow')('Error message')

You can also assign Color instances to handy variables.

    import ansi
    error_text=Color('bold red on yellow')
    .
    .
    .
    print error_text(some_message)

You can turn off the effect of ALL Color objects by disabling the whole
ansi module.

    print error_text("This text will be colored.")
    ansi.enabled=False
    print error_text("This text will NOT be colored.")
    ansi.enabled=True
    print error_text("This text will AGAIN be colored.")

This makes it easy to manage whether your script's output is colored or
not without having to have a bunch of messy if statements.

You can also call ansi.paint(), which takes any number of arguments

    import ansi
    error_type=ansi.Color('bold red on yellow')
    error_msg=ansi.Color('bold white on red')
    ansi.paint(error_type,'Error:',error_msg,' message \n')

The Color class can express itself into a string when called upon to do
so, in which case it will yield the ANSI escape sequence to turn on the
attribute, foreground, and background it contains. If you pass a Color
object to repr(), you'll get a Python expression that can be used to
recreate that Color object.

There's also the notion of a color palette that you can create with the
Palette class. A Palette object is essentially a Python list of Color
objects and can be treated as such, e.g. using len() to count its
elements or its append() method to add to it.

A Palette class is can be created using, among other things, an
extension of Color's spec string. Just use the single-string version of
hte constructor, and separate the color spec strings with commas. Here's
an example:

    import ansi
    pal=ansi.Palette('norm green on black, bold yellow, white on red')
    NORM,WARN,ERROR=pal

    ansi.paint(NORM,"This is normal text.")
    ansi.paint(WARN,"This is only a warning ... this time.")
    ansi.paint(ERROR,"This is an error message. No soup for you!")

Notice that when specifying a palette all at once, attribute and
background are persistent from the previous entry. We start by giving
everything about the NORM text (normal attribute, green foreground, and
black background). The next entry, WARN, specifies a bold yellow
foreground and keeps the black background from the first entry. The last
entry, ERROR, keeps "bold" from the WARN entry and then specifies a
white foreground on a red background.

Another option for Palette's constructor's argument is to give either
"dark" or "light".  The author is very lazy, usually uses terminals with
dark backgrounds, and likes to be able to call ansi.parsePalette('dark')
to set things up. The "light" spec is supposed to work well with
light-background terminals, but ... why would anyone need that?

BE AWARE: The terminal in front of the user is ENTIRELY in control of
how these ANSI sequences are interpreted. For example, while you can
specify "white on white" or "bold white on white", your terminal may
still render readable text. Some terminals are just "smart" that way.
The same goes for "black on black". The terminal might try to be clever
rather than doing what it's told. The particulars vary from terminal to
terminal. Run this module directly to find out how YOUR terminal
behaves:

    python ansi.py

You'll need a terminal window that's at least 88 columns wide and 34
lines tall to see the output all at once.

To test a specific color combination, you can pass it directly on the
command line:

    python ansi.py blue on yellow
or
    python ansi.py bold red on blue

"""

import colorsys,math,sys

# Traditional 8-color ANSI color escape sequence values:
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

rgb=dict(
  black=  (0x00,0x00,0x00),
  red=    (0xbf,0x00,0x00),
  green=  (0x00,0xbf,0x00),
  yellow= (0xbf,0xbf,0x00),
  blue=   (0x00,0x00,0xbf),
  magenta=(0xbf,0x00,0xbf),
  cyan=   (0x00,0xbf,0xbf),
  white=  (0xbf,0xbf,0xbf)
)

rgb_bold=dict(
  black=  (0x00,0x00,0x00),
  red=    (0xff,0x00,0x00),
  green=  (0x00,0xff,0x00),
  yellow= (0xff,0xff,0x00),
  blue=   (0x00,0x00,0xff),
  magenta=(0xff,0x00,0xff),
  cyan=   (0x00,0xff,0xff),
  white=  (0xff,0xff,0xff)
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

current_background='black';

# Assign luminosity values to our colors.
luminosity=dict(
  black=0.1,
  blue=0.2,
  red=0.3,
  magenta=0.4,
  green=0.6,
  cyan=0.7,
  yellow=0.8,
  white=0.9
)

# Dark and light palette specifications.
dark='norm red on black,green,yellow,bold blue,norm magenta,cyan,white'
light='norm red on white,green,blue,magenta,black'

# This is the master switch for this module. ANSI Colors have no effect unless
# enabled is True.
enabled=True

class AnsiException(Exception):
  "Exceptions raised from this module are of this type."

  pass

def englishList(l,conj='and'):
  "Return a string listing all elements of l as an english list phrase."

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

class Color(object):
  '''Objects of this class contain the attribute, foreground, and
  background of the color such an object represents.'''

  attribute_list=attr.keys()
  foreground_list=foreground.keys()
  background_list=background.keys()

  def  __init__(self,*args):
    """Construct a Color object.

    Form 1: Color(col)
    Create a new Color object as a copy of the given Color object.

    Form 2: Color(attr_str,fg_str,bg_str)
    Create this Color object with the given attribute, foreground, and
    background. (See the parse() method below.)

    Form 3: Color('[ATTR ] FG [on BG]')
    Create this Color object with the given attribute, foreground, and
    background, but parse them all from the given string argument.

    Ex: Three ways to create a "bold green on blue" Color object ...

        c1=ansi.Color('bold','green','blue')
        c2=ansi.Color('bold green on blue')
        c3=ansi.Color(c2)
        print 'c1=%r'%c1
        print 'c2=%r'%c2
        print 'c3=%r'%c3
        ansi.paint(c3,'See? I told you.')
    """
    
    self.attribute=self.foreground=self.background=None
    if len(args)==1:
      if isinstance(args[0],Color):
        self.attribute=args[0].attribute
        self.foreground=args[0].foreground
        self.background=args[0].background
      else:
        self.parse(args[0])
    elif len(args)==3:
      self.attribute,self.foreground,self.background=args
      if isinstance(self.attribute,basestring):
        self.attribute=complete(self.attribute.lower(),self.attribute_list)
      if isinstance(self.foreground,basestring):
        self.foreground=complete(self.foreground.lower(),self.foreground_list)
      if isinstance(self.background,basestring):
        self.background=complete(self.background.lower(),self.background_list)
    else:
      raise AnsiException('bad initializer for class Color: %r'%(args))

  def __call__(self,text):
    """Return the given text prefixed with the ANSI sequence for this
    Color and suffixed with the ANSI sequence to turn this Coler back
    off.

    >>> Color('normal','white','black')('test')=='\x1b[0;37mtest\x1b[0m'
    True
    >>> Color('normal white on black')('test')=='\x1b[0;37mtest\x1b[0m'
    True
    >>> Color(None,'white','black')('test')=='\x1b[37mtest\x1b[0m'
    True
    >>> Color('white on black')('test')=='\x1b[37mtest\x1b[0m'
    True
    >>> Color('black on white')('test')=='\x1b[30;47mtest\x1b[0m'
    True
    >>> Color('black on yellow')('test')=='\x1b[30;43mtest\x1b[0m'
    True
    >>> Color('black on green')('test')=='\x1b[30;42mtest\x1b[0m'
    True
    >>> Color('bold',None,'black')('test')=='\x1b[1mtest\x1b[0m'
    True
    >>> Color('bold','white',None)('test')=='\x1b[1;37mtest\x1b[0m'
    True
    >>> Color('bold white')('test')=='\x1b[1;37mtest\x1b[0m'
    True
    >>> Color('bold',None,None)('test')=='\x1b[1mtest\x1b[0m'
    True
    >>> Color(None,'white',None)('test')=='\x1b[37mtest\x1b[0m'
    True
    >>> Color(None,None,'black')('test')=='\x1b[mtest\x1b[0m'
    True
    """

    if enabled:
      return str(self)+str(text)+str(norm)
    return str(text)

  def __repr__(self):
    """Return a Python expression string that can be evaluated to re-
    create this object."""

    return 'Color(%r,%r,%r)'%(self.attribute,self.foreground,self.background)
      
  def __str__(self):
    """Return the ANSI escape sequence for this object's attribute,
    foreground, and background"""

    global current_background

    s='\x1b['
    if current_background in background and self.background==current_background:
      s+=';'.join([
        d[k] for d,k in (
          (attr,self.attribute),
          (foreground,self.foreground)
        ) if d.get(k)
      ])
    else:
      s+=';'.join([
        d[k] for d,k in (
          (attr,self.attribute),
          (foreground,self.foreground),
          (background,self.background)
        ) if d.get(k)
      ])
    s+='m'
    return s
    #return color(self.attribute,self.foreground,self.background)

  def parse(self,spec):
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
    l=spec.lower().strip().split('on')
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
      a=complete(a,Color.attribute_list)
    f=complete(f,Color.foreground_list)
    if b!=None:
      b=complete(b,Color.background_list)

    # Return our triplet of tokens.
    self.attribute,self.foreground,self.background=(a,f,b)
    return self

  def rgb(self):
    """Return two (r,g,b) triplets for the foreground and background of
    this color as (foreground rgb triplet,background rgb triplet). The
    r, g, and b values are integers from 0 to 255."""

    global current_background

    if self.attribute=='bold':
      fg=rgb_bold.get(self.foreground,rgb['white'])
    else:
      fg=rgb.get(self.foreground,rgb['white'])
    bg=rgb.get(self.background,rgb.get(current_background,rgb['black']))
    return (fg,bg)

  def rgbFloat(self):
    """Same as rgb(), but returns values in the range from 0.0 to 1.0."""

    return tuple([tuple([x/255.0 for x in y]) for y in self.rgb()])

  def brightness(self):
    """Return a tuple containing brightness values of the foreground and
    background colors. Values are in the range from 0.0 to 1.0."""

    # Compute brightness from RGB according to https://www.w3.org/TR/AERT,
    # but express the result as a floating point number from 0.0 to 1.0.
    fg,bg=self.rgb()
    fg=reduce(lambda a,b:a+b,[c*val for c,val in zip((299,587,114),fg)])/255000.0
    bg=reduce(lambda a,b:a+b,[c*val for c,val in zip((299,587,114),bg)])/255000.0
    return (fg,bg)

  def contrast(self):
    """Return a float from 0.0 to 1.0 indicating how different the
    foreground and background colors are."""

    # We already have a way to compute brightness.
    fg_brightness,bg_brightness=self.brightness()

    # Get the HSV version of our foreground and background colors.
    fg,bg=self.rgbFloat()
    fgH,fgS,fgV=colorsys.rgb_to_hsv(*fg)
    bgH,bgS,bgV=colorsys.rgb_to_hsv(*bg)

    # Now that we're in a cylendrical color system, return the "distance"
    # between the two colors. The constant divisor is the maximum actual
    # distance possible, which keeps the return value in the range from 0.0 to
    # 1.0, and I'm rounding to keep the values easy on the eyes. And I'm
    # ignoring saturation because considering it messes up the result.
    return round(cylindricalDistance((0,fgH,fgV),(0,bgH,bgV)),6)
    
  def str(self):
    '''Return the ANSI escape sequence for this object's attribute,
    foreground, and background. (color.str() is exactly the same as
    str(color).)'''

    return str(self)

class Palette(list):
  '''An instance of Palette is a list of Color objects and can be
  treated as such.'''

  dark_spec='norm red on black,green,yellow,bold blue,norm magenta,cyan'
  light_spec='norm red on white,green,blue,magenta,cyan'

  def __init__(self,spec):
    """Construct a Palette object.

    Form 1: Palette(pal)
    Create a new Palette object as a copy o fthe given Palette object.

    Form 2: Palette('dark') or Palette('light')
    Create a new Palette object for use with terminal with dark or light
    color schemes.

    Form 3: Palette(palette_spec_string)
    Create a new Palette object from a string of color specifications
    separated by commas, using attribute an background from previous
    entries as defaults for the current entry.

    Ex: Set up a patriotic (in the US) palette ...

        red,white,blue=ansi.Palette('bold red on black, white, blue')
        ansi.paint(red,'God ',white,'Bless ',blue,'America!')

    Notice that the "bold" attribute and "black" background needn't be
    repeated after they're set up in the first color of the palette."""

    if isinstance(spec,Palette):
      super(Palette,self).__init__(spec)
    else:
      super(Palette,self).__init__()
      if spec=='dark':
        spec=Palette.dark_spec
      elif spec=='light':
        spec=Palette.light_spec
      prev_attr=prev_fg=prev_bg=None
      for color_spec in spec.split(','):
        c=Color(color_spec) #a,f,b=parseColor(color_spec)
        if not c.attribute: c.attribute=prev_attr
        if not c.foreground: c.foreground=prev_fg
        if not c.background: c.background=prev_bg
        self.append(c)
        prev_attr,prev_fg,prev_bg=c.attribute,c.foreground,c.background

  def __call__(self,index):
    '''Return the Color object at the given index. The index value wraps
    around the list, so the caller needn't worry about index overflow.
    Otherwise, this is exactly like using square brackets on the palette
    object directly.
    
    Ex:
        pal=ansi.Palette('norm red on black,green,bold blue')
        words='this is a list of words'.split()
        ansi.paint(*ansi.flattenList(
          [[pal(i),words[i],' '] for i in range(len(words))]
        ))

    But this would will create an "index out of range" error:

        ansi.paint(*ansi.flattenList(
          [[pal[i],words[i],' '] for i in range(len(words))]
        ))

    The only (very subtle) difference is how we index the pal variable.
    The first example uses pal(i), while the second uses pal[i].
    
    '''

    return self[index%len(self)]

norm=Color('normal',None,None) #'\033['+attr['normal']+'m'

def flattenList(l,result=None):
  '''Recursively flatten the given list [of lists [of lists]]. This
  comes in handy when buiding arguments for ansi.paint() from list
  comprehensions. (See example under Palette.__call__().)
  
  The l argument is the list [of lists [of lists]] to be flattened. The
  second argument, if supplied, is the flattened list that's being built
  and can be thought of as an initializer for the result list that is
  ultimately returned.'''

  if result==None:
    result=[]
  for elem in l:
    if type(elem)==list:
      flattenList(elem,result)
    else:
      result.append(elem)
  return result

def cylindrical_to_cartesian(rho,theta,z):
  """Given point p in a cylindrical coordinate system, return the
  cartesian equivalent. OUR cylindrical coordinate system is defined by
  Rho, Theta, and Z dimensions. Rho is radial distance from the Z axis
  (any non-negative value), Theta is the angular component about the
  Z axis (from 0.0 to 1.0), and Z is any floating point value along the
  Z axis."""

  # Condition our coordinates into their canonical ranges to keep the
  # caller from violating the assumptions further down in this fun
  # subsequent assumptions cannot be violated.
  if rho<0.0:
    theta+=0.5
    rho=-rho
  # rho is now non-negative, and theta has been reversed if needed.
  theta=math.modf(theta)[0] # Puts theta in (-1 .. 1).
  if theta<0:
    theta=1-theta # Makes theta non-negative.
  # theta is now in [0 .. 1).

  theta*=2*math.pi # Converts theta to radians.
  x=round(rho*math.cos(theta),8)
  y=round(rho*math.sin(theta),8)
  # We're rounding x and y to 8 decimal places to let 0 be 0.
  return x,y,z

def cylindricalDistance(p1,p2):
  """Return the linear distance between two points defined in a
  cylindrical coordinate system. c1 and c2 MUST be tuples expresing
  cylindrical coordinates. See the documentation for the
  cylendrical_to_cartesian() function for details of expressing
  cylindrical coordinates."""

  # Convert our cylendrical space to cartesian space.
  c1=cylindrical_to_cartesian(*p1)
  c2=cylindrical_to_cartesian(*p2)

  # The Pythoreans were very cool.
  return math.sqrt(sum([(a-b)**2 for a,b in zip(c1,c2)]))

def paint(*args):
  '''Kind of like print, but supports coloring its output.

  An argument of class Color is used to paint all subsequent arguments
  until another such argument is found. All other arguments are rendered
  the same as print would render them.

  Painting is always turned off before this function returns, and this
  is always done before a final newline character is output.'''

  global current_background

  for arg in args:
    sys.stdout.write(str(arg))
    if isinstance(arg,Color):
      current_background=arg.background
      
  sys.stdout.write(str(norm)+'\n')
  current_background=norm.background


if __name__=='__main__': # TEST CODE TEST CODE TEST CODE TEST CODE TEST CODE
  import doctest,sys
  failed,total=doctest.testmod()

  if failed==0:
    if len(sys.argv)>1:
      # Interpret the command line as a color specification string, and output
      # that string using the attribute and colors it gives.
      spec=' '.join(sys.argv[1:])
      c=Color(spec)
      print c(spec)
    else:
      # Show a table of all color and attribute combinations.
      colors='Black Red Green Yellow Blue Magenta Cyan White'.split()
      # Print the column headings.
      print '        '+(' '.join([Color('under','black',c)('%-9s'%c) for c in colors]))
      # Foreground colors and attributes change from one line to the next.
      for fg in colors:
        # The first line of a given foreground color is labeled. Note that the
        # color name in the row label is given as flattenLists()'s result
        # initializer.
        paint(*flattenList(
          [[Color('norm',fg,bg),'Normal   ',norm,' '] for bg in colors],
          [Color('bold %s'%fg),'%7s '%fg]
        ))
        # The second line shows contrast values for the above foreground and
        # background combinations.
        paint(*flattenList(
          ['%-10.5f'%Color('norm',fg,bg).contrast() for bg in colors],
          [' '*8]
        ))
        paint(*flattenList(
          [[Color('Bold',fg,bg),'Bold     ',norm,' '] for bg in colors],
          [' '*8]
        ))
        # The fourth line shows contrast values for the above foreground and
        # background combinations.
        paint(*flattenList(
          ['%-10.5f'%Color('bold',fg,bg).contrast() for bg in colors],
          [' '*8]
        ))
        # Show the contrast figures for normal text.
        # Remaining lines of a given foreground just begin with spaces.
        for a in ('Italics','Underline'):
          paint(*flattenList(
            [[Color(a,fg,bg),'%-9s'%a,norm,' '] for bg in colors],
            [' '*8]
          ))
