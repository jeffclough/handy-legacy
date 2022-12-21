#!/usr/bin/env python3

"""
This debug module exports a single class named DebugChannel, instances
of which are useful for adding temporary or conditional debug output to
CLI scripts.

The minimal boilerplate is pretty simple:

    from debug import *
    dc=DebugChannel(True)

By default, output is sent to stdandard error formatted according to:

    '{label}: [{pid}] {basename}:{line}:{function}: {indent}{message}\\n'

There are several variables you can include in DebugChannel's output:

    date     - Current date in "%Y-%m-%d" format by default.
    time     - Current time in "%H:%M:%S" format by default.
    label    - Set in the initializer, defaults to "DC".
    pid      - The current numeric process ID.
    pathname - The full path to the source file.
    basename - The filename of the source file.
    function - The name of the function whence dc(...) was called. This
               will be "__main__" if called from outside any function.
    line     - The linenumber whence dc(...) was called.
    code     - The text of the line of code that called dc().
    indent   - The string (typically spaces) used to indent the message.
    message  - The message to be output.

So, for example, if you want to see how your variables are behaving in a
loop, you might do something like this:

    from debug import *

    dc=DebugChannel(
      True,
      fmt="{label}: {line:3}: {indent}{message}\\n"
    )

    dc("Entering loop ...").indent()
    for i in range(5):
      dc(f"i={i}").indent()
      for j in range(3):
        dc(f"j={j}")
      dc.undent()("Done with j loop.")
    dc.undent()("Done with i loop.")

That gives you this necely indented output. The indent() and undent()
methods are one thing that makes DebugChannels so nice to work with.

    DC:   8: Entering loop ...
    DC:  10:   i=0
    DC:  12:     j=0
    DC:  12:     j=1
    DC:  12:     j=2
    DC:  13:   Done with j loop.
    DC:  10:   i=1
    DC:  12:     j=0
    DC:  12:     j=1
    DC:  12:     j=2
    DC:  13:   Done with j loop.
    DC:  10:   i=2
    DC:  12:     j=0
    DC:  12:     j=1
    DC:  12:     j=2
    DC:  13:   Done with j loop.
    DC:  10:   i=3
    DC:  12:     j=0
    DC:  12:     j=1
    DC:  12:     j=2
    DC:  13:   Done with j loop.
    DC:  10:   i=4
    DC:  12:     j=0
    DC:  12:     j=1
    DC:  12:     j=2
    DC:  13:   Done with j loop.
    DC:  14: Done with i loop.

That's a simple example, but you might be starting to gret an idea of
how versatile DeviceContexts can be.

A DebugChannel instance can also be used as a function decorator:

    import time
    from debug import *

    def delay(**kwargs):
      time.sleep(1)
      return True

    dc=DebugChannel(True,callback=delay)
    dc.setFormat("{label}: {function}: {indent}{message}\\n")

    @dc
    def example1(msg):
      print(msg)

    @dc
    def example2(msg,count):
      for i in range(count):
        example1(f"{i+1}: {msg}")

    example2("First test",3)
    example2("Second test",2)

This causes entry into and exit from the decorated function to be
announced in the given DeviceChannel's output. If you put that into a
file named foo.py and then run "python3 -m foo", you'll get this:

    DC: __main__: Calling example2('First test',3) ...
    DC: example2:   Calling example1('1: First test') ...
    1: First test
    DC: example2:   Function example1 returns None after 0.000069 seconds.
    DC: example2:   Calling example1('2: First test') ...
    2: First test
    DC: example2:   Function example1 returns None after 0.000026 seconds.
    DC: example2:   Calling example1('3: First test') ...
    3: First test
    DC: example2:   Function example1 returns None after 0.000038 seconds.
    DC: __main__: Function example2 returns None after 6.036933 seconds.
    DC: __main__: Calling example2('Second test',2) ...
    DC: example2:   Calling example1('1: Second test') ...
    1: Second test
    DC: example2:   Function example1 returns None after 0.000039 seconds.
    DC: example2:   Calling example1('2: Second test') ...
    2: Second test
    DC: example2:   Function example1 returns None after 0.000023 seconds.
    DC: __main__: Function example2 returns None after 4.019719 seconds.

That's a very general start. See DebugChannel's docs for more.
"""

