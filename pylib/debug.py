#!/usr/bin/env python3

import inspect,os,sys
# Because I need "time" to be a local variable in DebugChannel.write() ...
from time import gmtime,localtime,sleep,strftime,time as get_time

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

      d=DebugChannel(
        True,
        stream=LogStream(facility='user'),
        label='D',
        line_fmt='{label}: {basename}({line}): {indent}{message}\\n'
      )
      d('Testing')

  The output in /var/log/user.log (which might be a different path on
  your system) might look like this:

      Aug 16 22:58:16 pi4 x[18478] D: x(12): Testing

  What I really like about this is that the source filename and line
  number are included in the log output. The "d('Testing')" call is on
  line 12.

  Run this module directly with

      python -m debug

  to see a demonstration of indenture. The example code for that demo
  is at the bottom of the debug.py source file."""

  def __init__(
      self,
      enabled=False,
      stream=sys.stderr,
      label='DEBUG',
      indent_with='  ',
      line_fmt='{label}: {basename}[{pid}]:{function}:{line}: {indent}{message}\n',
      date_fmt='%Y-%m-%d',
      time_fmt='%H:%M:%S',
      callback=None
    ):
    """Initialize the stream and on/off state of this new DebugChannel
    object. The "enabled" state defaults to False, and the stream
    defaults to sys.stderr (though any object with a write() method will
    do).

    Arguments:

      enabled      True if this DebugChannel object is allowed to output
                   messages.
      stream       The stream (or stream-like object) to write messages
                   to.
      label        A string indicated what we're doing.
      indent_with  The string used to indent each level of indenture.
      line_fmt     Formatting for our output lines. See setFormat().
      date_fmt     Date is formatted with strftime() using this string.
      time_fmt     Time is formatted with strftime() using this string.
      callback     A function accepting keyword arguments and returning
                   True if the current message is to be output. The
                   keyword arguments are all the local variables of
                   DebugChannel.write(). Of particular interest might be
                   "stack" and all the variables available for
                   formatting.

    DebugChannel.write() goes to some length to ensure that the filename
    and line number reported in its output is something helpful to the
    caller. For instance, the source line shouldn't be anything in this
    class.
    
    Since it's perfectly plausible for a DebugChannel object to be used
    from within another reporting class that should be similarly
    ignored, you can add to the ignore_modules attribute (a set), the
    name of any module you'd like DebugChannel's write() method to skip
    over as it searches downward through the stack. For example, the
    ignore_modules attribute is initialized with the full pathname of
    THIS copy of debug.py so that anything in this module will be
    skipped over, and the most recent line of the caller's code will be
    reported instead. Feel free to add the names of any other modules
    you'd like to ignore in the call stack."""

    assert hasattr(stream,'write'),"DebugChannel REQUIRES a stream object with a write() method."

    self.stream=stream
    self.enabled=enabled

    self.fmt=line_fmt
    self.indlev=0
    self.label=label
    self.indstr=indent_with
    self._t=0 # The last time we formatted the time.
    self.date=None # The last date we formatted.
    self.time=None # The last time we formatted.
    self.date_fmt=date_fmt
    self.time_fmt=time_fmt
    self.callback=callback
    # So we don't report anything in this module as the caller ...
    self.ignore_modules={}
    self.ignoreModule(str(inspect.stack()[0][1]))

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
          d(diagnostics)
    """

    return bool(self.enabled)

  def enable(self,state=True):
    """Allow this DebugChannel object to write messages if state is
    True. Return the previous state as a boolean."""

    prev_state=self.enabled
    self.enabled=bool(state)
    return prev_state

  def disable(self):
    """Inhibit output from this DebugChannel object, and return its
    previous "enabled" state."""

    return self.enable(False)

  def ignoreModule(self,name,*args):
    """Given the name of a module, e.g. "debug"), ignore any entries in
    our call stack from that module. Any subsequent arguments must be
    the name of a function to be ignored within that module. If no such
    functions are named, all calls from that module will be ignored."""

    if name in sys.modules:
      m=str(sys.modules[name])
      name=m[m.find(" from '")+7:m.rfind(".py")+3]
    if name not in self.ignore_modules:
      self.ignore_modules[name]=set([])
    self.ignore_modules[name].update(args)

  def setDateFormat(self,fmt):
    """Use the formatting rules of strftime() to format the "date"
    value to be output in debug messages. Return the previous date
    format string."""

    s=self.date_fmt
    self.date_fmt=fmt
    return s

  def setTimeFormat(self,fmt):
    """Use the formatting rules of strftime() to format the "time"
    value to be output in debug messages. Return the previous time
    format string."""

    s=self.time_fmt
    self.time_fmt=fmt
    return s

  def setIndentString(self,s):
    "Set the string to indent with. Return this DebugChannel object."

    self.indstr=s
    return self

  def setFormat(self,fmt):
    """Set the format of our debug statements. The format defaults to:

      '{date} {time} {label}: {basename}:{function}:{line}: {indent}{message}\\n'

    Fields:
      {date}     current date (see setDateFormat())
      {time}     current time (see setTimeFormat())
      {label}    what type of thing is getting logged (default: 'DEBUG')
      {pid}      numeric ID of the current process
      {pathname} full path of the calling source file
      {basename} base name of the calling source file
      {function} name of function debug.write() was called from
      {line}     number of the calling line of code in its source file
      {code}     the Python code at the given line of the given file
      {indent}   indention string multiplied by the indention level
      {message}  the message to be written

    All non-field text is literal text. The '\\n' at the end is required
    if you want a line ending at the end of each message. If your
    DebugChannel object is configured to write to a LogStream object
    that writes to syslog or something similar, you might want to remove
    the {date} and {time} (and maybe {label}) fields from the default
    format string to avoid logging these values redundantly."""

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
      pid=os.getpid()
      # Update our formatted date and time if necessary.
      t=int(get_time()) # Let's truncate at whole seconds.
      if self._t!=t:
        t=localtime(t)
        self._t=t
        self.date=strftime(self.date_fmt,t)
        self.time=strftime(self.time_fmt,t)
      # Set local variables for date and time so they're available for output.
      date=self.date
      time=self.time
      # Figure out where the caller called us from.
      pathname,basename,line=None,None,None
      stack=inspect.stack()
      max_frame=len(stack)-1
      i=0
      while i<max_frame:
        frame=stack[i]
        #print 'frame=%r'%(frame[1:4],)
        #print 'type=%s'%(type(frame[1]),)
        #print 'type=%s'%(type(self.ignore_modules.keys()[0]))
        #print '%r in %r = %r'%(frame[1],self.ignore_modules.keys(),frame[1] not in self.ignore_modules.keys())
        if frame[1] not in self.ignore_modules:
          # We're not ignoring ANY functions in this module.
          #print 'Not an ignored module.'
          break
          if frame[3] not in self.ignore_modules[frame[1]]:
            # This is not one of the ignored functions in this module.
            #print 'Not an ignored function.'
            break
        i+=1
      pathname,line,function,code,index=stack[i][1:6]
      code=code[index].rstrip()
      if str(function)=='<module>':
        function='__main__'
      basename=os.path.basename(pathname)
      indent=self.indstr*self.indlev
      label=self.label

      # If our caller provided a callback function, call that now.
      if self.callback:
        if not self.callback(**locals()):
          return self # Return without writing any output.

      # Format our message and write it to the debug stream.
      if isinstance(message,(list,tuple)):
        messages=message
        for message in messages:
          self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,dict):
        messages=message
        for k in messages.keys():
          message=f"{k}: {messages[k]}"
          self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,str) and os.linesep in message:
        messages=message
        for message in line_iter(messages):
          self.stream.write(self.fmt.format(**locals()))
      else:
        self.stream.write(self.fmt.format(**locals()))
      self.stream.flush()

    # Let the caller call other methods by using our return value.
    return self

if __name__=='__main__':
  from pprint import pprint

  def testing():
    """Make lots of calls to our DebugChannel object to put it
    through its paces."""

    d('BASIC OUTPUT ...').indent()
    d('Message 1')
    d('Message 2')
    d.undent()
    d('INDENTED OUTPUT ...').indent().setIndentString('| ')
    d('indlev=%r'%(d.indlev,)).indent(1)
    d('indlev=%r'%(d.indlev,)).indent(1)
    d('indlev=%r'%(d.indlev,)).indent(1)
    d('indlev=%r'%(d.indlev,))
    d('same level')
    d.indent(-1)('indlev=%r'%(d.indlev,))
    d.indent(-1)('indlev=%r'%(d.indlev,))
    d.indent(-1)('indlev=%r'%(d.indlev,))
    d.indent(-1).write('indlev=%r'%(d.indlev,))
    d.indent(-1).write('indlev=%r'%(d.indlev,)).setIndentString('  ')
    d.indent() # Restore indenture to where it ought to be.
    d('DISABLING OUTPUT ...').indent()
    prev=d.enable(False)
    d("Disabled debug output (so you shouldn't see this).")
    d('Previous DebugChannel enabled state: %r'%(prev,))
    prev=d.enable(prev)
    d.undent()('RE-ENABLED OUTPUT ...').indent()
    d('Previous DebugChannel enabled state: %r'%(prev,))
    d.undent()('MULTILINE OUTPUT ...\n').indent()
    d('MULTILINE\nOUTPUT\n...\n')
    d.undent()('LIST OUTPUT ...').indent()
    d('LIST OUTPUT ...'.split())
    d.undent()('TUPLE OUTPUT ...').indent()
    d(tuple('TUPLE OUTPUT ...'.split()))
    d.undent()('DICTIONARY OUTPUT ...').indent()
    d(dict(a='dictionary',c='output',b='...'))
    d.undent()('DONE!')

  def delay(**kwargs):
    """Keep debug output from flying by too fast to do any good. This
    is just a simple example of what might be done with a callback
    function."""

    sleep(.1)
    return True

  assert '__loader__' in globals(),"To run this module stand-along, use 'python -m debug'."
  # Create our DebugChannel object that is switched on.
  d=DebugChannel(True,stream=sys.stdout,callback=delay)
  # Since this test is running from the debug module itself, we need to ignore a couple of functions.
  #d.ignoreModule(inspect.stack()[0][1],'write','__call__')
  #d.ignoreModule('/usr/local/Cellar/python@2/2.7.17/Frameworks/Python.framework/Versions/2.7/lib/python2.7/runpy.py')
  # Now run our test.
  d("About to call testing() ...").indent()
  testing()
  d.undent()("Returned from testing()")
