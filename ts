#!/usr/bin/env python

import optparse,os,re,shutil,stat,sys,time

prog=os.path.basename(sys.argv[0])

op=optparse.OptionParser(
  usage='Usage: %prog [OPTIONS] filename ...',
  description='''This command renames the given file(s) to include the date and
time of each respective file. It renames filename to filename.YYYYMMDD_HHMMSS.
If -c (--copy) is given, the file is copied rather than renamed. If no
argument is given, the current (or offset) time is simply written to
standard output.'''
)
op.add_option('-t','--time',dest='time',choices=('created','accessed','modified'),default='modified',help="Choose which time to use for the timestamp. The choices are 'created', 'accessed', or 'modified'. (default: %default)")
op.add_option('--format',dest='format',action='store',default='%(filename)s.%(time)s',help="Specify a new format for a time-stamped filename. (default: %default)")
op.add_option('--time-format',dest='time_format',action='store',default='%Y%m%d_%H%M%S',help="Specify the format for expressing a file's timestamp. (default: %default)")
op.add_option('-n','--dry-run',dest='dry_run',action='store_true',default=False,help="Don't actually rename any files. Only output the new name of each file as it would be renamed.")
op.add_option('--offset',dest='offset',action='store',default=None,help="Formatted as '[+|-]H:M' or '[+|-]S', where H is hours, M is minutes, and S is seconds, apply the given offset to the time.")
op.add_option('-c','--copy',dest='copy',action='store_true',default=False,help="Copy the file rather than renaming it.")
opt,args=op.parse_args()
if opt.offset:
  # Convert our --offset argument to positive or negative seconds.
  m=re.match(r'(?P<sign>[-+])?((?P<hours>\d+):(?P<minutes>\d+)|(?P<seconds>\d+))$',opt.offset)
  if not m:
    print >>sys.stderr,'%s: Bad --offset argument: %r'%(sys.argv[0],opt.offset)
    sys.exit(1)
  d=m.groupdict('0')
  for k in d:
    if k=='sign':
      d[k]=(1,-1)[d[k]=='-']
    else:
      d[k]=int(d[k])
  opt.offset=d['sign']*(d['hours']*3600+d['minutes']*60+d['seconds'])
else:
  opt.offset=0

if args:
  # This is the usual mode of renaming files according to their time.
  for f in args:
    # Get the time this file was created, accessed, or modified.
    if opt.time=='created':
      t=os.stat(f).st_ctime
    elif opt.time=='accessed':
      t=os.stat(f).st_atime
    else:
      t=os.stat(f).st_mtime
    # Apply any offset
    t+=opt.offset
    # Format the time as a string.
    t=time.strftime(opt.time_format,time.localtime(t))
    # Create the new filename.
    filename=opt.format%dict(filename=f,time=t)
    if opt.dry_run:
      # Just output the new name of the file.
      print "'%s' %s> '%s'"%(f,'-='[opt.copy],filename)
    else:
      # Ensure that there's no existing file by the new filename.
      if os.path.lexists(filename):
        sys.stdout.flush()
        sys.stderr.write('%s: file exists: %s\n'%(prog,filename))
        sys.stderr.flush()
        continue
      else:
        if opt.copy:
          # Copy f to filename.
          print "'%s' => '%s'"%(f,filename)
          shutil.copy2(f,filename)
        else:
          # Rename f to filename.
          print "'%s' -> '%s'"%(f,filename)
          os.rename(f,filename)
else:
  # We're just outputting the current (or offset) time.
  print time.strftime(opt.time_format,time.localtime(time.time()+opt.offset))
