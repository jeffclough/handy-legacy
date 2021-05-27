import atexit,os,signal

# Be able to look up signal names from their numbers.
signal_names=dict([
  (getattr(signal,sig),sig) for sig in dir(signal)
    if sig.startswith('SIG') and not '_' in sig
])

class DaemonContext(object):
  "This is an implementation of PEP-3143."

  def __init__(self,**kwargs):

    # Get our arguments. Since we're destroying our keyword dict, we'll use a
    # copy.
    kw=dict(kwargs)
    for var,dval in (
        ('files_preserve',None),
        ('chroot_directory',None),
        ('working_directory','/'),
        ('umask',0),
        ('pidfile',None),
        ('detach_process',None),
        ('signal_map',None),
        ('uid',os.getuid()),
        ('gid',os.getgid()),
        ('prevent_core',True),
        ('stdin',None),
        ('stdout',None),
        ('stderr',None),
      ):
      setattr(self,var,kw.get(var,dval))
      if var in kw:
        del kw[var]
    for var,val in kw.items():
      setattr(self,var,val)

    # This is a brand new DaemonContext instance, so it's not open yet.
    self.is_open=False

    # Convert any file streams in files_preserve to file handles.
    if self.files_preserve==None:
      self.files_preserve=[]
    else:
      self.files_preserve=list(self.files_preserve)
    for i in range(len(self.files_preserve)):
      if has_attr(self.files_preserve,'fileno'):
        self.files_preserve[i]=self.files_preserve[i].fileno()

    # Add any stdin, stdout, and stderr arguments' file handles to our
    # files_preserve list of file handles.
    for sname in ('stdin','stdout','stderr'):
      f=getattr(self,sname)
      if f!=None and hasattr(f,'fileno'):
        self.files_preserve.append(f.fileno())

    # Make sure our signal_map has valid handlers.
    if self.signal_map==None:
      # Set up our default signal map.
      self.signal_map={}
    elif isinstance(self.signal_map,dict):
      # Work with a copy so we don't modify the caller's signal_map value.
      self.signal_map=dict(self.signal_map)
    else:
      raise TypeError('Non-dictionary signal_map type: %s'%(type(self.signal_map),))
    # Provide default mapping entries where needed.
    default_sigmap=dict(
        SIGTTIN=None,
        SIGTTOU=None,
        SIGTSTP=None,
        SIGTERM='terminate'
      )
    for sig,handler in list(default_sigmap.items()):
      if not(sig in self.signal_map or getattr(signal,sig) in self.signal_map):
        self.signal_map[sig]=handler
    # Listify our signal_map so we can cook keys as well as values.
    sigmap=list(self.signal_map.items())
    for i in range(len(sigmap)):
      sig,handler=sigmap[i]
      # Convert sig to a number if it's a string.
      if isinstance(sig,str):
        orig_sig=sig
        sig=sit.upper()
        if not sig.startwith('SIG'):
          sig='SIG'+sig
        if not hasattr(signal,sig):
          raise ValueError("Bad signal name: %r"%(orig_sig,))
        sig=getattr(signal,sig)
      else:
        if sig not in signal_names:
          raise ValueError("Bad signal number: %r"%(sig,))
      # Find an actual handler function for our handler.
      if handler==None:
        handler=signal.SIG_IGN
      elif isinstance(handler,str):
        if hasattr(handler):
          handler=getattr(handler)
        else:
          raise ValueError('No such signal handler attribute: %r'%(hander,))
      # Store our new, cooked values in our list.
      sigmap[i]=sig,handler
    # Rebuild our signal_map dict from our new values.
    self.signal_map=dict(sigmap)

  def terminate(sig,stack):
    "This is called if we get SIGTERM (typically)."

    raise SystemExit('Terminating: %s'%signal_names[sig])

  def __enter__(self):
    self.open()
    return self # Return this DaemonContext instance.

  def __exit__(self,t,v,tb):
    self.close()
    return False # Let the calling code handle any exception.

  def open(self):
    "Go daemon."

    if self.is_open:
      return
    if self.prevent_core:
      pass # Needs improvement.
    if self.chroot_directory!=None:
      os.chroot(self.chroot_directory)
    os.setuid(self.uid)
    os.setgid(self.gid)

    # Close every open files unless it's in our list of protected file handles.
    open_fds=[int(x) for x in os.listdir('/proc/self/fd')]
    for handle in open_fds:
      if handle not in self.files_preserve:
        os.close(handle)

    os.chdir(self.working_directory)
    os.umask(self.umask)

    if self.detach_process:
      pid=os.fork()
      if pid>0:
        os._exit(0) # Terminate the parent process.
      pid=os.fork()
      os.setsid() # Start a new Unix session with no controlling terminal.
      if pid>0:
        os._exit(0) # Terminate our transitional parent process.
      # We now have a new Unix session ID and no terminat attached to this child.

    # Set up our signal handlers.
    for sig,handler in list(self.signal_map.items()):
      signal.signal(sig,handler)

    # Handle our stdin, stdout, and stderr arguments, directing them to
    # /dev/null or adding them to files_preserve as appropriate.

    # Bind the system.[stdin,stdout,stderr] streams to those provided by the
    # caller. Set any that were not specified to this system's null device.
    for sname in ('stdin','stdout','stderr'):
      f=getattr(self,sname)
      if f==None:
        # Point this stream at the null device for this system.
        setattr(sys,sname,open(os.devnull,(os.RDWR,os.RDONLY)[sname=='stdin']))
      else:
        os.dup2(f.fileno(),getattr(sys,sname).fileno())

    if self.pidfile!=None:
      self.pidfile.__enter__()
    self.is_open=True
    atexit.register(self.close)

  def close(self):
    "Politely close this DaemonContext (if it's open)."

    if not self.is_open:
      return
    if self.pidfile!=None:
      self.pidfile.__exit__(None,None,None)
    self.is_open=False


