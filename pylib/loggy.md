# Table of Contents

* [loggy](#loggy)
  * [log\_lines](#loggy.log_lines)
  * [get\_logger](#loggy.get_logger)
  * [LogStream](#loggy.LogStream)

<a name="loggy"></a>
# loggy

<a name="loggy.log_lines"></a>
#### log\_lines

```python
log_lines(log, level, data)
```

Log individual lines at the given log level. If data is a string,
each line is logged individually. If it is a non-string sequence or an
iterable of some kind, each entry will be be logged.

<a name="loggy.get_logger"></a>
#### get\_logger

```python
get_logger(**kwargs)
```

Return the default logging object (if facility==None), or set up a
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
the logged message.

<a name="loggy.LogStream"></a>
## LogStream Objects

```python
class LogStream(object)
```

If you need to write to some log facility as if it were a stream,
instantiate LogStream using the parameters you'd use with
get_logger(). If you don't supply a "level" argument, it will default
to "debug".

