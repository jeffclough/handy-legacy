#!/usr/bin/env python2

import optparse,os,sys
import ansi

op=optparse.OptionParser()
op.add_option('--dump',dest='dump',action='store_true',default=False,help="Only dump the data once it's all been read. Don't actually plot anything.")
opt,args=op.parse_args()

# Get the data.
data=[]
if not (sys.stdin.isatty() or args):
  data_from(sys.stdin)
else:
  for filename in args:
    if filename=='-':
      data_from(sys.stdin)
    else:
      f=open(filename)
      data_from(f)
      f.close()

# Plot the data.
if opt.dump:
  for row in data:
    print ' '.join([str(field) for field in row])

