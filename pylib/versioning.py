#!/usr/bin/env python3
"""
This module is designed to work with any Python version >= 2.7
(including 3.*). We can go a little lower if it's never called as the
main module.

This versioning module can also be used to update version meta data in
existing files (once I implement that feature).
"""

import re,sys

# We need this code to run under any version of Python.
if sys.version_info[0]<3:
  # Python 2 code ...
  stringtype=(str,str)
else:
  # Python 3 code ...
  stringtype=str

  def cmp(a,b):
    """Provide Python 3's missing cmp(function) with a very poor
    substitute that should never be used for anything more demanding
    than this module."""

    if type(a) is type(b):
      if isinstance(a,(int,float,str,tuple,list)):
        if a<b:
          return -1
        elif a>b:
          return 1
        else:
          return 0
      elif hasattr(a,'__cmp__'):
        return a.__cmp__(b)
    raise ValueError("Cannot compare %s with %s"%(type(a),type(b)))

class Version(object):
  """The Version class is for storing, updating, and comparing semantic
  version data. This is a very simple implementation, but it does allow
  version comparisons to be numeric, so 1.5 < 1.10.

  The meta value defaults to an empty string, but there's a fair amount
  of versatility there too. Any numeric suffix is treated numerically so
  that 1.2.3.beta-5 < 1.2.3.beta-10, but the string portion is still
  compared alphabetically, so 1.2.3.test-5 > 1.2.3.prod-5.

  There's also the problem that 1.2.3 < 1.2.3.prod, but see the
  RankedVersion for a solution to that.

  >>> Version('1.2.3')._parsed_version
  (1, 2, 3, '', 0)
  >>> Version('1.2.3.test')._parsed_version
  (1, 2, 3, 'test', 0)
  >>> Version('1.2.3.123')._parsed_version
  (1, 2, 3, '', 123)
  >>> Version('1.2.3.test-123')._parsed_version
  (1, 2, 3, 'test-', 123)
  >>> Version('1.2.3.test-123.45')._parsed_version
  (1, 2, 3, 'test-', 123.45)
  >>> Version('1.2.3.test.123')._parsed_version
  (1, 2, 3, 'test.', 123)
  >>> Version('1.2.3.test.123.45')._parsed_version
  (1, 2, 3, 'test.', 123.45)
  >>> a=Version()
  >>> str(a)
  '0.0.0'
  >>> repr(a)
  "Version('0.0.0')"
  >>> a=Version((1,2,3))
  >>> a._version
  [1, 2, 3, '']
  >>> a._parsed_version
  (1, 2, 3, '', 0)
  >>> a.major
  1
  >>> a.minor
  2
  >>> a.patch
  3
  >>> a.meta
  ''
  >>> a[3]
  ''
  >>> b=Version(a)
  >>> b._parsed_version
  (1, 2, 3, '', 0)
  >>> a==b
  True
  >>> a.meta='beta'
  >>> a.meta
  'beta'
  >>> a[3]
  'beta'
  >>> a._version
  [1, 2, 3, 'beta']
  >>> a._parsed_version
  (1, 2, 3, 'beta', 0)
  >>> str(a)
  '1.2.3.beta'
  >>> str(b)
  '1.2.3'
  >>> b._parsed_version
  (1, 2, 3, '', 0)
  >>> a<b
  False
  >>> a<=b
  False
  >>> a==b
  False
  >>> a!=b
  True
  >>> a>=b
  True
  >>> a>b
  True
  """

  __version_parser=re.compile(r'(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(\.(?P<meta>.+))?)?)?$')
  __version_meta_parser=re.compile(r'(?P<s>.*?)(?P<n>\d+(\.\d+)?)?$')

  def __init__(self,arg=None):
    """The string form of a version constists if up to 3 numbers
    followed by a free-form metadata value, all separated by '.'
    characters. That might look like any of:

        1
        1.2
        1.2.3
        1.2.3.beta
        1.2.3.beta-3

    The numeric parts are, from left to right, called the major, minor,
    and patch numbers. The metadata can be any string value.

    Initialize this Version instance from a version string, a tuple,
    list, or another Version instance. If arg is None (the default), our
    value defaults to 0.0.0."""

    if not arg:
      self._version=[0,0,0,'']
    elif isinstance(arg,stringtype):
      # Parse this string.
      m=Version.__version_parser.match(arg)
      if not m:
        raise ValueError("Invalid initializer ('%s') for Version instance."%arg)
      d=m.groupdict()
      self._version=[int(d.get(f,0)) for f in ('major','minor','patch') if f in d]
      self._version.append(d.get('meta',''))
      if self._version[3] is None:
        self._version[3]=''
    elif isinstance(arg,(list,tuple)):
      # Use the values from this list or tuple.
      vals=list(arg)
      l=len(vals)
      if l<3:
        vals.extend([0]*(3-l))
        l=3
      try:
        for i in range(3):
          vals[i]=int(vals[i])
      except:
        raise ValueError("Invalid initializer (%r) for %s with non-numeric value at index %d."%(
          arg,self.__cls__.__name__,i
        ))
      if len(vals)<4:
        vals.append('')
      elif len(vals)>4:
        vals[3:]=['.'.join([str(part) for part in vals[3:]])]
      self._version=vals
    elif isinstance(arg,Version):
      # Copy this other Version's value.
      self._version=list(arg._version)
    else:
      # We don't know what to do with this initializer argument.
      raise ValueError("Invalid initializer type (%s) for %s."%(type(arg),self.__cls__.__name__))
    self.tuplize()

  def tuplize(self):
    """Set this Version instance's _parsed_version attribute. This must
    be called every time our _version attribute changes."""

    self._parsed_version=tuple([
      self.major,
      self.minor,
      self.patch
    ]+list(self.metaParser(self.meta)))

  # Python 2 uses __cmp__() for comparison operations.
  def __cmp__(self,other):
    "Return -1 if self<other, 0 if self==other, or 1 if self>other."

    diff=cmp(self._parsed_version[:3],other._parsed_version[:3])
    if diff==0:
      diff=self.meta_compare(other)
    return diff

  def meta_compare(self,other):
    "Just like __cmp__, but looks only at the meta values."

    a_meta=self._parsed_version[3:]
    b_meta=other._parsed_version[3:]
    diff=cmp(a_meta,b_meta)
    return diff

  # These overrides are required for Python 3.
  def __eq__(self,other): return self.__cmp__(other)==0
  def __ne__(self,other): return self.__cmp__(other)!=0
  def __lt__(self,other): return self.__cmp__(other)<0
  def __le__(self,other): return self.__cmp__(other)<=0
  def __ge__(self,other): return self.__cmp__(other)>=0
  def __gt__(self,other): return self.__cmp__(other)>0

  def __getitem__(self,i):
    "Return the ith elelement of our value."

    return self._version[i]

  def __setitem__(self,i,val):
    "Set the ith element of our value."

    self._version[i]=val
    self.tuplize()

  def __str__(self):
    "Return a string version of this Version object's value."

    s='.'.join([str(part) for part in self._version[:3]])
    if self._version[3]:
      s+='.%s'%(self._version[3],)
    return s

  def __repr__(self):
    "Return a evaluatable string that would recreate this object."

    return "Version(%r)"%(str(self),)

  def __iter__(self):
    "Allow iteration to support coercion to tuple and list types."

    for part in self._version:
      yield part

  @property
  def major(self):
    return self._version[0]

  @major.setter
  def major(self,n):
    if not isinstance(n,int):
      n=int(n)
    self._version[0]=n
    self.tuplize()

  @property
  def minor(self):
    return self._version[1]

  @minor.setter
  def minor(self,n):
    if not isinstance(n,int):
      n=int(n)
    self._version[1]=n
    self.tuplize()

  @property
  def patch(self):
    return self._version[2]

  @patch.setter
  def patch(self,n):
    if not isinstance(n,int):
      n=int(n)
    self._version[2]=n
    self.tuplize()

  @property
  def meta(self):
    return self._version[3]

  @meta.setter
  def meta(self,val):
    if val==None:
      val=''
    elif not isinstance(val,stringtype):
      val=str(val)
    self._version[3]=val
    self.tuplize()

  @classmethod
  def metaParser(cls,val):
    """Return any (string,number) tuple that can be parsed from our meta
    value. The number may be an int or float value. If meta doesn't
    begin with a non-numeric string, the tuple's first element will be
    None. If meta doesn't end with a number, the tuple's second element
    will be None.

    >>> Version.metaParser('')
    ('', 0)
    >>> Version.metaParser('test')
    ('test', 0)
    >>> Version.metaParser('123')
    ('', 123)
    >>> Version.metaParser('123.45')
    ('', 123.45)
    >>> Version.metaParser('test-123.45')
    ('test-', 123.45)
    """

    if not isinstance(val,stringtype):
      val=str(val)
    m=cls.__version_meta_parser.match(val)
    s,n='',0
    if m:
      d=m.groupdict()
      s=('',d['s'])[bool(d['s'])]
      n=(0,d['n'])[bool(d['n'])]
      if n:
        try:
          n=int(n)
        except:
          try:
            n=float(n)
          except:
            n=0
            s=val
      else:
        n=0
    return (s,n)

