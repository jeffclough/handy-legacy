#!/usr/bin/env python
import logging,os,platform,sys
from logging.handlers import SysLogHandler

# Get an ordered list of syslog facility names.
syslog_facilities=SysLogHandler.facility_names.items()
syslog_facilities.sort(key=lambda x:x[1])
syslog_facilities=[x[0] for x in syslog_facilities]

# Get an ordered list of the logging module's log level names.
levels=[(a,b) for a,b in logging._levelNames.items() if isinstance(b,int)]
levels.sort(key=lambda x:x[1])
levels=[x[0].lower() for x in levels if x[0]!='NOTSET']

def get_log_level_by_name(level):
  if isinstance(level,basestring):
    L=level.upper()
    if L in logging._levelNames:
      return logging._levelNames[L]
  raise ValueError,'bad log level value: %r'%(level,)

def get_logger(**kwargs):
  """Return the default logging object (if facility==None), or set up a
  new logger in any other case, and return that. Keyword arguments and
  their default values are:

    facility  None
    level     'warning'
    name      basename of process, minus any extension
    logfmt    '%(name)s %(levelname).1s: %(message)s'
    datefmt   '%Y-%m-%d %H:%M:%S '

  Note the space at the end of datefmt's default value. None is provided
  automatically, so end with one if you want one there.

  If facility argument is None (the default), the caller is assumed to
  want to use a previously configured logger or just wants to use the
  root logger. Otherwise, the facility argument may be a filename (e.g.
  "$HOME/myprog.log"), a file stream (e.g. sys.stderr), an integer value
  from SysLogHandler's LOG_* values (e.g. SysLogHandler.LOG_USER), or an
  instance of logging.Handler or any subclass thereof.

  The level argument must be one of the following string values:
  debug, info, notice, warning, error, or ctitical. ("warning" is the
  default.)

  The name argument defaults to the name of the currently running
  program, but any string will do. Note that providing says the caller
  wants to either create a new logger by that name or use a logger
  that's already been set up with that name.

  The logfmt string sets the format of the logged messages. See the
  logging.LogRecord class for details.

  The datefmt argument is used only when logging to files, and is used
  to format the "asctime" field that prepends every logged message. Set
  this to an empty string if you want to suppress "asctime" in the log
  output. Be sure to end datefmt with a space character (or other
  separator) if you want the to separate the timestamp from the rest of
  the logged message."""

  # Instantiate our keyword arguments as local variables.
  facility=kwargs.get('facility',None)
  level=kwargs.get('level','warning')
  name=kwargs.get('name',os.path.basename(sys.argv[0]).rsplit('.',1)[0])
  logfmt=kwargs.get('logfmt','%(name)s %(levelname).1s: %(message)s')
  datefmt=kwargs.get('datefmt','%Y-%m-%d %H:%M:%S ')

  if facility==None:
    # Assume this process has already set up a logger (or just wants to
    # use the default logger), and return that.
    return logging.getLogger()

  h=None
  if isinstance(facility,logging.Handler):
    # The caller has provided us with his own handler.
    h=facility
    if isinstance(h,logging.StreamHandler):
      # Include the date and time in our log format.
      f=logging.Formatter('%(asctime)s'+logfmt,datefmt=datefmt)
    else:
      # Trust the logging service to provide current date and time.
      f=logging.Formatter(logfmt)
  else:
    if isinstance(facility,basestring):
      if facility in syslog_facilities:
        # It looks like we're logging to syslog.
        facility=SysLogHandler.facility_names[facility]
      else:
        # This string must be a filename, so open it for appending.
        facility=open(facility,'a')

    if isinstance(facility,int):
      # This is a syslog facility number, or had better be.
      system=platform.system()
      if system=='Darwin':
        h=SysLogHandler(address='/var/run/syslog',facility=facility)
      elif system=='Linux':
        h=SysLogHandler(address='/dev/log',facility=facility)
      else:
        h=SysLogHandler(
          address=('localhost',logging.handlers.SYSLOG_UDP_PORT),
          facility=facility
        )
      f=logging.Formatter(logfmt)
    elif isinstance(facility,file):
      # This is a stream, so set up formatting accordingly.
      h=logging.StreamHandler(facility)
      f=logging.Formatter('%(asctime)s'+logfmt,datefmt=datefmt)
    else:
      raise ValueError,'bad log facility value: %r'%(facility,)

  if isinstance(level,basestring):
    # If level is a string, make sure it is upper case.
    level=level.upper()
  elif isinstance(level,int) and level in logging._levelNames:
    level=logging._levelNames[level]
  else:
    raise ValueError,'bad log level value: %r'%(level,)

  # Now create the new logger, and return it to the caller.
  h.setFormatter(f)
  log=logging.getLogger(name)
  log.addHandler(h)
  log.setLevel(logging._levelNames[level])
  #log.name=name
  return log

if __name__=='__main__':
  import optparse

  op=optparse.OptionParser('usage: %prog [options] message ...')

  op.add_option('--facility',dest='facility',metavar='FACILITY',action='store',default='stdout',help="Log to the given syslog facility (any of: %s). (default: %%default)"%', '.join(syslog_facilities))
  op.add_option('--file',dest='facility',metavar='FILE',action='store',help="Log message to the given file. The special filenames stdout and stderr (or any of the facilities listed above) may also be given. The --file option is just a synonym for --facility. They're exactly the same.")
  op.add_option('--level',dest='level',action='store',default='info',help="Log at the given level, any of: %s (default=%%default)"%', '.join(levels))

  opt,args=op.parse_args()
  if opt.facility=='stdout':   opt.facility=sys.stdout
  elif opt.facility=='stderr': opt.facility=sys.stderr

  log=get_logger(facility=opt.facility,level=opt.level)
  log.log(logging._levelNames[opt.level.upper()],' '.join(args))
