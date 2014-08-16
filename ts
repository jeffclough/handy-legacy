#!/usr/bin/env python

import optparse,os,shutil,stat,sys,time

prog=os.path.basename(sys.argv[0])

op=optparse.OptionParser(
  usage='Usage: %prog [OPTIONS] filename ...',
  description='''This command renames the given file(s) to include the date and time of
each respective file. It renames filename to filename.YYYYMMDD_HHMMSS.
If -c (--copy) is given, the file is copied rather than renamed.'''
)
op.add_option('-t','--time',dest='time',choices=('created','accessed','modified'),default='modified',help="Choose which time to use for the timestamp. The choices are 'created', 'accessed', or 'modified'. (default: %default)")
op.add_option('--format',dest='format',action='store',default='%(filename)s.%(time)s',help="Specify a new format for a time-stamped filename. (default: %default)")
op.add_option('--time-format',dest='time_format',action='store',default='%Y%m%d_%H%M%S',help="Specify the format for expressing a file's timestamp. (default: %default)")
op.add_option('-n','--dry-run',dest='dry_run',action='store_true',default=False,help="Don't actually rename any files. Only output the new name of each file as it would be renamed.")
op.add_option('-c','--copy',dest='copy',action='store_true',default=False,help="Copy the file rather than renaming it.")
opt,args=op.parse_args()

for f in args:
  # Get the time this file was created, accessed, or modified.
  if opt.time=='created':
    t=os.stat(f).st_ctime
  elif opt.time=='accessed':
    t=os.stat(f).st_atime
  else:
    t=os.stat(f).st_mtime
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
