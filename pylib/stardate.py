#!/usr/bin/env python2

import argparse,os,sys,time
from datetime import date as D
from datetime import datetime as DT

# Get the Unix Epoch time of stardate 0. That's the number of seconds from
# 1970-01-01 to 2323-01-01.
sdzero=time.mktime(DT(2323,1,1).timetuple())

# Compute the number of seconds per stardate unit by dividing the number of
# seconds in a 400-year span by 400,000.
spsd=(time.mktime(DT(2400,1,1).timetuple())-time.mktime(DT(2000,1,1).timetuple()))/400000

class Error(Exception):
  pass

class Stardate(object):

  __slots__=('t',)

  def __init__(self,t=None):
    "See Stardate.set()."

    self.set(t)

  def __repr__(self):
    return "Stardate(%r)"%(self.toDatetime())

  def __str__(self):
    return '%0.1f'%self.t

  def set(self,t):
    """Set this Stardate object from any of several time types:

    Stardate
    datetime.date
    datetime.datetime
    Unix Epoch integer - Number of seconds since 1970-01-01
    None               - New Stardate object gets the current time.
    """

    if isinstance(t,Stardate):
      # Copy the stardate right out of the other object.
      self.t=t.t
    else:
      if t==None:
        # t gets the current Unix Epoch time.
        t=time.time()
      if isinstance(t,int) or isinstance(t,float):
        # Convert Unix Epoch time to stardate.
        self.t=(t-sdzero)/spsd
      elif isinstance(t,D):
        # Convert either date or datetime to stardate
        self.t=(time.mktime(t.timetuple())-sdzero)/spsd
      else:
        raise Error("Stardate can't be set from %r."%(t,))

  def toUnixEpoch(self):
    "Return the Unix Epoch value of this stardate."

    return self.t*spsd+sdzero

  def toDatetime(self):
    "Return the datetime.datetime value of this stardate."

    return DT.fromtimestamp(self.toUnixEpoch())

  # See https://docs.python.org/2/reference/datamodel.html#basic-customization
  # for more method overloading choices.

  def __hash__(self): return self.t

  def __nonzero__(self): return True

  def __int__(self): return int(self.t)
  def __float__(self): return self.t

  def __lt__(self,other): return self.t<other.t
  def __le__(self,other): return self.t<=other.t
  def __eq__(self,other): return self.t==other.t
  def __ne__(self,other): return self.t!=other.t
  def __gt__(self,other): return self.t>=other.t
  def __ge__(self,other): return self.t>other.t

  def __cmp__(self,other): return self.t-other.t

  def __add__(self,other): return Stardate(self.t+float(other))
  def __sub__(self,other): return Stardate(self.t-float(other))

  def __iadd__(self,other):
    self.t+=float(other)
    return self

  def __isub__(self,other):
    self.t-=float(other)
    return self

  # The __enter__() and __exit__() functions provide "with ... as ..." support.
  def __enter__(self):
    return self

  def __exit__(self,exc_type,exc_value,traceback):
    return False
