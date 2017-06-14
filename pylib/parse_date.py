#!/usr/bin/env python

import re,time
import datetime as dt

# Day of week data:
dowl='Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
dowd=dict([
  (dowl[i].lower(),i) for i in range(len(dowl))
])
dowk=dowd.keys()

# Month data:
monl='January February March April May June July August September October November December'.split()
mond=dict([
  (monl[i].lower(),i) for i in range(len(monl))
])
monk=mond.keys()

def day_num(s):
  """Return 0-6 for day of week expressed in s.
  
  >>> print day_num('M')
  0
  >>> print day_num('Tu')
  1
  >>> print day_num('W')
  2
  >>> print day_num('Th')
  3
  >>> print day_num('F')
  4
  >>> print day_num('Sa')
  5
  >>> print day_num('Su')
  6
  >>> print day_num('T')
  None
  >>> print day_num('x')
  None
  >>> print day_num('monday')
  0
  >>> print day_num('mondayx')
  None
  """

  s=s.lower()
  l=len(s)
  possibles=[d for d in dowk if s==d[:l]]
  if len(possibles)==1:
    return dowd[possibles[0]]
  return None

def month_num(s):
  """Return 1-12 for the month as expressed in s.
  
  >>> print month_num('Ja')
  1
  >>> print month_num('F')
  2
  >>> print month_num('Mar')
  3
  >>> print month_num('Ap')
  4
  >>> print month_num('May')
  5
  >>> print month_num('Jun')
  6
  >>> print month_num('Jul')
  7
  >>> print month_num('Au')
  8
  >>> print month_num('S')
  9
  >>> print month_num('O')
  10
  >>> print month_num('N')
  11
  >>> print month_num('D')
  12
  >>> print month_num('December')
  12
  >>> print month_num('Decemberx')
  None
  >>> print month_num('x')
  None
  """

  s=s.lower()
  l=len(s)
  possibles=[d for d in monk if s==d[:l]]
  if len(possibles)==1:
    return mond[possibles[0]]+1
  return None

# [int ](day|week)[s] (ago|before DAY|from DAY|(in the )(past|future))
# DAY := yesterday|now|today|tomorrow|DOW
# DOW := any day of the week
re_relative_date_1=re.compile(
  r'^'
  r'((?P<n>[-+]?\d+)\s+)?'
  r'((?P<units>(day|week)s?)\s+)'
  r'(?P<dir>(ago|(before|from|after)\s+\w+|in\s+the\s+(past|future)))'
# r'(?P<dir>(ago|from\s+(now|today)|in\s+the\s+(past|future)))'
  r'$'
)


def parse_date(datestr):
  """Return a datetime.date object containing the date expressed
  in datestr."""

  datestr=datestr.strip().lower()
  lt=time.localtime()
  today=dt.date(*lt[:3])
  dow=lt[6]

  if s in ('now','today'):
    return today
  if s=='yesterday':
    return today+dt.timedelta(-1)
  if s=='tomorrow':
    return today+dt.timedelta(1)

  m=re_relative_date_1.search(datestr)
  if m:
    #g=Dict(m.groupdict())
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
      day=day_num(dayname)
      if day!=None:
        offset=day-dow
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


if __name__=="__main__":
  import doctest
  failed,total=doctest.testmod()
  if failed==0:
    for s in (
      'now',
      'today',
      'yesterday',
      'day ago',
      'day before today',
      'day after today',
      'tomorrow',
      'day from now',
      'day from today',
      '1 day ago',
      '3 days ago',
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
    ):
      print '%s is %s'%(parse_date(s),s)
