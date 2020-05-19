# RE Module

## DESCRIPTION

This module extends Python's re module just a touch, so re will be doing
almost all the work. I love the stock re module, but I'd also like it to
support extensible regular expression syntax.

So that's what this module does. It is a pure Python wrapper around
Python's standard re module that lets you register your own regexp
extensions by calling

```
RE.extend(name,pattern)
```

Doing so means that `(?E<name>)` in regular expressions used with *this*
module will be replaced with `(pattern)`, and `(?E\<label=name\>)` will be
replaced with `(?P<label>pattern)`, in any regular expressions you use
with *this* module. To keep things compatible with the common usage of
Python's standard re module, it's a good idea to import RE like this:

```
import RE as re
```

This keeps your code from calling the standard re functions directly
(which will report things like `(?E<anything>)` as errors, of course),
it lets you then create whatever custom extension you'd like in this way:

```
re.extend('last_first',r'([!,]+)\s*,\s*(.*)')
```

This regexp matches "Flanders, Ned" in this example string:

```
name: Flanders, Ned
```

And you can use it this way:

```
re_name=re.compile(r'name:\s+(?E<last_first>)')
```

That statement is exactly the same as

```
re_name=re.compile(r'name:\s+(([!,]+)\s*,\s*(.*))')
```

but it's much easier to read and understand what's going on. If you use
the extension like this,

```
re_name=re.compile(r'name:\s+(?E<name=last_first>)')
```

with "name=last_first" rather than just "last_first", that translates to

```
re_name=re.compile(r'name:\s+(?P<name>([!,]+)\s*,\s*(.*))')
```

so you can use the match object's groupdict() method to get the value of
the "name" group.

It turns out having a few of these regexp extensions predefined for your
code can be a handy little step-saver that also tends to increase its
readability, especially if it makes heavy use of regular expressions.

### Pre-loaded Regexp Extensions
This module comes with several pre-loaded regexp extensions that I've come
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
| ipv4     | E.g. "123.45.6.78".
| ipv6     | E.g. "1234:5678:9abc:DEF0:2:345".
| ipaddr   | Matches either ipv4 or ipv6.
| cidr     | E.g. "123.45.6.78/24".
| macaddr  | Looks a lot like ipv6, but the colons may also be dashes or dots instead.
| hostname | A DNS name.
| host     | Matches either hostname or ipaddr.
| email    | Any valid email address. (Well above average RFC 5322 compliance, but not quite perfect.) There's also an email_localpart extension, which is used inside both "email" and "url" (below), but it's really just for internal use. Take a look if you're curious.
| url      | Any URL consisting of: <ul> <li>protocol - REQUIRED (e.g. "http:" or "presto:http:")</li> <li>designator - REQUIRED (either "email_localpart@" or "//")</li> <li>host - REQUIRED (anything matching our "host" extension)</li><li>port - OPTIONAL (e.g. ":443")</li> <li>path - OPTIONAL (e.g. "/path/to/content.html")</li> <li>params - OPTIONAL (e.g. "q=regular%20expression&items=10")</li> </ul> |

#### Time and Date Extensions
| Name | Description |
| --- | --- |
| day      | Day of week, Sunday through Saturday, or any unambiguous prefix thereof.  |
| day3     | First three letters of any day of the week. |
| DAY      | Full name of any day of the week. |
| month    | January through December, or any unambiguous prefix thereof.  |
| month3   | First three letters of any month. |
| MONTH    | Full name of any month. |
| date_YMD | [CC]YY(-|/|.)[M]M(-|/|.)[D]D  |
| date_YmD | [CC]YY(-|/|.)month_name(-|/|.)[D]D  |
| date_mD  | month_name DD  |
| time_HM  | [H]H(-|:|.)MM  |
| time_HMS | [H]H(-|:|.)MM(-|:|.)SS  |

## CLASSES

### class error(exceptions.Exception)

This is the same as re.error.

## FUNCTIONS

### compile(pattern, flags=0)
Compile a regular expression pattern, returning a pattern object.

### escape(pattern)
Escape all non-alphanumeric characters in pattern.

### extend(name, pattern, expand=False)
Register an extension regexp pattern that can be referenced with the
`(?E<name>)` extension construct. You can call RE.extend() like this:

```
RE.extend('id',r'[-_0-9A-Za-z]+')
```

This registers a regexp extension named "id" with a regexp value of `r'[-_0-9A-Za-z]+'`. This means that rather than using `r'[-_0-9A-Za-z]+'` in every regexp where you need to match a username, you can use `r'(?E<id>)'` or maybe `r'(?E<user=id>)'` instead. The first form is simply expanded to

```
r'([-_0-9A-Za-z]+)'
```

Notice that parentheses are used so this becomes a regexp group. If you use the `r'(?E<user=id>)'` form of the id regexp extension, it is expanded to

```
r'(?P<user>[-_0-9A-Za-z]+)'
```

In addition to being a parenthesized regexp group, this is a *named* group that can be retrived by the match object's groupdict() method.

Normally, the pattern parameter is stored directly in this module's extension registry (browse through `RE._extensions` to see what this looks like). If the `expand` parameter is True, any regexp extensions in the pattern are expanded before being added to the registry. So for example,

```
RE.extend('cred',r'^\s*cred\s*=\s*(?E<id>):(.*)$')
```

will simply store that regular expression in the registry labeled as "cred". But if you register it this way,

```
RE.extend('cred',r'^\s*cred\s*=\s*(?E<id>):(.*)$',expand=True)
```

this expands the regexp before registering it, which means this is what's stored in the registry:

```
r'^\s*cred\s*=\s*([-_0-9A-Za-z]+):(.*)$'
```

The result of using `'(?E<cred>)'` in a regular expression is exactly the same in either case.

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
