#!/usr/bin/env python

from math import sqrt

def simple(val=None,count=None):
  """Return a list of primes up to and including <val> or the first
  <count> prime values. Exactly one of these must be given.
  
  This is a very simple algorithm that uses the fact that every
  composite number n has at least one prime factor <=sqrt(n). It builds
  a list of primes from 2 up to the desired value or number of primes.
  
  Pros:
  * This algorithm is so simple that it's easy to code from memory.
  * It's very memory-efficient because it stores only prime numbers.
  * It's more time-efficient than simpler sieves in that it checks only
    for prime factors.
  
  Cons:
  * This is suitable only for small primes. In practical terms, this
    is a bad choice in general for 9-digit primes, and for Python (or
    other interpreted languages), it's not worth much after 7 digits."""

  assert (val!=None)!=(count!=None)

  primes=[2]
  if val:
    # Find all primes up to and including val.
    for c in range(3,val+1,2):
      m=int(sqrt(c))
      for p in primes:
        if p>m:
          primes.append(c)
          break
        if c%p==0:
          break
  elif count:
    # Find the first count primes.
    c=3
    while len(primes)<count:
      m=int(sqrt(c))
      for p in primes:
        if p>m:
          primes.append(c)
          break
        if c%p==0:
          break
      c+=2

  return primes

methods=dict(
  simple=simple,
)

if __name__=='__main__':
  import argparse,json,os,sys
  from time import time
  from english import pnum

  ap=argparse.ArgumentParser()
  ap.add_argument('--method',action='store',default='simple',choices=tuple(sorted(methods.keys())),help="""Use "my usual method" for computing primes.""")
  ap.add_argument('--count',action='store',type=int,default=None,help="""Find the first COUNT prime values. Using --count means that no VAL arguent may be given.""")
  ap.add_argument('-o','--output',action='store',choices=('csv','json','json-pretty','stream','none'),default='stream',help="""Set the output format for prime values. (default: %(default)s)""")
  ap.add_argument('--sep',action='store',default=None,help="""If you want comma-separated numbers in the output, use "--sep ,". If you're feeling weird, you can also use "--sep ,5" to group digits by fives rather than threes. You be you.""")
  ap.add_argument('--top',metavar='M',action='store',type=int,default=None,help="""Show only the highest M prime values.""")
  ap.add_argument('-v','--verbose',action='store_true',help="""Precede output of prime numbers with some information describing our search for those values.""")
  ap.add_argument('val',metavar='VAL',action='store',type=int,default=None,nargs='?',help="""The highest numeric value to be tested for primality. No --count option may be given if VAL is present.""")
  opt=ap.parse_args()
  if (opt.count==None)==(opt.val==None):
    print("\nExactly one of --count or VAL must be given on the command line.\n")
    ap.print_usage()
    sys.exit(1)
  opt.method=methods[opt.method]

  if __name__=='__main__':
    t0=time()
    if opt.count:
      primes=opt.method(count=opt.count)
    else:
      primes=opt.method(val=opt.val)
    t1=time()
    t=t1-t0
    if opt.count:
      opt.val=primes[-1]
    if opt.verbose:
      print("Found %d prime values (in %d bytes) from 2 to %d in %f seconds."%(len(primes),sys.getsizeof(primes),opt.val,t))

    # Keep only the last few primes if --top was used.
    if opt.top:
      primes=primes[-opt.top:]

    # Output our primes.
    if opt.output=='csv':
      # Output one value per line.
      if opt.sep:
        for p in primes: print(pnum(p,sep=opt.sep))
      else:
        for p in primes: print(p)
    elif opt.output.startswith('json'):
      if opt.output>'json':
        # Output standard JSON.
        json.dump(primes,sys.stdout,indent=2)
      else:
        # Output valid JSON that's also easy to read.
        json.dump(primes,sys.stdout)
      sys.stdout.write('\n')
    elif opt.output=='stream':
      # Output one space-separated line of primes.
      if opt.sep:
        sys.stdout.write(pnum(primes[0],sep=opt.sep))
      else:
        sys.stdout.write(str(primes[0]))
      del primes[0]
      if opt.sep:
        for p in primes: sys.stdout.write(' %s'%pnum(p,sep=opt.sep))
      else:
        for p in primes: sys.stdout.write(' %d'%p)
      sys.stdout.write('\n')

