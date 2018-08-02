import sys

class Boolean(object):
  """Boolean is a very simple wrapper for a single boolean value, which
  might seem a little silly, but objects of this type are passed by
  reference because they're objects, as opposed to Python primitive
  types (like bool). The DebugChannel class makes use of this."""

  def __init__(self,state=False):
    """Initialize the state to the boolean value of the state argument,
    which defaults to False."""

    self.state=self(state)

  def __bool__(self):
    "Return the boolean value of this object's state."

    return bool(self.state)

  def __call__(self,*args):
    """If at least one argument is given, set our state to the boolean
    version of that value. Regardless, return the (possibly new) state
    of this Boolean object."""

    if len(args):
      self.state=bool(args[0])
    return self.state

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DebugChannel(object):
  def __init__(self,state_var,stream=sys.stderr):
    """Initialize the stream and on/off state of this new DebugChannel
    object. The stream defaults to sys.stderr (though any object with a
    write() method will do), and state defaults to False (off)."""

    assert hasattr(stream,'write'),"DebugChannel REQUIRES a stream object with a write() method."
    assert isinstance(state_var,Boolean),"DebugChannel REQUIRES a state of type 'Boolean'."

    self.stream=stream
    self.state=state_var

    self.fmt='DEBUG: {indent}{message}\n'
    self.ind=0
    self.indstr='  '

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

        debug=DebugChannel()
        debug('Testing')

        def func(arg):
          debug.write("Entering func(arg=%r)"%(arg,)).indent(1)
          for i in range(3):
            debug("i=%r"%(i,))
          debug.indent(-1).write("Leaving func()")

    This lets you decide whether to change indenture before or after the
    message is written."""

    if self.state():
      indent=self.indstr*self.ind
      self.stream.write(self.fmt.format(**locals()))
    return self

  def __call__(self,message):
    "Just a wrapper for the write() method."

    return self.write(message)

if __name__=='__main__':
  debugging=Boolean(True)
  print 'debugging=%r'%(debugging(),)

  d=DebugChannel(debugging)
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
  debugging(False)
  d('Message 11')
  d('Message 12')

  print 'debugging=%r'%(debugging(),)
