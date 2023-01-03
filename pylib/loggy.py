#!/usr/bin/env python3
import logging,os,platform,sys
import logging.handlers
from logging import NOTSET,DEBUG,INFO,WARNING,ERROR,CRITICAL
from io import IOBase

from debug import DebugChannel
dc=DebugChannel(label='D')

# Get an ordered list of syslog facility names.
syslog_facilities=list(logging.handlers.SysLogHandler.facility_names.items())
syslog_facilities.sort(key=lambda x:x[1])
syslog_facilities=[x[0] for x in syslog_facilities]

# Get a list of the logging module's level names ordered by priority.
try:
  # This is how it worked in Python 2.7.
  _nameToLevel={k:v for k,v in list(logging._levelNames.items()) if isinstahce(v,int)}
except AttributeError:
  # At some point, logging.py's internals changed to this.
  _nameToLevel={k:v for k,v in list(logging._nameToLevel.items())}

levels=sorted([(k,v) for k,v in list(_nameToLevel.items()) if k!=logging.NOTSET],key=lambda x:x[1])
levels=[k for k,_ in levels]

def get_log_level_by_name(level):
  if isinstance(level,str):
    L=level.upper()
    if L in logging._nameToLevel:
      return logging._nameToLevel[L]
  raise ValueError('bad log level value: %r'%(level,))

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

  if isinstance(level,str):
    level=get_log_level_by_name(level)
  if isinstance(data,str):
    for l in line_iter(data):
      log.log(level,l)
  else:
    for l in data:
      if not isinstance(l,str):
        l=str(l)
      log.log(level,l)

def get_logger(
  facility=None,
  level='warning',
  name=None,
  logfmt='%(name)s[%(process)d] %(levelname).1s: %(message)s',
  datefmt='%Y-%m-%d %H:%M:%S ',
  child=None
):
  """Return the default logging object (if facility==None), or set up a
  new logger in any other case, and return that.

  If facility argument is None (the default), the caller is assumed to
  want to use a previously configured logger or just wants to use the
  root logger. Otherwise, the facility argument may be a filename (e.g.
  "$HOME/myprog.log" or "~/myprog.log"), a file stream (e.g.
  sys.stderr), an integer value from SysLogHandler's LOG_* values (e.g.
  SysLogHandler.LOG_USER), or an instance of logging.Handler or any
  subclass thereof.

  The level argument must be one of the following string values: debug,
  info, notice, warning, error, or ctitical. ("warning" is the default.)

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
  the logged message.

  Note the space at the end of datefmt's default value. None is provided
  automatically, so end with one if you want one there.

  The child argument, if given, must be a string and will name the child
  logger of the main logger (which must already exist). A child logger
  is will be returned in this case. This argument has meaning only if
  facility is not given.
  """

  dc(f"facility={facility}, level={level}, name={name!r}, logfmt={logfmt!r}, datefmt={datefmt!r}, child={child!r}")

  # If no name is provided, use the name of the current program (minus
  # any file extension).
  if not name:
    name=os.path.basename(sys.argv[0]).rsplit('.',1)[0]

  if facility is None:
    if child:
      # Initialize this log as a child of the main logger.
      dc(f"Setting up child logger {child!r}.")
      log=logging.getLogger().getChild(child)
    else:
      # Assume this process has already set up a logger (or just wants to
      # use the default logger), and return that.
      dc(f"No facility, so getting root logger.")
      log=logging.getLogger()
      if not log.handlers:
        # Suppress "No handlers could be found ..." message, in case our
        # root logger hasn't been set up. NullHandler is a bit bucket.
        log.addHandler(logging.NullHandler)
      if name:
        log.name=name
      dc(f"Returning with logger {log!r}")
      return log

  if not child:
    # Child loggers use the parent logger's facility, handler, and
    # formatting.
    h=None
    if isinstance(facility,logging.Handler):
      dc(f"facility is logging.Handler {facility!r}")
      # The caller has provided a handler for us.
      h=facility
      if isinstance(h,logging.StreamHandler):
        # Prefix our log format with the date and time.
        if 'asctime' in logfmt:
          logfmt='%(asctime)s '+logfmt
      f=logging.Formatter(logfmt,datefmt=datefmt)
    else:
      if isinstance(facility,str):
        dc(f"facility is string {facility!r}")
        if facility in syslog_facilities:
          # It looks like we're logging to syslog.
          facility=logging.handlers.SysLogHandler.facility_names[facility]
        else:
          # This string must be a filename, so open it for appending.
          dc(f"Treating facility={facility!r} as a filename.")
          facility=os.path.expanduser(os.path.expandvars(facility))
          dc(f"Expanded filename is {facility!r}.")
          if os.path.isfile(facility):
            mode='a'
          elif not os.path.exists(facility):
            mode='w'
          else:
            raise ValueError('"%s" exists but is not a regular file.'%(facility,))
          facility=open(facility,mode)

      if isinstance(facility,int):
        dc(f"facility is integer {facility!r}")
        # This is a syslog facility number, or had better be.
        system=platform.system()
        if system=='Darwin':
          h=logging.handlers.SysLogHandler(address='/var/run/syslog',facility=facility)
        elif system=='Linux':
          h=logging.handlers.SysLogHandler(address='/dev/log',facility=facility)
        else:
          dc(f"Createing SysLogHandler for this logger.")
          h=logging.handlers.SysLogHandler(
            address=('localhost',logging.handlers.SYSLOG_UDP_PORT),
            facility=facility
          )
        dc(f"Createing logging.Formatter from logfmt={logfmt!r}")
        f=logging.Formatter(logfmt)
      elif isinstance(facility,IOBase):
        dc(f"facility is {facility!r}")
        # This is a stream, so add date and time to the start of our log format.
        h=logging.StreamHandler(facility)
        logfmt='%(asctime)s'+logfmt
        dc(f"Createing logging.Formatter from logfmt={logfmt!r}, datefmt={datefmt!r}")
        f=logging.Formatter(logfmt,datefmt=datefmt)
      else:
        raise ValueError('bad log facility value: %r'%(facility,))

  if isinstance(level,str):
    # If level is a string, make sure it is upper case.
    level=level.upper()
    dc(f"level is string {level!r}")
  elif isinstance(level,int) and level in _nameToLevel:
    dc(f"level is int {level!r}")
    level=_nameToLevel[level]
    dc(f"converted level is int {level!r}")
  else:
    raise ValueError('bad log level value: %r'%(level,))

  # Now create the new logger, and return it to the caller.
  if not child:
    dc(f"Applying formatter {f!r} to handler {h!r}")
    h.setFormatter(f)
    log=logging.getLogger(name)
    dc(f"Adding handler to logger")
    log.addHandler(h)
  l=_nameToLevel[level]
  dc(f"_nameToLevel[{level!r}]{_nameToLevel[level]!r}")
  log.setLevel(_nameToLevel[level])
  dc(f"Returning with logger {log!r}")
  return log


