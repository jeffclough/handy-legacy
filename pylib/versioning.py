#!/usr/bin/env python
"""

This module is designed to work with any Python version >= 2.7. We can
a little lower if it's never called as the main module.

This versioning module can also be used to update version meta data in
existing files (if I'd implemented that feature).

"""

import re,sys

# We need this code to run under any version of Python.
if sys.version_info[0]<3:
  # Python 2 code ...
  stringtype=(str,unicode)
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
  version data.

  >>> Version('1.2.3')._parsed_version
  (1, 2, 3, None, None)
  >>> Version('1.2.3.test')._parsed_version
  (1, 2, 3, 'test', None)
  >>> Version('1.2.3.123')._parsed_version
  (1, 2, 3, None, 123)
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
  (1, 2, 3, None, None)
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
  (1, 2, 3, 'beta', None)
  >>> str(a)
  '1.2.3.beta'
  >>> str(b)
  '1.2.3'
  >>> b._parsed_version
  (1, 2, 3, None, None)
  >>> a<b
  True
  >>> a<=b
  True
  >>> a==b
  False
  >>> a!=b
  True
  >>> a>=b
  False
  >>> a>b
  False
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
    value defaults to 0.0.0.
    """

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

  def __cmp__(self,other):
    "Return -1 if self<other, 0 if self==other, or 1 if self>other."

    a=self._version[:3]
    b=other._version[:3]
    if a!=b:
      diff=cmp(a,b)
    else:
      diff=self.meta_compare(other)
    return diff

  def meta_compare(self,other):
    "Just like __cmp__, but looks only at the meta values."

    diff=cmp(self.meta,other.meta)
    a_empty=not all([x==None for x in self.meta])
    b_empty=not all([x==None for x in other.meta])
    if a_empty!=b_empty:
      diff=-diff
    return diff
    

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
      s+='.%s'%self._version[3]
    return s

  def __repr__(self):
    "Return a evaluatable string that would recreate this object."

    return "Version(%r)"%str(self)

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
    if not isinstance(val,stringtype):
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
    (None, None)
    >>> Version.metaParser('test')
    ('test', None)
    >>> Version.metaParser('123')
    (None, 123)
    >>> Version.metaParser('123.45')
    (None, 123.45)
    >>> Version.metaParser('test-123.45')
    ('test-', 123.45)
    """

    if not isinstance(val,stringtype):
      val=str(val)
    m=cls.__version_meta_parser.match(val)
    s=n=None
    if m:
      d=m.groupdict()
      s=(None,d['s'])[bool(d['s'])]
      n=(None,d['n'])[bool(d['n'])]
      if n:
        try:
          n=int(n)
        except:
          try:
            n=float(n)
          except:
            n=None
            s=val
      else:
        n=None
    return (s,n)

python_version=Version(sys.version_info[:4])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DtpVersion(Version):
  """DtpVersion is just like Version, except that it recognizes the
  standard values "dev", "test", "alpha", "beta", and "prod" in it's meta component. For
  purposes of comparing DtpVersion objects, each value is greater than
  the one before it (in the order shown above).

  A meta value of "" is greater than "prod", but any other non-standard
  value is less than "dev" and compares any with other non-standard
  value alphabetically.

  Whatever the meta value is, any standard value may be followed by an
  arbitrary string that only participates in comparison operations if
  the standard part of each DtpVersion's meta value is the same. If the
  standard part of meta's value begins with a '.', the remainder of the
  value will be interpreted numerically (if possible) for comparison purposes.
  Otherwise, it will be interpreted as a string. So "1.2.3.prod.11" is
  greater than "1.2.3.prod.2", and "1.2.3.beta-dog" is greater than
  "1.2.3.beta-chimp", but remember that "1.2.3.test-anything" is
  greater than "1.2.3.dev-something"

  >>> a=DtpVersion('4.5.6')
  >>> str(a)
  '4.5.6'
  >>> dev=DtpVersion(a)
  >>> dev.meta='dev'
  >>> str(dev)
  '4.5.6.dev'
  >>> test=DtpVersion(a)
  >>> test.meta='test'
  >>> str(test)
  '4.5.6.test'
  >>> prod=DtpVersion(a)
  >>> prod.meta='prod'
  >>> str(prod)
  '4.5.6.prod'
  >>> dev==test
  False
  >>> test==prod
  False
  >>> prod==dev
  False
  >>> a==dev
  False
  >>> dev<test
  True
  >>> dev<prod
  True
  >>> test<prod
  True
  >>> prod<a
  True
  >>> x=DtpVersion(a)
  >>> x.meta='x'
  >>> str(x)
  '4.5.6.x'
  >>> a>x
  True
  >>> prod>x
  True
  >>> a>x
  True
  >>> DtpVersion("1.2.3.prod.11")>DtpVersion("1.2.3.prod.2")
  True
  >>> DtpVersion("1.2.3.beta-dog")>DtpVersion("1.2.3.beta-chimp")
  True
  >>> DtpVersion("1.2.3.test-anything")>DtpVersion("1.2.3.dev-something")
  True
  """

  env=dict(
    dev=1,
    test=2,
    alpha=3,
    beta=4,
    prod=5
  )

  def __init__(self,arg):
    # Leave everything to the superclass.
    super(DtpVersion,self).__init__(arg)

  @classmethod
  def metaParser(cls,val):
    """Return an (env_rank,(string,number)) tuple from the given meta
    value."""

    if not val:
      # An empty meta value is greater than any standard value.
      rank,suffix=DtpVersion.env['prod']+1,''
    else:
      # Find any standard value and its sufix.
      for e in DtpVersion.env:
        if val.startswith(e):
          l=len(e)
          rank,suffix=DtpVersion.env[val[:l]],val[l:]
      else:
        # Whatever this is is valued less than "dev", and the whole string is the suffix.
        rank,suffix=0,val
    suffix=super(DtpVersion,cls).metaParser(suffix)
    return (rank,suffix)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__=='__main__':
  try:
    import argparse
  except:
    import argparse27 as argparse

  ap=argparse.ArgumentParser()
  ap.add_argument('--test',action='store_true',default=False,help="Run all internal tests, and terminate.")
  opt=ap.parse_args()

  if opt.test:
    import doctest
    failed,_=doctest.testmod()
    if failed==0:
      sys.exit(0)
    sys.exit(1)
