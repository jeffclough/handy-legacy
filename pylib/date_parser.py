#!/usr/bin/env python2

"""
The DateParser class is for parsing relative times. For example:

    sunday
    thursday
    yesterday
    tomorrow
    day before yesterday
    day before tomorrow
    day after yesterday
    2 days before yesterday
    now
    today
    day after tomorrow
    1 day ago
    3 days ago
    1 week ago
    -1 week from now
    2 weeks ago
    1 week from fri
    2 weeks before monday
    1 fortnight hence
    1 month ago
    1 year hence



"""

import re,time
import datetime as dt
import pyparsing as pyp

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

begin=end=None

class DateParser(object):
  def __init__(self,syntax):
    """The subclass must implement __init__(), which must set
    self.syntax to some pyparsing.ParserElement derivative."""

    raise NotImplemented("DateParser must not be instantiated on its own.")

  def __call__(self,s):
    """Parse the given string according to this DateParser's syntax, and
    return this object. The "now" and "date" attributes will be set. If
    the syntax matches the string, this object's "date" attribute will
    contain the correspond value. Otherwise, it will have a value of
    None datetime.date value. Otherwise, return None."""

    try:
      self.tokens=self.syntax.parseString(s)
      self.begin=begin
      self.end=end
    except pyp.ParseException:
      self.begin=None
      self.end=None
      return None
    self.now=dt.date.today()
    self.date=self.convert(self.tokens)
    return self

  def convert(self,tokens):
    """This method MUST be implemented in a subclass. tokens is a list
    of words that have matched our the syntax defined for the subclass.
    A self.now attribute will be initialized to datetime.date.today()
    immediately before this method is called."""

    raise NotImplemented("DateParser.convert() must be implemented in a subclass.")

  def relativeDay(self,daystr):
    """Given a day name, return the corresponding datetime.date object.
    The given string can be a day of the week, yesterday, today, now, or
    tomorrow.
    
    This method is intended to be called from the convert() method of a
    subclass of DateParser. It requires that self.now already be
    initialized to an appropriate value."""

    t=self.now.timetuple()
    d=downum.get(daystr)
    if d!=None:
      delta=d-t.tm_wday
      if delta<=0:
        delta+=7
      delta=dt.timedelta(delta)
    elif daystr=='yesterday':
      delta=dt.timedelta(-1)
    elif daystr=='tomorrow':
      delta=dt.timedelta(1)
    elif daystr in ('today','now'):
      delta=dt.timedelta(0)
    return self.now+delta

  def relativeMonth(self,count):
    """Given the number of months (positive or negative) to offset from
    self.now, return the datetime.date value of the result.

    This method is intended to be called from the convert() method of a
    subclass of DateParser. It requires that self.now already be
    initialized to an appropriate value."""

    # BTW, all hail the power of Python's modulo operator!
    y,m,d=self.now.timetuple()[:3]
    m1=(m+count-1)%12+1
    y1=y+(m+count-1)/12
    try:
      new_date=dt.date(y1,m1,d)
    except ValueError:
      if m1==2 and d==29:
        m1,d=3,1
      else:
        raise
    new_date=dt.date(y1,m1,d)
    return new_date

  def relativeYear(self,count):
    """ Given the number of years (positive or negative) to offset from
    self.now, return the datetime.date value of the result.

    This method is intended to be called from the convert() method of a
    subclass of DateParser. It requires that self.now already be
    initialized to an appropriate value."""

    # Year arithmetic requires working with the calendar (a little).
    y,m,d=self.now.timetuple()[:3]
    y1=y+count
    try:
      new_date=dt.date(y1,m,d)
    except ValueError:
      if m==2 and d==29:
        m,d=3,1
      else:
        raise
    new_date=dt.date(y1,m,d)
    return new_date

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def remember_range(s,loc,toks):
  global begin,end

  begin=loc
  end=pyp.getTokensEndLoc()

SUNDAY=pyp.oneOf('sunday sunda sund sun su',True).setParseAction(pyp.replaceWith('sunday'))
MONDAY=pyp.oneOf('monday monda mond mon mo m',True).setParseAction(pyp.replaceWith('monday'))
TUESDAY=pyp.oneOf('tuesday tuesda tuesd tues tue tu',True).setParseAction(pyp.replaceWith('tuesday'))
WEDNESDAY=pyp.oneOf('wednesday wednesda wednesd wednes wedne wedn wed we w',True).setParseAction(pyp.replaceWith('wednesday'))
THURSDAY=pyp.oneOf('thursday thursda thursd thurs thur thu th',True).setParseAction(pyp.replaceWith('thursday'))
FRIDAY=pyp.oneOf('friday frida frid fri fr f',True).setParseAction(pyp.replaceWith('friday'))
SATURDAY=pyp.oneOf('saturday saturda saturd satur satu sat sa').setParseAction(pyp.replaceWith('saturday'))
day_of_week=SUNDAY|MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY

YESTERDAY=pyp.CaselessKeyword('yesterday')
TODAY=pyp.oneOf('today now',True).setParseAction(pyp.replaceWith('today'))
TOMORROW=pyp.CaselessKeyword('tomorrow')
relative_day=YESTERDAY|TODAY|TOMORROW

day=relative_day|day_of_week
day.setParseAction(remember_range)

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
    return self.relativeDay(dayname)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sign=pyp.Literal('-')|pyp.Literal('+')
integer=pyp.Word(pyp.nums)
signed_integer=pyp.Combine(pyp.Optional(sign)+integer)
count=pyp.Optional(signed_integer,default=1)
count.setParseAction(lambda s,l, t: int(t[0]))

