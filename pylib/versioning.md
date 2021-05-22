# Table of Contents

* [versioning](#versioning)
  * [Version](#versioning.Version)
    * [\_\_init\_\_](#versioning.Version.__init__)
    * [tuplize](#versioning.Version.tuplize)
    * [\_\_cmp\_\_](#versioning.Version.__cmp__)
    * [meta\_compare](#versioning.Version.meta_compare)
    * [\_\_getitem\_\_](#versioning.Version.__getitem__)
    * [\_\_setitem\_\_](#versioning.Version.__setitem__)
    * [\_\_str\_\_](#versioning.Version.__str__)
    * [\_\_repr\_\_](#versioning.Version.__repr__)
    * [\_\_iter\_\_](#versioning.Version.__iter__)
    * [metaParser](#versioning.Version.metaParser)
  * [RankedVersion](#versioning.RankedVersion)
    * [setRanks](#versioning.RankedVersion.setRanks)
    * [metaParser](#versioning.RankedVersion.metaParser)

<a name="versioning"></a>
# versioning

This module is designed to work with any Python version >= 2.7
(including 3.*). We can go a little lower if it's never called as the
main module.

This versioning module can also be used to update version meta data in
existing files (once I implement that feature).

<a name="versioning.Version"></a>
## Version Objects

```python
class Version(object)
```

The Version class is for storing, updating, and comparing semantic
version data. This is a very simple implementation, but it does allow
version comparisons to be numeric, so 1.5 < 1.10.

The meta value defaults to an empty string, but there's a fair amount
of versatility there too. Any numeric suffix is treated numerically so
that 1.2.3.beta-5 < 1.2.3.beta-10, but the string portion is still
compared alphabetically, so 1.2.3.test-5 > 1.2.3.prod-5.

There's also the problem that 1.2.3 < 1.2.3.prod, but see the
RankedVersion for a solution to that.

>>> Version('1.2.3')._parsed_version
(1, 2, 3, '', 0)
>>> Version('1.2.3.test')._parsed_version
(1, 2, 3, 'test', 0)
>>> Version('1.2.3.123')._parsed_version
(1, 2, 3, '', 123)
>>> Version('1.2.3.test-123')._parsed_version
(1, 2, 3, 'test-', 123)
>>> Version('1.2.3.test-123.45')._parsed_version
(1, 2, 3, 'test-', 123.45)
>>> Version('1.2.3.test.123')._parsed_version
(1, 2, 3, 'test.', 123)
>>> Version('1.2.3.test.123.45')._parsed_version
(1, 2, 3, 'test.', 123.45)
>>> a=Version()
>>> str(a)
'0.0.0'
>>> repr(a)
"Version('0.0.0')"
>>> a=Version((1,2,3))
>>> a._version
[1, 2, 3, '']
>>> a._parsed_version
(1, 2, 3, '', 0)
>>> a.major
1
>>> a.minor
2
>>> a.patch
3
>>> a.meta
''
>>> a[3]
''
>>> b=Version(a)
>>> b._parsed_version
(1, 2, 3, '', 0)
>>> a==b
True
>>> a.meta='beta'
>>> a.meta
'beta'
>>> a[3]
'beta'
>>> a._version
[1, 2, 3, 'beta']
>>> a._parsed_version
(1, 2, 3, 'beta', 0)
>>> str(a)
'1.2.3.beta'
>>> str(b)
'1.2.3'
>>> b._parsed_version
(1, 2, 3, '', 0)
>>> a<b
False
>>> a<=b
False
>>> a==b
False
>>> a!=b
True
>>> a>=b
True
>>> a>b
True

<a name="versioning.Version.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(arg=None)
```

The string form of a version constists if up to 3 numbers
followed by a free-form metadata value, all separated by '.'
characters. That might look like any of:

    1
    1.2
    1.2.3
    1.2.3.beta
    1.2.3.beta-3

The numeric parts are, from left to right, called the major, minor,
and patch numbers. The metadata can be any string value.

Initialize this Version instance from a version string, a tuple,
list, or another Version instance. If arg is None (the default), our
value defaults to 0.0.0.

<a name="versioning.Version.tuplize"></a>
#### tuplize

```python
 | tuplize()
```

Set this Version instance's _parsed_version attribute. This must
be called every time our _version attribute changes.

<a name="versioning.Version.__cmp__"></a>
#### \_\_cmp\_\_

```python
 | __cmp__(other)
```

Return -1 if self<other, 0 if self==other, or 1 if self>other.

<a name="versioning.Version.meta_compare"></a>
#### meta\_compare

```python
 | meta_compare(other)
```

Just like __cmp__, but looks only at the meta values.

<a name="versioning.Version.__getitem__"></a>
#### \_\_getitem\_\_

```python
 | __getitem__(i)
```

Return the ith elelement of our value.

<a name="versioning.Version.__setitem__"></a>
#### \_\_setitem\_\_

```python
 | __setitem__(i, val)
```

Set the ith element of our value.

<a name="versioning.Version.__str__"></a>
#### \_\_str\_\_

```python
 | __str__()
```

Return a string version of this Version object's value.

<a name="versioning.Version.__repr__"></a>
#### \_\_repr\_\_

```python
 | __repr__()
```

Return a evaluatable string that would recreate this object.

<a name="versioning.Version.__iter__"></a>
#### \_\_iter\_\_

```python
 | __iter__()
```

Allow iteration to support coercion to tuple and list types.

<a name="versioning.Version.metaParser"></a>
#### metaParser

```python
 | @classmethod
 | metaParser(cls, val)
```

Return any (string,number) tuple that can be parsed from our meta
value. The number may be an int or float value. If meta doesn't
begin with a non-numeric string, the tuple's first element will be
None. If meta doesn't end with a number, the tuple's second element
will be None.

>>> Version.metaParser('')
('', 0)
>>> Version.metaParser('test')
('test', 0)
>>> Version.metaParser('123')
('', 123)
>>> Version.metaParser('123.45')
('', 123.45)
>>> Version.metaParser('test-123.45')
('test-', 123.45)

<a name="versioning.RankedVersion"></a>
## RankedVersion Objects

```python
class RankedVersion(Version)
```

RankedVersion is just like Version, except that it recognizes the
rank values "dev", "test", and "prod" (by default) in its meta
component. For purposes of comparing RankedVersion objects, each value
is greater than the one before it (in the order shown above).

A meta value of "" is greater than "prod", but any other non-ranked
value is less than "dev" and compares any with other non-ranked value
alphabetically.

Whatever the meta value is, any ranked value may be followed by an
arbitrary string that only participates in comparison operations if
the ranked part of each RankedVersion's meta value is the same. This
may be suffixed with a numeric value, which if present, will
participate in comparison operation according to its numeric value. So
"1.2.3.prod.11" is greater than "1.2.3.prod.2", and "1.2.3.beta-dog"
is greater than "1.2.3.beta-chimp", but remember that
"1.2.3.test-anything" is greater than "1.2.3.dev-something" That's
what ranking is all about.

>>> sorted(RankedVersion._ranks.items())
[('dev', 0), ('prod', 2), ('test', 1)]

>>> a=RankedVersion('1.2.3')
>>> a._parsed_version
(1, 2, 3, 3, '', 0)
>>> str(a)
'1.2.3'

>>> b=RankedVersion(a)
>>> id(a)!=id(b)
True
>>> b._parsed_version
(1, 2, 3, 3, '', 0)
>>> str(b)
'1.2.3'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(True, False, False, True, True, False)

>>> b.patch=15
>>> b._parsed_version
(1, 2, 15, 3, '', 0)
>>> str(b)
'1.2.15'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, True, True, False, False)

>>> b.patch='3'
>>> b._parsed_version
(1, 2, 3, 3, '', 0)

>>> b.meta='prod'
>>> b._parsed_version
(1, 2, 3, 2, '', 0)
>>> str(b)
'1.2.3.prod'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, False, False, True, True)

>>> a.meta='test'
>>> a._parsed_version
(1, 2, 3, 1, '', 0)
>>> str(a)
'1.2.3.test'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, True, True, False, False)

>>> b.meta='dev'
>>> b._parsed_version
(1, 2, 3, 0, '', 0)
>>> str(b)
'1.2.3.dev'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, False, False, True, True)

>>> a.meta=''
>>> a._parsed_version
(1, 2, 3, 3, '', 0)
>>> str(a)
'1.2.3'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, False, False, True, True)

>>> a.meta='bogus'
>>> a._parsed_version
(1, 2, 3, -1, 'bogus', 0)
>>> str(a)
'1.2.3.bogus'
>>> a==b, a!=b, a<b, a<=b, a>=b, a>b
(False, True, True, True, False, False)

>>> RankedVersion("1.2.3.prod.11")>RankedVersion("1.2.3.prod.2")
True
>>> RankedVersion("1.2.3.beta-dog")>RankedVersion("1.2.3.beta-chimp")
True
>>> RankedVersion("1.2.3.test-anything")>RankedVersion("1.2.3.dev-something")
True

<a name="versioning.RankedVersion.setRanks"></a>
#### setRanks

```python
 | @classmethod
 | setRanks(cls, *ranks)
```

Assign the rank names, in order, to this class. The default ranks
are:
    dev
    test
    prod

If you'd like other, you can set them up by calling this class
method. For example:

    RankedVersion.setRanks('dev','test','canditate','final')

Use whatever ranking terminology you prefer, but be sure call this
method BEFORE instantiating any RankedVersion objects.

<a name="versioning.RankedVersion.metaParser"></a>
#### metaParser

```python
 | @classmethod
 | metaParser(cls, val)
```

Return an (env_rank,string,number) tuple from the given meta
value.

This overloads Version's copy of this method and is called from
Version's tuplize() method during construction and whenever this
instance's data changes.

