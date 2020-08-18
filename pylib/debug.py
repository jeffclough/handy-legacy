import inspect,os,sys

def line_iter(s):
  """This iterator facilitates stepping through each line of a multi-
  line string in place, without having to create a list containing those
  lines."""

  i=0
  n=len(s)
  while i<n:
    j=s.find(os.linesep,i)
    if j<0:
      yield s[i:] # Yield the rest of this string.
      j=n
    else:
      yield s[i:j] # Yield the next line in this string.
      j+=1
    i=j

class DebugChannel(object):
  """Objects of this class are really useful for debugging, and this is
  even more powerful when combined with loggy.LogStream to write all
  debug output to some appropriate syslog facility. Here's an example,
  put into an executable script called x:

      #!/usr/bin/env python

      from debug import DebugChannel
      from loggy import LogStream

      d=DebugChannel(True,LogStream(facility='user'))
      d('Testing')

  The output in /var/log/user.log might look like this:

      Aug 16 22:58:16 pi4 x[18478] D: x(8): Testing

  What I really like about this is that the source filename and line
  number are included in the log output. The "d('Testing')" call is on
  line 8."""

  def __init__(self,enabled=False,stream=sys.stderr,label='DEBUG'):
    """Initialize the stream and on/off state of this new DebugChannel
    object. The "enabled" state defaults to False, and the stream
    defaults to sys.stderr (though any object with a write() method will
    do).

    DebugChannel.write() goes to some length to ensure that the filename
    and line number reported in its output is something helpful to the
    caller. For instance, the source line shouldn't be anything in this
    class.
    
    Since it's perfectly plausible for a DebugChannel object to be used
    from within another reporting class that should be similarly
    ignored, you can add to the ignore_modules attribute (a set), the
    name of any module you'd like DebugChannel's write() method to skip
    over as it searches downward through the stack. For example, the
    ignore_modules attribute is initialized with 'loggy.py' so that
    anything in that module will be skipped over, and whatever called
    loggy's code will be reported instead. Feel free to add the names of
    any other modules you'd like to ignore in the call stack."""

    assert hasattr(stream,'write'),"DebugChannel REQUIRES a stream object with a write() method."

    self.stream=stream
    self.enabled=enabled

    self.fmt='{label}: {basename}({line}): {indent}{message}\n'
    self.indlev=0
    self.label=label
    self.indstr='  '
    # So we don't report anything in this module as the caller ...
    self.ignore_modules=set([__loader__.filename])

  def __bool__(self):
    """Return the Enabled state of this DebugChannel object. It is
    somtimes necessary to logically test whether our code is in debug
    mode at runtime, and this method makes that very simple.

        d=DebugChannel(opt.debug)
        .
        .
        .
        if d:
          d("Getting diagnostics ...")
          diagnostics=some_expensive_data()
          d.writelines(diagnostics)
    """

    return bool(self.enabled)

  def enable(self,state=True):
    """Allow this DebugChannel object to write messages if state is
    True. Return the previous state as a boolean."""

    prev_state=self.enabled
    self.enabled=bool(state)
    return prev_state

  def setFormat(self,fmt):
    """Set the format of our debug statements. The format defaults to:

        '{label}: {basename}({line}): {indent}{message}\\n'

    Fields:
      {label}    printed before the colon (default: 'DEBUG')
      {pathname} full path of the calling source file
      {basename} base name of the calling source file
      {line}     number of the calling line of code in its source file
      {indent}   indention string multiplied by the indention level
      {message}  the message to be written

    All non-field text is literal text. The '\\n' at the end is required
    if you want a line ending at the end of each message."""

    self.fmt=fmt

  def indent(self,indent=1):
    """Increase this object's current indenture by this value (which
    might be negative. Return this DebugChannel opject with the adjusted
    indenture. See write() for how this might be used."""

    self.indlev+=indent
    if self.indlev<0:
      self.indlev=0
    return self

  def undent(self,indent=1):
    """Decrease this object's current indenture by this value (which
    might be negative. Return this DebugChannel object with the adjusted
    indenture. See write() for how this might be used."""

    self.indlev-=indent
    if self.indlev<0:
      self.indlev=0
    return self

  def write(self,message):
    """If our debug state is on (True), write the given message using the
    our current format. In any case, return this DebugChannel instance
    so that, for example, things like this will work:

        debug=DebugChannel(opt.debug)
        debug('Testing')

        def func(arg):
          debug.write("Entering func(arg=%r)"%(arg,)).indent(1)
          for i in range(3):
            debug("i=%r"%(i,))
          debug.indent(-1).write("Leaving func()")

    This lets the caller decide whether to change indenture before or
    after the message is written.
    
    If message is a single string containing no line endings, that
    single value will be outout.

    if message contains at least one newline (the value of os.linesep),
    each line is output on a debug line of its own.
    
    If message is a list or tuple, each item in that sequence will be
    output on its own line.
    
    If message is a dictionary, each key/value pair is written out as
    
        key: value
        
    to its own log line. The keys are sorted in ascending order."""

    if self.enabled:
      # Figure out where the caller called us from.
      pathname,basename,line=None,None,None
      stack=inspect.stack()
      max_frame=len(stack)-1
      i=0
      while i<max_frame and stack[i][1] in self.ignore_modules:
        i+=1
      pathname,line=stack[i][1:3]
      basename=os.path.basename(pathname)
      indent=self.indstr*self.indlev
      label=self.label

      # Format our message and write it to the debug stream.
      if isinstance(message,(list,tuple)):
        messages=message
        for message in messages:
          self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,dict):
        messages=message
        for k in sorted(messages.keys()):
          message='%s: %s'%(k,messages[k])
          self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,basestring) and os.linesep in message:
        messages=message
        for message in line_iter(messages):
          self.stream.write(self.fmt.format(**locals()))
      else:
        self.stream.write(self.fmt.format(**locals()))

    # Let the caller call other methods by using our return value.
    return self

  def writelines(self,seq):
    """Just a wrapper around write(), since that method handles
    sequences (and other things) just fine. writelines() is only
    provided for compatibility with code that expects it to be
    supported."""

    return self.write(seq)

  def __call__(self,message):
    """Just a wrapper for the write() method. Message can be a single-
    line string, multi-line string, list, tuple, or dict. See write()
    for details."""

    return self.write(message)

