# 
# A semantic versioning implementation for Python.
# See https://semver.org for details.
#

import os,re,sys
  
re_metadata=r'[-0-9A-Za-z]+(\.[0-9A-Za-z]+)*'
re_version=re.compile(
  '(?P<major>\d+)\.(?P<minor>\d+)'
  '(\.(?P<patch>\d+))?'
  '(-(?P<release>'+re_metadata+'))?'
  '(\+(?P<build>'+re_metadata+'))?'
  '$'
)
re_metadata=re.compile(re_metadata+'$')

class Metadata(object):
  def __init__(self,md=None):
    self.md=None
    if isinstance(md,str):
      m=re_metadata.match(md)
      if m==None:
        raise ValueError('Malformed base: %r'%(base,))
    elif isinstance(md,Metadata):
      md=md.md
    else:
      raise TypeError('Bad metadata parameter: %r'%(md,))
    self.md=md

  def __bool__(self):
    return self.md!=None

  def __str__(self):
    if self.md==None:
      return ''
    return self.md

  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__,self.md)

class SemanticVersion(object):

  def __init__(self,version=None):
    """Create this object from an existing SemanticVersion object or from
    a string."""

    if version==None:
      self.major=0
      self.minor=0
      self.patch=None
      self.release=None
      self.build=None
    elif isinstance(version,SemanticVersion):
      self.major=version.major
      self.minor=version.minor
      self.patch=version.patch
      self.release=version.release
      self.build=version.build
    elif isinstance(version,str):
      m=re_version.match(version)
      if m==None:
        raise ValueError('Malformed version string: %r'%(version,))
      m=type('',(),m.groupdict())
      self.major=int(m.major)
      self.minor=int(m.minor)
      self.patch=int(m.patch)
      self.release=Metadata(m.release)
      self.build=Metadata(m.build)

# @classmethod
# def fromComponents(self,major=None,minor=None,patch=None,release=None,build=None):
#   "Create this object from individual version components."

#   # Check parameter types.
#   if major!=None and not isinstance(major,int): raise TypeError('"major" must be either None or an integer.')
#   if minor!=None and not isinstance(minor,int): raise TypeError('"minor" must be either None or an integer.')
#   if patch!=None and not isinstance(patch,int): raise TypeError('"patch" must be either None or an integer.')
#   if release!=None and not isinstance(major,Metadata): raise TypeError('"release" must be either None or a Metadata object.')
#   if build!=None and not isinstance(build,Metadata): raise TypeError('"build" must be either None or a Metadata object.')

#   # Set our attributes from our parameters.
#   self.major=major
#   self.minor=minor
#   self.patch=patch
#   self.release=release
#   self.build=build

  def __str__(self):
    s=(str(self.major),'0')[self.major==None]+'.'+(str(self.minor),'0')[self.minor==None]
    if self.patch:
      s+='.'+str(self.patch)
    if self.release!=None:
      s+='-'+str(self.release)
    if self.build!=None:
      s+='+'+str(self.build)
    return s

  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__,str(self))

  def nextMajor(self):
    self.major+=1
    return self

  def nextMinor(self):
    self.minor+=1
    return self

  def nextPatch(self):
    self.patch+=1
    return self

  def setRelease(self,release):
    if isinstance(release,Metadata):
      self.release=release
    else:
      self.release=Metadata(release)
    return self

  def setBuild(self,build):
    if isinstance(release,Metadata):
      self.release=build
    else:
      self.build=Metadata(build)
    return self

def fromFilename(filename):
  """Given a versioned filename, return a (filename,sep,version) tuple such
  that filename+sep+str(version) is the original filename.
  
  >>> v=SemanticVersion()
  >>> repr(v)
  "SemanticVersion('0.0')"
  >>> repr(v.major)
  '0'
  >>> repr(v.minor)
  '0'
  >>> repr(v.patch)
  'None'
  >>> repr(v.release)
  'None'
  >>> repr(v.build)
  'None'
  >>> v=SemanticVersion('1.2.3-release.4+build.567')
  >>> v.major
  1
  >>> v.minor
  2
  >>> v.patch
  3
  >>> v.release
  Metadata('release.4')
  >>> v.build
  Metadata('build.567')
  >>> v
  SemanticVersion('1.2.3-release.4+build.567')
  >>> fromFilename('1.2.3-release.4+build.567')
  ('', '', SemanticVersion('1.2.3-release.4+build.567'))
  >>> fromFilename('x1.2.3-release.4+build.567')
  ('x', '', SemanticVersion('1.2.3-release.4+build.567'))
  >>> fromFilename('x-1.2.3-release.4+build.567')
  ('x', '-', SemanticVersion('1.2.3-release.4+build.567'))
  >>> fromFilename('somefile-1.2.3-release.4+build.567')
  ('somefile', '-', SemanticVersion('1.2.3-release.4+build.567'))
  """

  m=re_version.search(filename)
  if m:
    i=m.start()
    if i==0:
      f,s,v='','',filename
    elif i==1:
      f,s,v=filename[0],'',filename[1:]
    else:
      f,s,v=filename[:i-1],filename[i-1],filename[i:]
    return f,s,SemanticVersion(v)

if __name__=='__main__':
  import doctest

  t,f=doctest.testmod()
  if f>0:
    sys.exit(1)