class LogStream(object):
  """If you need to write to some logger as if it were a stream,
  instantiate LogStream using the parameters you'd use with
  get_logger(). You can also """

  def __init__(self,
    faciliity=None,
    level='warning',
    name=None,
    logfmt='%(name)s[%(process)d] %(levelname).1s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S ',
    child=None,
    logger=None
  ):
    """These arguments are teh same as for get_logger, except for the
    logger argument. If you already have a logger set up and simply want
    to be able to write to it in a stream-like way, pass that logger to
    this initializer as logger's value."""

    if logger:
      self.level=logging.getLevelName(logger.level)
      dc(f"{logger.handlers}")
      dc(f"self.level={self.level!r}")
      self.log=logger
    else:
      self.level=level
      self.log=getlogger(facility=facility,level=level,name=name,logfmt=logfmt,datefmt=datefmt,child=child)

  def write(self,s):
    self.log.log(_nameToLevel[self.level],s)

  def writelines(self,seq):
    for s in seq:
      self.write(s)

  def flush(self):
    "This method does nothing, but it needs to be here."

    pass


if __name__=='__main__':
  import argparse

  ap=argparse.ArgumentParser(description="Running this command test's the loggy.py module. It writes a single log message according to the options given.")

  ap.add_argument('--debug',action='store_true',help="Turn on debug output (for use during development of the loggy module).")
  ap.add_argument('--facility',action='store',default='stdout',help="Log to the given syslog facility (any of: %s). (default: %%(default)s)"%', '.join(syslog_facilities))
  ap.add_argument('--file',dest='facility',metavar='FILE',action='store',help="Log message to the given file. The special filenames stdout and stderr (or any of the facilities listed above) may also be given. The --file option is just a synonym for --facility. They're exactly the same.")
  ap.add_argument('--level',action='store',default='info',help="Log at the given level, any of: %s (default=%%(default)s)"%', '.join(levels))
  ap.add_argument('--stream',action='store_true',help="Write out log message using our LogStream rather than a simple logger instance.")
  ap.add_argument('args',metavar='message',action='store',nargs='+',help="The message to be logged. ")

  opt=ap.parse_args()
  dc.enable(opt.debug)
  if opt.facility=='stdout':
    opt.facility=sys.stdout
  elif opt.facility=='stderr':
    opt.facility=sys.stderr

  log=get_logger(facility=opt.facility,level=opt.level)
  if opt.stream:
    # Write log data as if to a proper stream.
    f=LogStream(logger=log)
    f.write(' '.join(opt.args))
  else:
    # Write log data in the usual way.
    log.log(_nameToLevel[opt.level.upper()],' '.join(opt.args))
