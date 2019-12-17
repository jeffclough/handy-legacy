import re,sys

"""

The Version class is for storing, updating, and comparing semantic
version data. This versioning module can also be used to update version
meta data in files (if I'd implemented that feature).

This module is designed to work with any Python version >= 2.7. We can
a little lower if it's never called as the main module.

"""

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

    if type(a) is type(b) and isinstance(a,(int,float,str,tuple,list)):
      if a<b: return -1
      elif a>b: return 1
      else: return 0
    elif hasattr(a,'__cmp__'):
      return a.__cmp__(b)
    else:
      raise ValueError("Cannot compare %s with %s"%(type(a),type(b)))

class Version(object):
  """
  >>> a=Version()
  >>> str(a)
  '0.0.0'
  >>> repr(a)
  "Version('0.0.0')"
  >>> a=Version((1,2,3))
  >>> a._version
  [1, 2, 3, '']
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
  >>> str(a)
  '1.2.3.beta'
  >>> str(b)
  '1.2.3'
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

  _parser=re.compile(r'(?P<major>\d+)(\.(?P<minor>\d+)(\.(?P<patch>\d+)(\.(?P<meta>.+))?)?)?$')

  def _meta_cmp(self,other):
    """Compare the metadata portions of self and other, returning ...
    
        -1 if self.meta<other.meta,
         0 if self.meta==other.meta, and
         1 if self.meta>other.meta.
     
    This comparison differs from an ordinary string comparison in that
    the empty string is greater than any non-empty string. So "1.2.3" >
    "1.2.3.something".
    
    >>> a=Version('1.2.3')
    >>> b=Version('2.3.4')
    >>> a._meta_cmp(b)
    0
    >>> a.meta='abc'
    >>> b.meta='abc'
    >>> a._meta_cmp(b)
    0
    >>> b.meta=''
    >>> a._meta_cmp(b)
    -1
    >>> b._meta_cmp(a)
    1
    >>> b.meta='def'
    >>> a._meta_cmp(b)
    -1
    >>> b._meta_cmp(a)
    1
    """

    diff=cmp(self.meta,other.meta)
    if bool(self.meta)!=bool(other.meta):
      diff=-diff
    return diff

  def __init__(self,arg=None):
    """The string form of a version constists if up to 3 numbers
    followed by a free-form metadata value, all separated by '.'
    characters. That might look like any of:

        1
        1.2
        1.2.3
        1.2.3.beta

    The numeric parts are, from left to right, called the major, minor,
    and patch numbers. The metadata can be any string value.
    
    Initialize this Version instance from a version string, a tuple,
    list, or another Version instance. If arg is None (the default), our
    value defaults to 0.0.0.
    """

    if arg is None:
      self._version=[0,0,0,'']
    elif isinstance(arg,stringtype):
      # Parse this string.
      m=Version._parser.match(arg)
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
        raise ValueError("Invalid initializer (%r) for Version with non-numeric value in positions %d."%(arg,i+1))
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
      raise ValueError("Invalid initializer type (%s) for Version instance."%type(arg))

  def __cmp__(self,other):
    """Compare this object's value with that of the other object,
    returning -1 if self<other, 0 if self==other, and 1 if self>other.
    The three numeric components are compared numerically. The metadata
    component is compared using the meta_comp() class method.
    
    The _meta_cmp() class method may be overridden in a subclass if you
    want to provide your own logic for that. For example if
    dev<test<prod, or if numeric metadata should not be compared as
    string values, you'll want to provide your own method for handling
    that.
    
    See _meta_cmp()'s documentation for a description of Version's
    implementation."""

    a=self._version[:3]
    b=other._version[:3]
    if a!=b:
      diff=cmp(a,b)
    else:
      diff=self._meta_cmp(other)
    return diff

  def __eq__(self,other): return self._version==other._version
  def __ne__(self,other): return self._version!=other._version
  #def __lt__(self,other): return self.__cmp__(other)<0
  #def __le__(self,other): return self.__cmp__(other)<=0
  #def __gt__(self,other): return self.__cmp__(other)>0
  #def __ge__(self,other): return self.__cmp__(other)>=0
  def __lt__(self,other): return cmp(self,other)<0
  def __le__(self,other): return cmp(self,other)<=0
  def __gt__(self,other): return cmp(self,other)>0
  def __ge__(self,other): return cmp(self,other)>=0
 
  def __getitem__(self,i):
    "Return the ith elelement of our value."

    return self._version[i]

  def __setitem__(self,i,val):
    "Set the ith element of our value."

    self._version[i]=val

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
  def major(self): return self[0]

  @major.setter
  def major(self,val): self[0]=int(val)

  @property
  def minor(self): return self[1]

  @minor.setter
  def minor(self,val): self[1]=int(val)

  @property
  def patch(self): return self[2]

  @patch.setter
  def patch(self,val): self[2]=int(val)

  @property
  def meta(self): return self[3]

  @meta.setter
  def meta(self,val): self[3]=val

python_version=Version(sys.version_info[:4])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DtpVersion(Version):
  """
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
  """

  env=dict(
    dev=1,
    test=2,
    prod=3
  )

  def __init__(self,arg):
    # Leave everything to the superclass.
    super(DtpVersion,self).__init__(arg)

  def _meta_cmp(self,other):
    """Compare the metadata portion of self and other, returning ...
        -1 if self.meta<other.meta,
         0 if self.meta==other.meta, and
         1 if self.meta>other.meta.
     
    This implementation uses dev<test<prod ordering, and everything else
    is less than dev, and an empty metadata string is greater than
    anything else."""

    if '' in (self.meta,other.meta):
      diff=-cmp(self.meta,other.meta)
    else:
      i=DtpVersion.env.get(self.meta,0)
      j=DtpVersion.env.get(other.meta,0)
      diff=i-j
    if diff<0:
      diff=-1
    elif diff>0:
      diff=1
    return diff

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
