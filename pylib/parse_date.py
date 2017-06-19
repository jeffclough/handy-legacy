#!/usr/bin/env python

import re,time
import datetime as dt

import sys # for debugging

class IndexedNames(object):
  """Handle the tedium of matching things like day and month names to
  their proper index values, even when given only an abbreviated name to
  get the index value of. Use dictionary syntax to get and set index
  values on an instance of this class.

  >>> foo=IndexedNames('Abcd Abef Ghij Klmn Opqr Opqs Opqt'.split(),4,2)
  >>> print repr(foo)
  IndexedNames(('Abcd', 'Abef', 'Ghij', 'Klmn', 'Opqr', 'Opqs', 'Opqt'), start=4, step=2)
  >>> print foo['abc']
  4
  >>> print foo['abe']
  6
  >>> foo['totally bogus']
  Traceback (most recent call last):
  KeyError: 'totally bogus'
  >>> foo['a']
  Traceback (most recent call last):
  KeyError: 'a'
  >>> print 'ghij' in foo
  True
  >>> print 'ghi' in foo
  True
  >>> print 'gh' in foo
  True
  >>> print 'g' in foo
  True
  >>> print foo[0]
  Traceback (most recent call last):
  KeyError: '0'
  >>> print foo[4]
  Abcd
  >>> print foo[8]
  Ghij
  >>> foo[99]
  Traceback (most recent call last):
  KeyError: '99'
  >>> foo.items()
  [('Abcd', 4), ('Abef', 6), ('Ghij', 8), ('Klmn', 10), ('Opqr', 12), ('Opqs', 14), ('Opqt', 16)]
  >>> foo.keys()
  ['Abcd', 'Abef', 'Ghij', 'Klmn', 'Opqr', 'Opqs', 'Opqt']
  >>> foo.values()
  [4, 6, 8, 10, 12, 14, 16]
  >>> bar=IndexedNames('abc ABC def ghi'.split())
  Traceback (most recent call last):
  KeyError: "Duplicate items in list: 'abc'"
  >>> bar=IndexedNames('abc ABCD def ghi'.split())
  Traceback (most recent call last):
  KeyError: "'abc' is an abbreviation of 'abcd'"
  >>> dow=IndexedNames('Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split())
  >>> print dow.get('M')
  0
  >>> print dow.get('Tu')
  1
  >>> print dow.get('W')
  2
  >>> print dow.get('Th')
  3
  >>> print dow.get('F')
  4
  >>> print dow.get('Sa')
  5
  >>> print dow.get('Su')
  6
  >>> print dow.get('T')
  None
  >>> print dow.get('x')
  None
  >>> print dow.get('monday')
  0
  >>> print dow.get('mondayx')
  None
  
  """
  
  def __init__(self,name_list,start=0,step=1):
    """Store an index value, starting at 0 by default, for each name in
    the list. Also precompute all distinct abbreviations for those
    names, remembering each one by the index of the full name.

    Every name in the list must be case-insensitively distinct from
    every other name, an no full name may match the beginning of another
    name. Otherwise, a KeyError will be raised."""

    # Remember our list of name and in what order they were given.
    self.name_list=tuple(name_list)
    self.start=int(start)
    try:
      self.step=int(step)
      if self.step==0:
        raise
    except:
      raise ValueError('Illegal step value: %r'%(step,))
    self.num_dict=dict([
      (self.name_list[i].lower(),(i,self.start+self.step*i)) for i in range(len(self.name_list))
    ])
    # num_dict[key]=(i,start+step*i)

    # Verify that no two names match and that no name is abbreviation for any
    # other name.
    klist=self.num_dict.keys()
    for i in range(len(self.name_list)):
      for j in range(len(self.name_list)):
        if i!=j:
          if self.name_list[i].lower()==self.name_list[j].lower():
            raise KeyError('Duplicate items in list: %r'%(self.name_list[i].lower()))
    for i in range(len(klist)):
      for j in range(len(klist)):
        if i!=j:
          if klist[i].startswith(klist[j]):
            raise KeyError('%r is an abbreviation of %r'%(klist[j],klist[i]))

    # Add decreasingly minimal forms of all keys to dictionary.
    for name in klist:
      for i in range(1,len(name)):
        partial=name[:i]
        possibles=[s for s in klist if s.startswith(partial)]
        if len(possibles)==1:
          val=self.num_dict[name]
          self.num_dict.update(dict([
            (name[:j],val) for j in range(i,len(name))
          ]))
          break

  def __repr__(self):
    """Return a string that could be passed to eval() to recreate this
      object."""

    return '%s(%r, start=%r, step=%r)'%(self.__class__.__name__,self.name_list,self.start,self.step)

  def __contains__(self,key):
    """Return true if key is either the name or index of an item stored
    in this object."""

    if isinstance(key,basestring):
      return key.lower() in self.num_dict
    try:
      key=int(key)
    except:
      raise KeyError(repr(key))
    return key in [v[1] for v in self.num_dict.values()]

  def __getitem__(self,key):
    """If key is a string value, return the index of that string.
    Otherwise, assume key is an index and return the corresponding
    name."""

    if isinstance(key,basestring):
      return self.num_dict[key.lower()][1]
    try:
      key=int(key)
    except:
      raise KeyError(repr(key))
    for n in self.name_list:
      if self.num_dict[n.lower()][1]==key:
        return n
    raise KeyError(repr(key))

  def get(self,key,default=None):
    """If key is a string value, return the index of that string.
    Otherwise, assume key is an index and return the corresponding
    name. In either case, return the default value if the key is
    not found."""

    try:
      val=self[key]
    except KeyError:
      val=default
    return val

  def items(self):
    """Return a list of (name, index) tuples that defines this object's
    value, ensuring that the names are returned in the same order as
    they were originally presented to this object. The list returned is
    suitable for constructing a dict."""

    #print >>sys.stderr,'DEBUG: num_dict=%r'%(self.num_dict,)

    return [(n,self.num_dict[n.lower()][1]) for n in self.name_list]

  def keys(self):
    """Return a list of the names stored in this object in the same
    order in which they were originally presented to it."""

    return list(self.name_list)

  def values(self):
    """Return a list of index values for the names stored in this
    object, ensuring that the index values are in the same order as the
    names."""

    return [self.num_dict[n.lower()][1] for n in self.name_list]



