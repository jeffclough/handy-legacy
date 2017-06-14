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


# [int ](day|week)[s] (ago|before DAY|from DAY|(in the )(past|future))
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
        print '%s is %s'%(parse_date(sample),sample)