DAY=pyp.oneOf('days day',True).setParseAction(pyp.replaceWith('day'))
WEEK=pyp.oneOf('weeks week',True).setParseAction(pyp.replaceWith('week'))
FORTNIGHT=pyp.oneOf('fortnights fortnight',True).setParseAction(pyp.replaceWith('fortnight'))
MONTH=pyp.oneOf('months month',True).setParseAction(pyp.replaceWith('month'))
YEAR=pyp.oneOf('years year',True).setParseAction(pyp.replaceWith('year'))
unit=DAY|WEEK|FORTNIGHT|MONTH|YEAR

IN=pyp.CaselessLiteral('in')
THE=pyp.CaselessLiteral('the')
PAST=pyp.CaselessLiteral('past')
FUTURE=pyp.CaselessLiteral('future')

AGO=(pyp.CaselessLiteral('ago')|(IN+THE+PAST)).setParseAction(pyp.replaceWith('ago'))
HENCE=(pyp.CaselessLiteral('hence')|(IN+THE+FUTURE)).setParseAction(pyp.replaceWith('hence'))

counted_relative_day=count+unit+(AGO|HENCE)
counted_relative_day.setParseAction(remember_range)

class DateParser_2(DateParser):
  """

  relday := [signed_integer] unit direction
  unit := {DAY[S]|WEEK[S]|FORTNIGHT[S]|MONTH[S]|YEAR[S]}
  direction := {AGO|HENCE}

  """

  def __init__(self):
    self.syntax=counted_relative_day

  def convert(self,tokens):
    "Convert out tokens to a datetime.date object."""

    # DEBUGGING
    #self.now=dt.date(2016,2,29)

    count,unit,direction=tokens
    #print 'DEBUG: count=%r, unit=%r, direction=%r'%(count,unit,direction)
    if direction=='ago':
      count=-count
    if unit in ('day','week','fortnight'):
      if unit=='day':
        delta=dt.timedelta(days=count)
      elif unit=='week':
        delta=dt.timedelta(days=count*7)
      else: # unit=='fortnight':
        delta=dt.timedelta(days=count*14)
      return self.now+delta
    elif unit=='month':
      new_date=self.relativeMonth(count)
    elif unit=='year':
      new_date=self.relativeYear(count)
    return new_date


BEFORE=pyp.CaselessLiteral('before').setName('BEFORE').setParseAction(pyp.replaceWith('before'))
AFTER=pyp.oneOf('after from').setName('AFTER').setParseAction(pyp.replaceWith('after'))
refday=(BEFORE|AFTER)+day

counted_relative_from_refday=count+unit+refday
counted_relative_from_refday.setParseAction(remember_range)

class DateParser_3(DateParser):
  """

  relday := [signed_integer] unit direction ref_day
  unit := DAY[S]|WEEK[S]|FORTNIGHT[S]|MONTH[S]|YEAR[S]
  refday := {BEFORE|AFTER|FROM} day
  day := day_of_week|relative_day

  """

  def __init__(self):
    self.syntax=counted_relative_from_refday

  def convert(self,tokens):
    count,unit,direction,refday=tokens
    if direction=='before':
      count=-count
    refday=self.relativeDay(refday)
    if unit in ('day','week','fortnight'):
      if unit=='day':
        delta=dt.timedelta(days=count)
      elif unit=='week':
        delta=dt.timedelta(days=count*7)
      else: # unit=='fortnight':
        delta=dt.timedelta(days=count*14)
      return refday+delta
    elif unit=='month':
      delta=dt.timedelta(days=count*30)
    elif unit=='year':
      delta=dt.timedelta(days=count*365)
    return refday+delta

def add_parser(*args):
  """Accept one or more instances of a DateParser-dreived class, and
  append them to the list of date parsers."""

  for p in args:
    if isinstance(p,DateParser):
      _parsers.append(p)
    else:
      raise TypeError('Cannot add object of type %s as a date parser.'%(p.__class__.__name__,))

def parse(s):
  for parser in _parsers:
    d=parser(s)
    if d:
      return d
  return None

# Add our standard date parsers.
_parsers=[]
add_parser(
  DateParser_1(),
  DateParser_2(),
  DateParser_3()
)

if __name__=="__main__":
  import argparse,doctest,pprint

  ap=argparse.ArgumentParser(description="Test this Python module.")
  ap.add_argument('args',metavar='args',nargs='*',help="Each argument is a date string to be interpreted.")
  opt=ap.parse_args()

  if not opt.args:
    opt.args=[
      'sunday',
      'monday',
      'tuesday',
      'wednesday',
      'thursday',
      'friday',
      'saturday',
      '2 days before yesterday',
      'day before yesterday',
      'yesterday',
      'day after yesterday',
      'now',
      'today',
      'day before tomorrow',
      'tomorrow',
      'day ago',
      'day before today',
      'day after today',
      'day from now',
      'day from today',
      'day after tomorrow',
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
      '+2 weeks in the past',
      '1 week from monday',
      '1 week from tue',
      '1 week from w',
      '1 week from th',
      '1 week from fri',
      '1 week from sat',
      '1 week from sun',
      '2 weeks before monday',
      '1 fortnight hence',
      '1 month ago',
      '1 year hence',
    ]

  failed,total=doctest.testmod()
  if failed==0:
    for sample in opt.args:
      p=parse(sample)
      print '%s parsed from %r (%d - %d)'%(p.date,sample,p.begin,p.end)