if __name__=='__main__':
  assert '__loader__' in globals(),"To run this module stand-along, use 'python -m debug'."
  # Create our DebugChannel object that is switched on.
  d=DebugChannel(True)
  d('BASIC OUTPUT ...').indent()
  d('Message 1')
  d('Message 2')
  d.undent()('INDENTED OUTPUT ...').indent().indstr='| '
  d('indlev=%r'%(d.indlev,)).indent(1)
  d('indlev=%r'%(d.indlev,)).indent(1)
  d('indlev=%r'%(d.indlev,)).indent(1)
  d('indlev=%r'%(d.indlev,))
  d('same level')
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1).write('indlev=%r'%(d.indlev,))
  d.indent(-1).write('indlev=%r'%(d.indlev,)).indstr='  '
  d.undent()('DISABLING OUTPUT ...').indent()
  prev=d.enable(False)
  d("Disabled debug output (so you shouldn't see this).")
  d.enable(prev)
  d.undent()('RE-ENABLING OUTPUT ...').indent()
  d('Previous DebugChannel enabled state: %r'%(prev,))
  d.undent()('MULTILINE OUTPUT ...\n').indent()
  d('MULTILINE\nOUTPUT\n...\n')
  d.undent()('LIST OUTPUT ...').indent()
  d('LIST OUTPUT ...'.split())
  d.undent()('TUPLE OUTPUT ...').indent()
  d(tuple('TUPLE OUTPUT ...'.split()))
  d.undent()('DICTIONARY OUTPUT ...').indent()
  d(dict(a='dictionary',c='...',b='output'))
  d('DONE!')
