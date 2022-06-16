#!/usr/bin/env python3

import argparse,os,sys,time
from datetime import date as D
from datetime import datetime as DT,timedelta as TD,timezone

# Get the Unix Epoch time of stardate 0. That's the number of seconds from
# 1970-01-01 to 2323-01-01.
sdzero=time.mktime(DT(2323,1,1).timetuple())

# Compute the number of seconds per stardate unit by dividing the number of
# seconds in a 400-year span by 400,000.
spsd=(time.mktime(DT(2400,1,1).timetuple())-time.mktime(DT(2000,1,1).timetuple()))/400_000

class Error(Exception):
  pass

class Stardate(object):

  def __init__(self,t=None):
    "See Stardate.set()."

    self.set(t)

  def __repr__(self):
    return "Stardate(%r)"%(self.toDatetime())

  def __str__(self):
    """Return the floating-point stardate value to 5 decimal places, 
    which is slightly beyond 1-second resolution.

    A caller who wants the full-precision valuie is welcome to access
    this object's "t" attribute."""

    return f"{self.t:0.5f}"

  def set(self,t):
    """Set this Stardate object from any of several time types:

    Stardate
    datetime.date
    datetime.datetime
    Unix Epoch integer - Number of seconds since 1970-01-01
    Stardate float     - Interpret this float as a stardate.
    None               - New Stardate object gets the current time.
    """

    if isinstance(t,Stardate):
      # Copy the stardate right out of the other object.
      self.t=t.t
    else:
      if t is None:
        # t gets the current Unix Epoch time.
        t=int(time.time())
      if isinstance(t,int):
        # Convert Unix Epoch time to stardate.
        self.t=(t-sdzero)/spsd
      elif isinstance(t,float):
        # No conversion is needed.
        self.t=t
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

  def __bool__(self): return True

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

if __name__=='__main__':
  import argparse

  ap=argparse.ArgumentParser(description="Work with stardate. A floating-point value is interpreted as a stardate and output in Gregorian format. An integer is interpreted as a Unix-epoch value and output as a stardate. A Gregorian date/time string will also be converted to a stardate value.")
  ap.add_argument('-f','--format',action='store',default='%Y-%m-%d %H:%M:%S',help="Use this date/time format for parsing and expressing Gregorian date/time values. (default: %(default)r)")
  ap.add_argument('t',action='store',help="A numeric stardate value or a Gregorian date/time string.")
  opt=ap.parse_args()

  if opt.t:
    # See if we're dealing with a numeric value.
    try:
      # Try interpreting opt.t as an integer Unix epoch value.
      opt.t=int(opt.t)
      print(Stardate(opt.t))
    except ValueError:
      try:
        # Try interpreting opt.t as a stardate value directly.
        opt.t=float(opt.t)
        t=Stardate(opt.t)
        print(t.toDatetime().strftime(opt.format))
      except ValueError:
        # Last try: See how we can interpret this string value.
        if opt.t.lower()=='now':
          # It doesn't get any simpler that this.
          print(Stardate())
        else:
          # Convert Gregorian time to stardate.
          try:
            t=DT.strptime(opt.t,opt.format)
          except:
            t=None
          if not t:
            print(f"ERROR: Cannot interpret {opt.t!r} as a Gregorian date using format {opt.format!r}.",file=sys.stderr)
            sys.exit(1)
          print(Stardate(t))
