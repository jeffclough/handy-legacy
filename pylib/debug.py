import inspect,os,sys

class DebugChannel(object):
  """Objects of this class are really useful for debugging, and this is
  even more powerful when combined with loggy.LogStream to write all
  debug output to some appropriate syslog facility. Here's an example,
  put into an executable script called x:

      #!/usr/bin/env python

      from debug import DebugChannel
      from loggy import LogStream

      d=DebugChannel(True,LogStream(facility='user'))
      d.setFormat('{filename}({line}): {indent}{message}')
      d('Testing')

  The output in /var/log/user.log might look like this

      Aug 16 22:58:16 pi4 x[18478] D: /home/jclough/my/bin/x(8): Testing

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

    self.fmt='{label}: {filename}({line}): {indent}{message}\n'
    self.indlev=0
    self.label=label
    self.indstr='  '
    self.ignore_modules=set(['loggy.py'])

  @staticmethod
  def filenamer(filename):
    return filename

  def __bool__(self):
    "Return the Enabled state of this DebugChannel object."

    return self.enabled

  def enable(self,state=True):
    """Allow this DebugChannel object to write messages if state is
    True. Return the previous state as a boolean."""

    prev_state=self.enabled
    self.enabled=bool(state)
    return prev_state

  def setFormat(self,fmt):
    """Set the format of our debug statements. The format defaults to:

        '{label}: {filename}({line}): {indent}{message}\\n'

    Fields:
      {label}    printed before the colon (default: 'DEBUG')
      {filename} name of the calling source file
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

        debug=DebugChannel(Boolean(True))
        debug('Testing')

        def func(arg):
          debug.write("Entering func(arg=%r)"%(arg,)).indent(1)
          for i in range(3):
            debug("i=%r"%(i,))
          debug.indent(-1).write("Leaving func()")

    This lets the caller decide whether to change indenture before or
    after the message is written."""

    if self.enabled:
      filename,line=None,None
      stack=inspect.stack()
      max_frame=len(stack)-1
      #sys.stderr.write("stack length=%d\n"%(max_frame+1,))
      #sys.stderr.write("%s\n"%('\n'.join(["  %d: %r"%(i,stack[i]) for i in range(max_frame+1)])))
      if len(stack)>=2:
        if stack[0][1]==stack[1][1] and stack[1][3]=='__call__':
          # write() was called from our own __call__ method.
          i=2
        else:
          i=1
        if self.ignore_modules:
          while i<max_frame and stack[i] in self.ignore_modules:
            i+=1
        filename=self.filenamer(stack[i][1])
        line=stack[i][2]
      indent=self.indstr*self.indlev
      label=self.label
      self.stream.write(self.fmt.format(**locals()))
    return self

  def __call__(self,message):
    "Just a wrapper for the write() method."

    self.write(message)
    return self

class DebugChannelBasename(DebugChannel):
  def __init__(self,enabled=False,stream=sys.stderr,label='DEBUG'):
    super(self.__class__,self).__init__(enabled,stream,label)

  @staticmethod
  def filenamer(filename):
    return os.path.basename(filename)

if __name__=='__main__':
  # Create our DebugChannel object that is switched on.
  d=DebugChannel(True)
  d('Message 1')
  d('Message 2')
  d('indlev=%r'%(d.indlev,)).indent(1)
  d('indlev=%r'%(d.indlev,)).indent(1).indstr='| '
  d('indlev=%r'%(d.indlev,)).indent(1)
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1)('indlev=%r'%(d.indlev,))
  d.indent(-1).write('indlev=%r'%(d.indlev,))
  d.indent(-1).write('indlev=%r'%(d.indlev,))
  prev=d.enable(False)
  d("Disabled debug output (so you shouldn't see this).")
  print 'Previous DebugChannel enabled state: %r'%(prev,)
