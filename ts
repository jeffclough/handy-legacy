#!/usr/bin/env python

import optparse,os,re,shutil,stat,sys,time

# By defalt, files with any of these extensions keep their extension when
# they are renamed with a timestamp.
extensions=set('''
  .3ctype .3fr .a .ac .aiff .ani .anim .ar .arc .ari .arw .asc .asm .awk .bay
  .bin .bmp .bom .book .bsd .c .c++ .cache .cc .cdf .cfg .cgm .cix .class .cmd
  .coffee .collection .com .conf .config .cpp .cr2 .crl .crw .css .csv .cvf .d
  .data .db .dcr .dcs .djvu .dll .dng .doc .docx .drf .dtml .dylib .egg .eip
  .el .eot .eps .epub .erf .exe .exif .fff .gif .git .gnu .gpg .gz .h .hdr
  .help .hpp .htm .html .hts .ico .iiq .inc .info .ini .jar .java .jfif .jpeg
  .jpg .jps .js .jshint .jsm .json .k25 .kdc .key .keystore .kml .l .ldb .lij
  .lnk .lock .log .lrtemplate .lua .m4 .m4a .machelp .makefile .map .markdown
  .mbox .mcl .md .mdc .mef .model .mos .mov .mp3 .mp4 .mpo .mrw .mustache .nef
  .net .nib .node .nrw .o .oab .obm .odg .opts .orf .org .otf .pack .pak .pal
  .pbm .pcf .pdf .pef .pem .pgm .php .pict .pimx .pkg .pl .plist .pm .png .pnm
  .pns .postscript .ppm .prefs .psd .psp .psv .psw .ptx .pub .pxn .py .pyc .pyd
  .qyp .r3d .raf .raw .rb .ref .rif .rpm .rtv .rw2 .rwl .rwz .scpt .scss
  .settings .sh .sig .so .sql .sqlite .sqlite3 .sqlitedb .sr2 .srf .srw .sst
  .sublime-keymap .sublime-menu .svg .svn .swf .tab .tar .tcl .tgz .tif .tiff
  .todo .tsv .ttf .txt .url .uue .vdi .war .watchr .webm .webp .x3f .xaml .xbm
  .xls .xml .xsd .yaml .z .zip'''.split())

prog=os.path.basename(sys.argv[0])

op=optparse.OptionParser(
  usage='Usage: %prog [OPTIONS] filename ...',
  description='''This command renames the given file(s) to include the date and
time of each respective file. It renames filename to filename.YYYYMMDD_HHMMSS.
If -c (--copy) is given, the file is copied rather than renamed. If no
argument is given, the current (or offset) time is simply written to
standard output.'''
)
op.add_option('--age',dest='age',action='store_true',default=False,help="Report the age of the file in seconds. No copying or renaming is performed.")
op.add_option('-t','--time',dest='time',choices=('created','accessed','modified'),default='modified',help="Choose which time to use for the timestamp. The choices are 'created', 'accessed', or 'modified'. (default: %default)")
op.add_option('--format',dest='format',action='store',default='%(filename)s.%(time)s',help="Specify a new format for a time-stamped filename. (default: %default)")
op.add_option('--time-format',dest='time_format',action='store',default='%Y%m%d_%H%M%S',help="Specify the format for expressing a file's timestamp. (default: %default)")
op.add_option('-n','--dry-run',dest='dry_run',action='store_true',default=False,help="Don't actually rename any files. Only output the new name of each file as it would be renamed.")
op.add_option('--offset',dest='offset',action='store',default=None,help="Formatted as '[+|-]H:M' or '[+|-]S', where H is hours, M is minutes, and S is seconds, apply the given offset to the time.")
op.add_option('-c','--copy',dest='copy',action='store_true',default=False,help="Copy the file rather than renaming it.")
op.add_option('-s','--show-me',dest='showme',action='store_true',default=False,help="Only output the timestamped filename of the given file(s). No file is actually renamed or copied.")
op.add_option('--utc',dest='utc',action='store_true',default=False,help="Express all times as UTC (no time zone at all).")
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

def new_filename(filename,timestamp):
  """Return the new filename of the timestamped file."""

  return

if opt.utc:
  # Compute how far, in seconds, local time is from UTC.
  t=time.mktime(time.localtime()) # Make sure we're all rounding floats the same way.
  utc_offset=int(time.mktime(time.gmtime(t))-t)
else:
  utc_offset=0

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
    t+=utc_offset
    t+=opt.offset
    if opt.age:
      print int(time.time()-t+utc_offset)
      continue
    # Format the time as a string.
    t=time.strftime(opt.time_format,time.localtime(t))
    # Create the new filename.
    for ext in extensions:
      if f.endswith(ext):
        # Remove the file extension, but remember what we removed.
        f=f[:-len(ext)]
        break
    else:
      # No special file extension found, so remember that.
      ext=None
    filename=opt.format%dict(filename=f,time=t)
    if ext!=None:
      # Re-attach the file extension to our original and new filenames.
      f+=ext
      filename+=ext
    if opt.showme:
      print filename
    elif opt.dry_run:
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
  if opt.age:
    print int(time.time())+opt.offset+utc_offset
  else:
    print time.strftime(opt.time_format,time.localtime(time.time()+opt.offset+utc_offset))
