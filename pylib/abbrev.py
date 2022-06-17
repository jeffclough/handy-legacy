#!/usr/bin/env python3

import re,time
import datetime as dt

import sys # for debugging

class IndexedNames(object):
  """Handle the tedium of matching things like day and month names to
  their proper index values, even when given only an abbreviated name to
  get the index value of. Use dictionary syntax to get and set index
  values on an instance of this class.

  >>> foo=IndexedNames('Abcd Abef Ghij Klmn Opqr Opqs Opqt'.split(),4,2)
  >>> print(repr(foo)
  IndexedNames(('Abcd', 'Abef', 'Ghij', 'Klmn', 'Opqr', 'Opqs', 'Opqt'), start=4, step=2)
  >>> print(foo['abc']
  4
  >>> print(foo['abe']
  6
  >>> foo['totally bogus']
  Traceback (most recent call last):
  KeyError: 'totally bogus'
  >>> foo['a']
  Traceback (most recent call last):
  KeyError: 'a'
  >>> print('ghij' in foo)
  True
  >>> print('ghi' in foo)
  True
  >>> print('gh' in foo)
  True
  >>> print('g' in foo)
  True
  >>> print(foo[0])
  Traceback (most recent call last):
  KeyError: '0'
  >>> print(foo[4])
  Abcd
  >>> print(foo[8])
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
  >>> print(dow.get('M'))
  0
  >>> print(dow.get('Tu'))
  1
  >>> print(dow.get('W'))
  2
  >>> print(dow.get('Th'))
  3
  >>> print(dow.get('F'))
  4
  >>> print(dow.get('Sa'))
  5
  >>> print(dow.get('Su'))
  6
  >>> print(dow.get('T'))
  None
  >>> print(dow.get('x'))
  None
  >>> print(dow.get('monday'))
  0
  >>> print(dow.get('mondayx'))
  None
  
  """
  
  def __init__(self,name_list,start=0,step=1):
    """Store an index value, starting at 0 by default, for each name in
    the list. Also precompute all distinct abbreviations for those
    names, remembering each one by the index of the full name.

    Every name in the list must be case-insensitively distinct from
    every other name, an no full name may match the beginning of another
    name. Otherwise, a KeyError will be raised."""

    # Remember our list of names and in what order they were given.
    self.name_list=tuple(name_list)
    self.start=int(start)
    try:
      self.step=int(step)
      1/self.step # Raise an exception if step is 0.
    except:
      raise ValueError('Illegal step value: %r'%(step,))
    #self.num_dict=dict([
    #  (self.name_list[i].lower(),(i,self.start+self.step*i)) for i in range(len(self.name_list))
    #])
    self.num_dict={
      self.name_list[i].lower():(i,self.start+self.step*i)
        for i in range(len(self.name_list))
    }

    # Verify that no two names match and that no name is an abbreviation for any
    # other name.
    keys=list(self.num_dict.keys())
    for i in range(len(self.name_list)):
      for j in range(len(self.name_list)):
        if i!=j:
          if self.name_list[i].lower()==self.name_list[j].lower():
            raise KeyError(f"Duplicate items in list: {self.name_list[i]!r}")
    for i in range(len(keys)):
      for j in range(len(keys)):
        if i!=j:
          if keys[i].startswith(keys[j]):
            raise KeyError(f"{keys[j]!r} is an abbreviation of {keys[i]!r}")

    # Add decreasingly minimal forms of all keys to dictionary.
    for name in keys:
      for i in range(1,len(name)):
        partial=name[:i]
        possibles=[s for s in keys if s.startswith(partial)]
        if len(possibles)==1:
          val=self.num_dict[name]
          #self.num_dict.update(dict([
          #  (name[:j],val) for j in range(i,len(name))
          #]))
          self.num_dict.update({
            name[:j]:val
              for j in range(i,len(name))
          })
          break

  def __repr__(self):
    """Return a string that could be passed to eval() to recreate this
      object."""

    return '%s(%r, start=%r, step=%r)'%(self.__class__.__name__,self.name_list,self.start,self.step)

  def __contains__(self,key):
    """Return true if key is either the name or index of an item stored
    in this object."""

    if isinstance(key,str):
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

    if isinstance(key,str):
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

    #print('DEBUG: num_dict=%r'%(self.num_dict,),file=sys.stderr)

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



class AbbrevDict(dict):

  def __init__(self,*args,**kwargs):
    """This is just like dict's constructor, but it also accepts a
    keymod keyword argument. If given, keymod must be a function that
    accepts a key value as its sole argument and returns the modified
    version of that key (e.g. the lower-case version of the key)."""

    if 'keymod' in kwargs:
      self.keymod=kwargs['keymod']
      del kwargs['keymod']
    else:
      self.keymod=None
    super(AbbrevDict,self).__init__(args,kwargs)

  def __getitem__(self,key):
    if self.keymod:
      key=self.keymod(key)
    super(AbbrevDict,self).__getitem__(key)

  def __setitem__(self,key,val):
    if self.keymod:
      key=self.keymod(key)
    super(AbbrevDict,self).__setitem__(key,val)

  def __contains__(self,key):
    if self.keymod:
      key=self.keymod(key)
    return super(AbbrevDict,self).__contains__(key)

  def __del__(self,key):
    if self.keymod:
      key=self.keymod(key)
    super(AbbrevDict,self).__del__(key)

  ### NOT FINISHED