python_version=Version(sys.version_info[:4])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class RankedVersion(Version):
  """RankedVersion is just like Version, except that it recognizes the
  rank values "dev", "test", and "prod" (by default) in its meta
  component. For purposes of comparing RankedVersion objects, each value
  is greater than the one before it (in the order shown above).

  A meta value of "" is greater than "prod", but any other non-ranked
  value is less than "dev" and compares any with other non-ranked value
  alphabetically.

  Whatever the meta value is, any ranked value may be followed by an
  arbitrary string that only participates in comparison operations if
  the ranked part of each RankedVersion's meta value is the same. This
  may be suffixed with a numeric value, which if present, will
  participate in comparison operation according to its numeric value. So
  "1.2.3.prod.11" is greater than "1.2.3.prod.2", and "1.2.3.beta-dog"
  is greater than "1.2.3.beta-chimp", but remember that
  "1.2.3.test-anything" is greater than "1.2.3.dev-something" That's
  what ranking is all about.

  >>> sorted(RankedVersion._ranks.items())
  [('dev', 0), ('prod', 2), ('test', 1)]

  >>> a=RankedVersion('1.2.3')
  >>> a._parsed_version
  (1, 2, 3, 3, '', 0)
  >>> str(a)
  '1.2.3'

  >>> b=RankedVersion(a)
  >>> id(a)!=id(b)
  True
  >>> b._parsed_version
  (1, 2, 3, 3, '', 0)
  >>> str(b)
  '1.2.3'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (True, False, False, True, True, False)

  >>> b.patch=15
  >>> b._parsed_version
  (1, 2, 15, 3, '', 0)
  >>> str(b)
  '1.2.15'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, True, True, False, False)

  >>> b.patch='3'
  >>> b._parsed_version
  (1, 2, 3, 3, '', 0)

  >>> b.meta='prod'
  >>> b._parsed_version
  (1, 2, 3, 2, '', 0)
  >>> str(b)
  '1.2.3.prod'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, False, False, True, True)

  >>> a.meta='test'
  >>> a._parsed_version
  (1, 2, 3, 1, '', 0)
  >>> str(a)
  '1.2.3.test'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, True, True, False, False)

  >>> b.meta='dev'
  >>> b._parsed_version
  (1, 2, 3, 0, '', 0)
  >>> str(b)
  '1.2.3.dev'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, False, False, True, True)

  >>> a.meta=''
  >>> a._parsed_version
  (1, 2, 3, 3, '', 0)
  >>> str(a)
  '1.2.3'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, False, False, True, True)

  >>> a.meta='bogus'
  >>> a._parsed_version
  (1, 2, 3, -1, 'bogus', 0)
  >>> str(a)
  '1.2.3.bogus'
  >>> a==b, a!=b, a<b, a<=b, a>=b, a>b
  (False, True, True, True, False, False)

  >>> RankedVersion("1.2.3.prod.11")>RankedVersion("1.2.3.prod.2")
  True
  >>> RankedVersion("1.2.3.beta-dog")>RankedVersion("1.2.3.beta-chimp")
  True
  >>> RankedVersion("1.2.3.test-anything")>RankedVersion("1.2.3.dev-something")
  True
  """

  # DO NOT MODIFY _ranks DIRECTLY. Use RankedVersion.setRanks() instead. You
  # have been warned.
  _ranks={}

  def __init__(self,arg):
    # Leave everything the superclass.
    super(RankedVersion,self).__init__(arg)

  @classmethod
  def setRanks(cls,*ranks):
    """Assign the rank names, in order, to this class. The default ranks
    are:
        dev
        test
        prod

    If you'd like others, you can set them up by calling this class
    method. For example:

        RankedVersion.setRanks('dev','test','canditate','final')

    Use whatever ranking terminology you prefer, but be sure call this
    method BEFORE instantiating any RankedVersion objects."""

    cls._ranks={str(v):i for i,v in enumerate(ranks)}
    cls.unranked=len(ranks)

  @classmethod
  def metaParser(cls,val):
    """Return an (env_rank,string,number) tuple from the given meta
    value.

    This overloads Version's copy of this method and is called from
    Version's tuplize() method during construction and whenever this
    instance's data changes."""

    if not val:
      # An empty meta value is greater than any ranked value.
      rank,suffix=cls.unranked,''
    else:
      # Find any standard value and its sufix.
      for e in RankedVersion._ranks:
        if val.startswith(e):
          l=len(e)
          # Get the numeric rank and any remainder of the meta value.
          rank,suffix=RankedVersion._ranks[val[:l]],val[l:]
          break
      else:
        # Whatever this is is valued less than our least rank, and the whole string is the suffix.
        rank,suffix=-1,val
    suffix=super(RankedVersion,cls).metaParser(suffix)
    meta=tuple([rank]+list(suffix))
    return meta

# Set up our default rank names (in order).
RankedVersion.setRanks('dev','test','prod')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__=='__main__':

  import argparse

  ap=argparse.ArgumentParser()
  ap.add_argument('--test',action='store_true',default=False,help="Run all internal tests, and terminate.")
  opt=ap.parse_args()

  if opt.test:
    import doctest
    #import pprint
    #print("Ranks:")
    #pprint.pprint(RankedVersion._ranks)
    #print(f"RankedVersion.unranked={RankedVersion.unranked}")
    f,t=doctest.testmod()
    print(f"Passed {t-f} of {t} tests.")
    if not f:
      print(f"python_version: {python_version}")
      print(f"python_version: {repr(python_version)}")
    sys.exit(f>0)
