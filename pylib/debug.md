# Table of Contents

* [debug](#debug)
  * [line\_iter](#debug.line_iter)
  * [DebugChannel](#debug.DebugChannel)
    * [\_\_init\_\_](#debug.DebugChannel.__init__)
    * [\_\_bool\_\_](#debug.DebugChannel.__bool__)
    * [enable](#debug.DebugChannel.enable)
    * [ignoreModule](#debug.DebugChannel.ignoreModule)
    * [setDateFormat](#debug.DebugChannel.setDateFormat)
    * [setTimeFormat](#debug.DebugChannel.setTimeFormat)
    * [setIndentString](#debug.DebugChannel.setIndentString)
    * [setFormat](#debug.DebugChannel.setFormat)
    * [indent](#debug.DebugChannel.indent)
    * [undent](#debug.DebugChannel.undent)
    * [writelines](#debug.DebugChannel.writelines)
    * [\_\_call\_\_](#debug.DebugChannel.__call__)
    * [write](#debug.DebugChannel.write)

<a name="debug"></a>
# debug

<a name="debug.line_iter"></a>
#### line\_iter

```python
line_iter(s)
```

This iterator facilitates stepping through each line of a multi-
line string in place, without having to create a list containing those
lines.

<a name="debug.DebugChannel"></a>
## DebugChannel Objects

```python
class DebugChannel(object)
```

Objects of this class are really useful for debugging, and this is
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
is at the bottom of the debug.py source file.

<a name="debug.DebugChannel.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(enabled=False, stream=sys.stderr, label='DEBUG', indent_with='  ', line_fmt='{date} {time} {label}: {basename}:{function}:{line}: {indent}{message}\n', date_fmt='%Y-%m-%d', time_fmt='%H:%M:%S', callback=None)
```

Initialize the stream and on/off state of this new DebugChannel
object. The "enabled" state defaults to False, and the stream
defaults to sys.stderr (though any object with a write() method will
do).

**Arguments**:


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
  you'd like to ignore in the call stack.

<a name="debug.DebugChannel.__bool__"></a>
#### \_\_bool\_\_

```python
 | __bool__()
```

Return the Enabled state of this DebugChannel object. It is
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

<a name="debug.DebugChannel.enable"></a>
#### enable

```python
 | enable(state=True)
```

Allow this DebugChannel object to write messages if state is
True. Return the previous state as a boolean.

<a name="debug.DebugChannel.ignoreModule"></a>
#### ignoreModule

```python
 | ignoreModule(name, *args)
```

Given the name of a module, e.g. "debug"), ignore any entries in
our call stack from that module. Any subsequent arguments must be
the name of a function to be ignored withing that module. If no such
functions are named, all calls from that module will be ignored.

<a name="debug.DebugChannel.setDateFormat"></a>
#### setDateFormat

```python
 | setDateFormat(fmt)
```

Use the formatting rules of strftime() to format the "date"
value to be output in debug messages. Return the previous date
format string.

<a name="debug.DebugChannel.setTimeFormat"></a>
#### setTimeFormat

```python
 | setTimeFormat(fmt)
```

Use the formatting rules of strftime() to format the "time"
value to be output in debug messages. Return the previous time
format string.

<a name="debug.DebugChannel.setIndentString"></a>
#### setIndentString

```python
 | setIndentString(s)
```

Set the string to indent with. Return this DebugChannel object.

<a name="debug.DebugChannel.setFormat"></a>
#### setFormat

```python
 | setFormat(fmt)
```

Set the format of our debug statements. The format defaults to:

  '{date} {time} {label}: {basename}:{function}:{line}: {indent}{message}\\n'

Fields:
  {date}     current date (see setDateFormat())
  {time}     current time (see setTimeFormat())
  {label}    what type of thing is getting logged (default: 'DEBUG')
  {pathname} full path of the calling source file
  {basename} base name of the calling source file
  {function} name of function debug.write() was called from
  {line}     number of the calling line of code in its source file
  {indent}   indention string multiplied by the indention level
  {message}  the message to be written

All non-field text is literal text. The '\\n' at the end is required
if you want a line ending at the end of each message. If your
DebugChannel object is configured to write to a LogStream object
that writes to syslog or something similar, you might want to remove
the {date} and {time} (and maybe {label}) fields from the default
format string to avoid logging these values redundantly.

<a name="debug.DebugChannel.indent"></a>
#### indent

```python
 | indent(indent=1)
```

Increase this object's current indenture by this value (which
might be negative. Return this DebugChannel opject with the adjusted
indenture. See write() for how this might be used.

<a name="debug.DebugChannel.undent"></a>
#### undent

```python
 | undent(indent=1)
```

Decrease this object's current indenture by this value (which
might be negative. Return this DebugChannel object with the adjusted
indenture. See write() for how this might be used.

<a name="debug.DebugChannel.writelines"></a>
#### writelines

```python
 | writelines(seq)
```

Just a wrapper around write(), since that method handles
sequences (and other things) just fine. writelines() is only
provided for compatibility with code that expects it to be
supported.

<a name="debug.DebugChannel.__call__"></a>
#### \_\_call\_\_

```python
 | __call__(message)
```

Just a wrapper for the write() method. Message can be a single-
line string, multi-line string, list, tuple, or dict. See write()
for details.

<a name="debug.DebugChannel.write"></a>
#### write

```python
 | write(message)
```

If our debug state is on (True), write the given message using the
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

to its own log line. The keys are sorted in ascending order.
