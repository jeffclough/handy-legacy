import sys

class DebugChannel(object):
  def __init__(self,enabled=False,stream=sys.stderr):
    """Initialize the stream and on/off state of this new DebugChannel
    object. The "enabled" state defaults to False, and the stream
    defaults to sys.stderr (though any object with a write() method will
    do)."""

    assert hasattr(stream,'write'),"DebugChannel REQUIRES a stream object with a write() method."

    self.stream=stream
    self.enabled=enabled

    self.fmt='DEBUG: {indent}{message}\n'
    self.ind=0
    self.indstr='  '

  def enable(self,state=True):
    """Allow this DebugChannel object to write messages if state is
    True. Return the previous state as a boolean."""

    prev_state=self.enabled
    self.enabled=bool(state)
    return prev_state

  def setFormat(self,fmt):
    """Set the format of our debug statements. The format defaults to:

        'DEBUG: {indent}{message}\n'

    Fields:
      {indent}   indention string multiplied by the indention level
      {message}  the message to be written

    All non-field text is literal text. The '\n' at the end is required
    if you want a line ending at the end of each message.
    """

    self.fmt=fmt

  def indent(self,indent):
    """Increase this object's current indenture by this value (which
    might be negative. Return the new indenture value."""

    self.ind+=indent
    if self.ind<0:
      self.ind=0
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
      indent=self.indstr*self.ind
      self.stream.write(self.fmt.format(**locals()))
    return self

  def __call__(self,message):
    "Just a wrapper for the write() method."

    return self.write(message)

if __name__=='__main__':
  # Create our DebugChannel object that is switched on.
  d=DebugChannel(True)
  d('Message 1')
  d('Message 2')
  d('ind=%r'%(d.ind,)).indent(1)
  d('ind=%r'%(d.ind,)).indent(1).indstr='..'
  d('ind=%r'%(d.ind,)).indent(1)
  d.indent(-1)('ind=%r'%(d.ind,))
  d.indent(-1)('ind=%r'%(d.ind,))
  d.indent(-1)('ind=%r'%(d.ind,))
  d.indent(-1)('ind=%r'%(d.ind,))
  d.indent(-1)('ind=%r'%(d.ind,))
  prev=d.enable(False)
  d("Disabled debug output (so you shouldn't see this).")
  print 'Previous DebugChannel enabled state: %r'%(prev,)
