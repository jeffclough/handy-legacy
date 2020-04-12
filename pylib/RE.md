# RE Module

## DESCRIPTION

This module extends Python's re module just a touch, so re will be doing
almost all the work. I love the stock re module, but I want it to
support extensible regular expression syntax.

So that's what I've done. You can register your own RE extensions by
calling

```
RE.extend(name,pattern)
```

Doing so means that "(E\<name\>)" will be replaced with "(pattern)", and
"(?E\<name\>)" will be replaced with "(?P\<name\>pattern)", in any regular
expressions you use with this module. To keep things compatible with the
common usage of Python's standard re module, it's a good idea to import
RE like this:

```
import RE as re
```

You can then create whatever custom extension you'd like in this way:

```
re.extend('last_first',r'([!,]+)\s*,\s*(.*)')
```

Doing so means that

```
re_name=re.compile(r'name:\s+(?E<last_first>)')
```

becomes exactly the same as

```
re_name=re.compile(r'name:\s+(([!,]+)\s*,\s*(.*))')
```

If you use the extension like this,

```
re_name=re.compile(r'name:\s+(?E<name=last_first>)')
```

with "name=last_first" rather than just "last_first", that translates to

```
re_name=re.compile(r'name:\s+(?P<name>([!,]+)\s*,\s*(.*))')
```

so you can use groupdict() to get the value of "name".

It turns out having a few of these RE extensions predefined for your
code can be a handy little step-saver that also tends to increase its
readability, especially if it makes heavy use of regular expressions.

### Pre-loaded RE Extensions
This module comes with several pre-loaded RE extensions that I've come
to appreciate.

#### General Extensions

| Name | Description |
| --- | --- |
| id | This matches login account names. If you need to change how this is defined for *your* OS, call `RE.extend('id',r'whatever RE you want')` to replace this pre-loaded extension. |
| ident | This matches Python (and Java, C, et al.) identifiers. |
| comment | Content following #, ;, or //, possibly preceded by whitespace. |

#### Network Extensions
| Name | Description |
| --- | --- |
| ipv4     | E.g. "1.2.3.4".
| ipv6     | E.g. "1:2:3:4:5:6".
| ipaddr   | Matches either ipv4 or ipv6.
| cidr     | E.g. "1.2.3.4/24".
| macaddr  | Looks a lot like ipv6, but the colons may also be dashes or dots instead.
| hostname | A DNS name.
| host     | Matches either hostname or ipaddr.
| email    | Any valid email address. (Well above average, but not quite perfect.) There's also an email_localpart extension, which is used inside both "email" and "url" (below), but it's really just for internal use. Take a look if you're curious.
| url      | Any URL consisting of: <ul> <li>protocol - req (e.g. "http:" or "presto:http:")</li> <li>designator - req (either "email_localpart@" or "//")</li> <li>host - req (anything matching our "host" extension) port - opt (e.g. ":443")</li> <li>path - opt (e.g. "/path/to/content.html")</li> <li>params - opt (e.g. "q=regular%20expression&items=10")</li> </ul> |

#### Time and Date Extensions
| Name | Description |
| --- | --- |
| day      |   |
| month    |   |
| date_YMD |   |
| date_YmD |   |
| date_mD  |   |
| time_HM  |   |
| time_HMS |   |

## CLASSES

### class error(exceptions.Exception)

This is the same as re.error.

## FUNCTIONS

### compile(pattern, flags=0)
Compile a regular expression pattern, returning a pattern object.

### escape(pattern)
Escape all non-alphanumeric characters in pattern.

### extend(name, pattern, expand=False)
Register an extension RE pattern that can be referenced with the
"(?E<name>)" construct. You can call RE.extend() like this:

```
    RE.extend('id','[-_0-9A-Za-z]+')
```

And then, anytime you want to match an account name, you can simply use the
`'(?E<id>)'` extension RE, making your code more readable and less prone to
errors in regular expressions. Also, there are certainly other ways to
accomplish this, a natural side-effect of this is that the RE for an account
name only exists in one place in your code if it ever needs to be updated. Such
references are replaced by `'([-_0-9A-Za-z]+)'` by the time the stock re module
gets control. If you want to refer to matched groups by name, use the
`'(?E<user=id>)'` form, which be substituted with `'(?P<user>[-_0-9A-Za-z]+)'`.

### findall(pattern, s, flags=0)
Return a list of all non-overlapping matches in the string.

If one or more groups are present in the pattern, return a list of
groups; this will be a list of tuples if the pattern has more than one
group.

Empty matches are included in the result.

### match(pattern, s, flags=0)
Try to apply the pattern at the start of the string, returning a
match object, or None if no match was found.

### purge()
Clear the regular expression cache

### search(pattern, s, flags=0)
Scan through string looking for a match to the pattern, returning a
match object, or None if no match was found.

### split(pattern, s, maxsplit=0, flags=0)
Split the source string by the occurrences of the pattern,
returning a list containing the resulting substrings.

### sub(pattern, repl, string, count=0, flags=0)
Return the string obtained by replacing the leftmost
non-overlapping occurrences of the pattern in string by the
replacement repl. repl can be either a string or a callable; if a
string, backslash escapes in it are processed. If it is a callable,
it's passed the match object and must return a replacement string to
be used.

### subn(pattern, repl, string, count=0, flags=0)
  Return a 2-tuple containing (new_string, number). new_string is the
  string obtained by replacing the leftmost non-overlapping occurrences
  of the pattern in the source string by the replacement repl. number
  is the number of substitutions that were made. repl can be either a
  string or a callable; if a string, backslash escapes in it are
  processed. If it is a callable, it's passed the match object and must
  return a replacement string to be used.

### template(pattern, flags=0)
Compile a template pattern, returning a pattern object.

## DATA
```
I = IGNORECASE = 2
L = LOCALE = 4
M = MULTILINE = 8
S = DOTALL = 16
U = UNICODE = 32
X = VERBOSE = 64
DEBUG = 128
```