# Prepare day-of-week and month-of-year indices, from 0-6 and from 1-12, respectively.
dow=IndexedNames('Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split())
moy=IndexedNames('January February March April May June July August September October November December'.split(),1)

# [int ](day|week|fortnight|month|year)[s] (ago|hence|(before|from) DAY)
# DAY := yesterday|now|today|tomorrow|DOW
# DOW := any day of the week
re_relative_date_1=re.compile(
  r'^'
  r'((?P<n>[-+]?\d+)\s+)?'
  r'((?P<units>(day|week)s?)\s+)'
  r'(?P<dir>(ago|(before|from|after)\s+\w+|in\s+the\s+(past|future)))'
  r'$'
)

def parse_date(datestr):
  """Return a datetime.date object containing the date expressed
  in datestr."""

  datestr=datestr.strip().lower()
  lt=time.localtime()
  today=dt.date(*lt[:3])
  this_day=lt[6]

  if datestr in ('now','today'):
    return today
  if datestr=='yesterday':
    return today+dt.timedelta(-1)
  if datestr=='tomorrow':
    return today+dt.timedelta(1)

  m=re_relative_date_1.search(datestr)
  if m:
    g=type('',(),m.groupdict())

    if g.n:
      g.n=int(g.n)
    else:
      g.n=1

    if g.units.startswith('week'):
      g.n*=7

    offset=0
    g.dir=g.dir.split()
    if g.dir[0]=='ago':
      g.dir=-1
    elif g.dir[0] in ('before','from','after'):
      dayname=g.dir[-1]
      day=dow.get(dayname)
      if day!=None:
        offset=day-this_day
        if offset<1:
          offset+=7
      else:
        if dayname=='yesterday':
          offset=-1
        elif dayname in ('now','today'):
          offset=0
        elif dayname=='tomorrow':
          offset=1
        else:
          return None
      if g.dir[0].startswith('before'):
        g.dir=-1
      else:
        g.dir=1
    elif g.dir[0]=='in' and g.dir[1]=='the':
      if g.dir[-1]=='past':
        g.dir=-1
      else:
        g.dir=1
    else:
      g.dir=1
    #print 'today=%r, g.n=%r, g.dir=%r, offset=%r'%(today,g.n,g.dir,offset)
    return today+dt.timedelta(g.n*g.dir+offset)
  return None

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# The new way begins here.

downum=dict(
  monday=0,
  tuesday=1,
  wednesday=2,
  thursday=3,
  friday=4,
  saturday=5,
  sunday=6
)

moynum=dict(
  january=1,
  february=2,
  march=3,
  april=4,
  may=5,
  june=6,
  july=7,
  august=8,
  september=9,
  october=10,
  november=11,
  december=12
)

import time,pyparsing as pyp

class DateParser(object):
  def __init__(self,syntax):
    """The subclass must implement __init__(), which must set
    self.syntax to some pyparsing.ParserElement derivative."""

    raise NoteImplemented("DateParser must not be instantiated on its own.")

  def __call__(self,s):
    """Parse the given string according to this DateParser's syntax. If
    the syntax matches the string, return the corresponding
    datetime.date value. Otherwise, return None."""

    try:
      tokens=self.syntax.parseString(s)
      #print 'DEBUG: tokens=%r'%(tokens,)
    except pyp.ParseException:
      return None
    self.now=dt.date.today()
    return self.convert(tokens)

  def convert(self,tokens):
    raise NotImplemented("DateParser.convert() must be implemented in a subclass.")

SUNDAY=pyp.oneOf('sunday sunda sund sun su',True).setParseAction(pyp.replaceWith('sunday'))
MONDAY=pyp.oneOf('monday monda mond mon mo m',True).setParseAction(pyp.replaceWith('monday'))
TUESDAY=pyp.oneOf('tuesday tuesda tuesd tues tue tu',True).setParseAction(pyp.replaceWith('tuesday'))
WEDNESDAY=pyp.oneOf('wednesday wednesda wednesd wednes wedne wedn wed we w',True).setParseAction(pyp.replaceWith('wednesday'))
THURSDAY=pyp.oneOf('thursday thursda thursd thurs thur thu th',True).setParseAction(pyp.replaceWith('thursday'))
FRIDAY=pyp.oneOf('friday frida frid fri fr f',True).setParseAction(pyp.replaceWith('friday'))
SATURDAY=pyp.oneOf('saturday saturda saturd satur satu sat sa').setParseAction(pyp.replaceWith('saturday'))
specific_day=SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY

YESTERDAY=pyp.CaselessKeyword('yesterday')
TODAY=pyp.oneOf('today now',True).setParseAction(pyp.replaceWith('today'))
TOMORROW=pyp.CaselessKeyword('tomorrow')
relative_day=YESTERDAY|TODAY|TOMORROW

day=relative_day|specific_day

def relativeDay(s,reference=dt.date.today()):
  """Given a day name, return the corresponding datetime.date objects.
  The given string can be a day of the week, yesterday, today, now, or
  tomorrow."""

  t=reference.timetuple()
  d=downum.get(s)
  if d!=None:
    if d<=t.tm_wday:
      d+=7
    delta=dt.timedelta(d-t.tm_wday)
  elif s=='yesterday':
    delta=dt.timedelta(-1)
  elif s=='tomorrow':
    delta=dt.timedelta(1)
  elif s in ('today','now'):
    delta=dt.timedelta(0)
  return reference+delta

class DateParser_1(DateParser):
  """

  rel_day := YESTERDAY | TODAY | NOW | TOMORROW
  spec_day := SUNDAY | MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY | SATURDAY
  day := rel_day | spec_day

  """

  def __init__(self):
    self.syntax=day

  def convert(self,tokens):
    dayname=tokens[0]
    return relativeDay(dayname)

# def convert(self,tokens):
#   """Convert the list of tokens matching the "day" syntax to a
#   datetime.date value."""
#
#   t=self.now.timetuple()
#   dayname=tokens[0]
#   #print 'DEBUG: dayname=%r'%dayname
#   d=downum.get(dayname)
#   if d!=None:
#     if d<=t.tm_wday:
#       d+=7
#     delta=dt.timedelta(d-t.tm_wday)
#   elif dayname=='yesterday':
#     delta=dt.timedelta(-1)
#   elif dayname=='tomorrow':
#     delta=dt.timedelta(1)
#   else:
#     delta=dt.timedelta(0)
#   #print 'DEBUG: ds=%r'%ds
#   return self.now+delta

integer=pyp.Word(pyp.nums)
count=pyp.Optional(integer,default=1)
count.setParseAction(lambda s,l, t: int(t[0]))

DAY=pyp.oneOf('days day',True).setParseAction(pyp.replaceWith('day'))
WEEK=pyp.oneOf('weeks week',True).setParseAction(pyp.replaceWith('week'))
FORTNIGHT=pyp.oneOf('fortnights fortnight',True).setParseAction(pyp.replaceWith('fortnight'))
MONTH=pyp.oneOf('months month',True).setParseAction(pyp.replaceWith('month'))
YEAR=pyp.oneOf('years year',True).setParseAction(pyp.replaceWith('year'))
unit=DAY|WEEK|FORTNIGHT|MONTH|YEAR

AGO=pyp.CaselessLiteral('ago').setName('AGO').setParseAction(pyp.replaceWith('ago'))
HENCE=pyp.CaselessLiteral('hence').setName('HENCE').setParseAction(pyp.replaceWith('hence'))

counted_relative_day=count+unit+(AGO|HENCE)

class DateParser_2(DateParser):
  """

  relday := [integer] unit direction
  unit := {DAY[S]|WEEK[S]|FORTNIGHT[S]|MONTH[S]|YEAR[S]}
  direction := {AGO|HENCE}

  """

  def __init__(self):
    self.syntax=counted_relative_day

  def convert(self,tokens):
    "Convert out tokens to a datetime.date object."""

    count,unit,direction=tokens
    #print 'DEBUG: count=%r, unit=%r, direction=%r'%(count,unit,direction)
    if direction=='ago':
      count=-count
    if unit=='day':
      delta=dt.timedelta(days=count)
    elif unit=='week':
      delta=dt.timedelta(days=count*7)
    elif unit=='fortnight':
      delta=dt.timedelta(days=count*14)
    elif unit=='month':
      delta=dt.timedelta(days=count*30)
    elif unit=='year':
      delta=dt.timedelta(days=count*365)
    return self.now+delta


BEFORE=pyp.CaselessLiteral('before').setName('BEFORE').setParseAction(pyp.replaceWith('before'))
AFTER=pyp.oneOf('after from').setName('AFTER').setParseAction(pyp.replaceWith('after'))
refday=(BEFORE|AFTER)+day

counted_relative_from_refday=count+unit+refday

class DateParser_3(DateParser):
  """

  relday := [integer] unit direction ref_day
  unit := DAY[S]|WEEK[S]|FORTNIGHT[S]|MONTH[S]|YEAR[S]
  refday := {BEFORE|AFTER|FROM} day
  day := specific_day|relative_day

  """

  def __init__(self):
    self.syntax=counted_relative_from_refday

  def convert(self,tokens):
    count,unit,direction,refday=tokens
    if direction=='before':
      count=-count
    refday=relativeDay(refday)
    if unit=='day':
      delta=dt.timedelta(days=count)
    elif unit=='week':
      delta=dt.timedelta(days=count*7)
    elif unit=='fortnight':
      delta=dt.timedelta(days=count*14)
    elif unit=='month':
      delta=dt.timedelta(days=count*30)
    elif unit=='year':
      delta=dt.timedelta(days=count*365)
    return refday+delta


date_parsers=[
  DateParser_1(),
  DateParser_2(),
  DateParser_3(),
]

def pd(s):
  for parser in date_parsers:
    d=parser(s)
    if d:
      return d
  return None

if __name__=="__main__":
  import doctest
  failed,total=doctest.testmod()
  if failed==0:
    import sys
    if len(sys.argv)>1:
      sample=' '.join(sys.argv[1:])
      print '%s is %s'%(parse_date(sample),sample)
    else:
      for sample in (
        'sunday',
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'yesterday',
        'now',
        'today',
        'tomorrow',
        'day ago',
        'day before today',
        'day after today',
        'day from now',
        'day from today',
        '1 day ago',
        '3 days ago',
        '1 day hence',
        '3 days hence',
        '1 day from now',
        '2 days from now',
        '3 days from today',
        '1 week ago',
        '-1 week from now',
        '2 weeks ago',
        '-2 weeks from today',
        '1 week from now',
        '-1 week ago',
        '2 weeks from today',
        '-2 weeks in the past',
        '1 week from monday',
        '1 week from tue',
        '1 week from w',
        '1 week from th',
        '1 week from fri',
        '1 week from sat',
        '1 week from sun',
        '2 weeks before monday',
        'fortnight hence',
        'month ago',
        'year hence',
      ):
#       print '%s is %s'%(parse_date(sample),sample)
        print '%s is %s'%(pd(sample),sample)