__all__=[
  'DebugChannel',
  'gmtime',
  'localtime',
]
__version__='0.1.0'

import inspect,os,sys,traceback
# Because I need "time" to be a local variable in DebugChannel.write() ...
from time import gmtime,localtime,strftime,time as get_time

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
        fmt='{label}: {basename}({line}): {indent}{message}\\n'
      )
      d('Testing')

  The output in /var/log/user.log (which might be a different path on
  your system) might look like this:

      Aug 16 22:58:16 pi4 x[18478] D: x(12): Testing

  What I really like about this is that the source filename and line
  number are included in the log output. The "d('Testing')" call is on
  line 12.

  Run this module directly with

      python3 -m debug

  to see a demonstration of indenture. The example code for that demo
  is at the bottom of the debug.py source file.

  IGNORING MODULES:
    DebugChannel.write() goes to some length to ensure the filename and
    line number reported in its output are something helpful to the
    caller. For instance, the source line shouldn't be anything in this
    DebugChannel class. 

    Use the ignoreModule() method to tell the DebugChannel object ignore
    other modules, and optionally, specific functions within that
    module."""

  def __init__(
      self,
      enabled=False,
      stream=sys.stderr,
      label='DC',
      indent_with='    ',
      fmt='{label}: {basename}:{line}:{function}: {indent}{message}\n',
      date_fmt='%Y-%m-%d',
      time_fmt='%H:%M:%S',
      time_tupler=localtime,
      callback=None
    ):
    """Initialize the stream and on/off state of this new DebugChannel
    object. The "enabled" state defaults to False, and the stream
    defaults to sys.stderr (though any object with a write() method will
    do).

    Arguments:

      enabled      True if this DebugChannel object is allowed to output
                   messages. False if it should be quiet.
      stream       The stream (or stream-like object) to write messages
                   to.
      label        A string indicated what we're doing.
      indent_with  The string used to indent each level of indenture.
      fmt          Formatting for our output lines. See setFormat().
      date_fmt     Date is formatted with strftime() using this string.
      time_fmt     Time is formatted with strftime() using this string.
      time_tupler  This is either localtime or gmtime and defaults to
                   localtime.
      callback     A function accepting keyword arguments and returning
                   True if the current message is to be output. The
                   keyword arguments are all the local variables of
                   DebugChannel.write(). Of particular interest might be
                   "stack" and all the variables available for
                   formatting: label, basename, pid, function, line,
                   indent, and message.

    """

    assert hasattr(stream,'write'),"DebugChannel REQUIRES a stream object with a write() method."

    self.stream=stream
    self.enabled=enabled
    self.pid=os.getpid()
    self.fmt=fmt
    self.indlev=0
    self.label=label
    self.indstr=indent_with
    self._t=0 # The last time we formatted the time.
    self.date=None # The last date we formatted.
    self.time=None # The last time we formatted.
    self.date_fmt=date_fmt
    self.time_fmt=time_fmt
    self.time_tupler=time_tupler
    self.callback=callback
    # So we don't report anything in this module as the caller ...
    self.ignore={}
    #self.ignoreModule(str(inspect.stack()[0][1]))
    self.ignoreModule(os.path.normpath(inspect.stack()[0].filename))

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
          diagnostics=get_some_computationally_expensive_data()
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
    the names of functions to be ignored within that module. If no such
    functions are named, all calls from that module will be ignored."""

    if name in sys.modules:
      m=str(sys.modules[name])
      name=m[m.find(" from '")+7:m.rfind(".py")+3]
    if name not in self.ignore:
      self.ignore[name]=set([])
    self.ignore[name].update(args)

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
      {label}    what type of thing is getting logged (default: 'DC')
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

    return self.indent(-indent)

  def writelines(self,seq):
    """Just a wrapper around write(), since that method handles
    sequences (and other things) just fine. writelines() is only
    provided for compatibility with code that expects it to be
    supported."""

    return self.write(seq)

  def __call__(self,arg,*args,**kwargs):
    """Just a wrapper for the write() method. The message in the arg
    argument can be a single- line string, multi-line string, list,
    tuple, or dict. See write() for details.
    """

    lines=inspect.stack(context=2)[1].code_context
    if lines and any(l.lstrip().startswith('@') for l in lines):
      # We're being called as a decorator.
      def f(*args,**kwargs):
        # Record how this function is being called.
        sig=','.join([repr(a) for a in args]+[f"{k}={v!r}" for k,v in kwargs.items()])
        self.write(f"{arg.__name__}({sig}) ...").indent()
        t0=get_time()
        # Call the function we're wrapping
        ret=arg(*args,**kwargs)
        # Record this function's return.
        t1=get_time()
        sig='...' if sig else ''
        dt=t1-t0
        d,dt=divmod(dt,86400) # Days
        if d:
          d=f"{int(d)}d"
        else:
          d=''
        h,dt=divmod(dt,3600) # Hours
        if h:
          h=f"{int(h)}h"
        else:
          h='0h' if d else ''
        m,dt=divmod(dt,60) # Minutes
        if m:
          m=f"{int(m)}m"
        else:
          m='0m' if h else ''
        if m: # Seconds
          s=f"{int(dt)}s"
        else:
          if dt>=1: # Fractional seconds
            s=f"{dt:0.3f}"
            s=s[:4].rstrip('0')+'s'
          elif dt>=0.001: # Milliseconds
            s=f"{int(dt*1000)}ms"
          else: # Microseconds
            s=f"{int(dt*1e6)}µs"
        self.undent().write(f"{arg.__name__}({sig}) returns {ret!r} after {d}{h}{m}{s}.")
        return ret
      return f

    # We were called as a regulear method.
    return self.write(arg)

  def writeTraceback(self,exc):
    """Write the given exception with traceback information to our
    output stream."""

    if self.enabled:
      for line in traceback.format_exception(exc):
        self.write(line.rstrip())

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
      # Update our formatted date and time if necessary.
      t=int(get_time()) # Let's truncate at whole seconds.
      if self._t!=t:
        t=self.time_tupler(t)
        self._t=t
        self.date=strftime(self.date_fmt,t)
        self.time=strftime(self.time_fmt,t)
      # Set local variables for date and time so they're available for output.
      date=self.date
      time=self.time
      # Find the first non-ignored stack frame whence we were called.
      pathname,basename,line=None,None,None
      for frame in inspect.stack():
        p=os.path.normpath(frame.filename)
        if p not in self.ignore:
          break
          if frame.function not in self.ignore[p]:
            break
      # Set some local variables so they'll be available to our callback
      # function and for formatting.
      pid=self.pid
      pathname=os.path.normpath(frame.filename)
      basename=os.path.basename(pathname)
      line=frame.lineno
      function=frame.function
      if str(function)=='<module>':
        function='__main__'
      #code=frame.code_context[frame.index].rstrip()
      code=frame.code_context
      if code:
        code=code[frame.index].rstrip()
      else:
        code=None
      indent=self.indstr*self.indlev
      label=self.label

      # If our caller provided a callback function, call that now.
      if self.callback:
        if not self.callback(**locals()):
          return self # Return without writing any output.

      # Format our message and write it to the debug stream.
      if isinstance(message,(list,tuple)):
        if isinstance(message,tuple):
          left,right='()'
        else:
          left,right='[]'
        messages=message
        message=left;self.stream.write(self.fmt.format(**locals()))
        for message in messages:
          message=self.indstr+message
          self.stream.write(self.fmt.format(**locals()))
        message=right;self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,dict):
        messages=dict(message)
        message='{';self.stream.write(self.fmt.format(**locals()))
        for k in messages.keys():
          message=f"{self.indstr}{k}: {messages[k]}"
          self.stream.write(self.fmt.format(**locals()))
        message='}';self.stream.write(self.fmt.format(**locals()))
      elif isinstance(message,str) and os.linesep in message:
        messages=message
        for message in line_iter(messages):
          self.stream.write(self.fmt.format(**locals()))
      else:
        self.stream.write(self.fmt.format(**locals()))
      self.stream.flush()

    # Let the caller call other methods by using our return value.
    return self

