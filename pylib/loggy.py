#!/usr/bin/env python2
import logging,os,platform,sys
import logging.handlers
from logging import NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL

# Get an ordered list of syslog facility names.
syslog_facilities=logging.handlers.SysLogHandler.facility_names.items()
syslog_facilities.sort(key=lambda x:x[1])
syslog_facilities=[x[0] for x in syslog_facilities]

# Get an ordered list of the logging module's log level names.
levels=[(a,b) for a,b in logging._levelNames.items() if isinstance(b,int)]
levels.sort(key=lambda x:x[1])
levels=[x[0].lower() for x in levels if x[0]!='NOTSET']

# Don't leave these global crumbs lying around from the work above.
del a,b,x

def get_log_level_by_name(level):
  if isinstance(level,basestring):
    L=level.upper()
    if L in logging._levelNames:
      return logging._levelNames[L]
  raise ValueError,'bad log level value: %r'%(level,)

def log_lines(log,level,data):
  """Log individual lines at the given log level. If data is a string,
  each line is logged individually. If it is a non-string sequence or an
  iterable of some kind, each entry will be be logged."""

  def line_iter(s):
    """This iterator facilitates stepping through each line of a multi-
    line string without having to use '\n'.split()."""

    i=0
    n=len(s)
    while i<n:
      j=s.find('\n',i)
      if j<0:
        yield s[i:]
        j=n
      else:
        yield s[i:j]
        j+=1
      i=j

  if isinstance(level,basestring):
    level=get_log_level_by_name(level)
  if isinstance(data,basestring):
    for l in line_iter(data):
      log.log(level,l)
  else:
    for l in data:
      if not isinstance(l,basestring):
        l=str(l)
      log.log(level,l)

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
  "$HOME/myprog.log" or "~/myprog.log"), a file stream (e.g.
  sys.stderr), an integer value from SysLogHandler's LOG_* values (e.g.
  SysLogHandler.LOG_USER), or an instance of logging.Handler or any
  subclass thereof.

  The level argument must be one of the following string values:
  debug, info, notice, warning, error, or ctitical. ("warning" is the
  default.)

  The name argument defaults to the name of the currently running
  program, but any string will do. Note that providing one says the
  caller wants to either create a new logger by that name or use a
  logger that's already been set up with that name.

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
  logfmt=kwargs.get('logfmt','%(name)s[%(process)d] %(levelname).1s: %(message)s')
  datefmt=kwargs.get('datefmt','%Y-%m-%d %H:%M:%S ')

  if facility==None:
    # Assume this process has already set up a logger (or just wants to
    # use the default logger), and return that.
    log=logging.getLogger()
    if not log.handlers:
      # Suppress "No handlers could be found ..." message, in case our
      # root logger hasn't been set up. NullHandler is a bit bucket.
      log.addHandler(logging.NullHandler)
    if name:
      log.name=name
    return log

  h=None
  if isinstance(facility,logging.Handler):
    # The caller has provided a handler for us.
    h=facility
    if isinstance(h,logging.StreamHandler):
      # Prefix our log format with the date and time.
      if 'asctime' in logfmt:
        logfmt='%(asctime)s '+logfmt
    f=logging.Formatter(logfmt,datefmt=datefmt)
  else:
    if isinstance(facility,basestring):
      if facility in syslog_facilities:
        # It looks like we're logging to syslog.
        facility=logging.handlers.SysLogHandler.facility_names[facility]
      else:
        # This string must be a filename, so open it for appending.
        facility=os.path.expanduser(os.path.expandvars(facility))
        if os.path.isfile(facility):
          mode='a'
        elif not os.path.exists(facility):
          mode='w'
        else:
          raise ValueError('"%s" exists but is not a regular file.'%(facility,))
        facility=open(facility,mode)

    if isinstance(facility,int):
      # This is a syslog facility number, or had better be.
      system=platform.system()
      if system=='Darwin':
        h=logging.handlers.SysLogHandler(address='/var/run/syslog',facility=facility)
      elif system=='Linux':
        h=logging.handlers.SysLogHandler(address='/dev/log',facility=facility)
      else:
        h=logging.handlers.SysLogHandler(
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


class LogStream(object):
  """If you need to write to some log facility as if it were a stream,
  instantiate LogStream using the parameters you'd use with
  get_logger(). If you don't supply a "level" argument, it will default
  to "debug"."""

  def __init__(self,**kwargs):
    if 'level' not in kwargs:
      kwargs['level']='debug'
    self.level=kwargs['level'].upper()
    self.log=get_logger(**kwargs)

  def write(self,s):
    self.log.log(logging._levelNames[self.level],s)

  def writelines(self,seq):
    for s in seq:
      self.write(s)


if __name__=='__main__':
  import optparse

  op=optparse.OptionParser('usage: %prog [options] message ...')

  op.add_option('--facility',dest='facility',metavar='FACILITY',action='store',default='stdout',help="Log to the given syslog facility (any of: %s). (default: %%default)"%', '.join(syslog_facilities))
  op.add_option('--file',dest='facility',metavar='FILE',action='store',help="Log message to the given file. The special filenames stdout and stderr (or any of the facilities listed above) may also be given. The --file option is just a synonym for --facility. They're exactly the same.")
  op.add_option('--level',dest='level',action='store',default='info',help="Log at the given level, any of: %s (default=%%default)"%', '.join(levels))

  opt,args=op.parse_args()
  if opt.facility=='stdout':   opt.facility=sys.stdout
  elif opt.facility=='stderr': opt.facility=sys.stderr

  if False:
    # Write log data in the usual way.
    log=get_logger(facility=opt.facility,level=opt.level)
    log.log(logging._levelNames[opt.level.upper()],' '.join(args))
  else:
    # Write log data as if to a proper stream.
    f=LogStream(facility=opt.facility,level=opt.level)
    f.write(' '.join(args))
