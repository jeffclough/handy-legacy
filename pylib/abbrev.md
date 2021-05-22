# Table of Contents

* [abbrev](#abbrev)
  * [IndexedNames](#abbrev.IndexedNames)
    * [\_\_init\_\_](#abbrev.IndexedNames.__init__)
    * [\_\_repr\_\_](#abbrev.IndexedNames.__repr__)
    * [\_\_contains\_\_](#abbrev.IndexedNames.__contains__)
    * [\_\_getitem\_\_](#abbrev.IndexedNames.__getitem__)
    * [get](#abbrev.IndexedNames.get)
    * [items](#abbrev.IndexedNames.items)
    * [keys](#abbrev.IndexedNames.keys)
    * [values](#abbrev.IndexedNames.values)
  * [AbbrevDict](#abbrev.AbbrevDict)
    * [\_\_init\_\_](#abbrev.AbbrevDict.__init__)

<a name="abbrev"></a>
# abbrev

<a name="abbrev.IndexedNames"></a>
## IndexedNames Objects

```python
class IndexedNames(object)
```

Handle the tedium of matching things like day and month names to
their proper index values, even when given only an abbreviated name to
get the index value of. Use dictionary syntax to get and set index
values on an instance of this class.

>>> foo=IndexedNames('Abcd Abef Ghij Klmn Opqr Opqs Opqt'.split(),4,2)
>>> print repr(foo)
IndexedNames(('Abcd', 'Abef', 'Ghij', 'Klmn', 'Opqr', 'Opqs', 'Opqt'), start=4, step=2)
>>> print foo['abc']
4
>>> print foo['abe']
6
>>> foo['totally bogus']
Traceback (most recent call last):
KeyError: 'totally bogus'
>>> foo['a']
Traceback (most recent call last):
KeyError: 'a'
>>> print 'ghij' in foo
True
>>> print 'ghi' in foo
True
>>> print 'gh' in foo
True
>>> print 'g' in foo
True
>>> print foo[0]
Traceback (most recent call last):
KeyError: '0'
>>> print foo[4]
Abcd
>>> print foo[8]
Ghij
>>> foo[99]
Traceback (most recent call last):
KeyError: '99'
>>> foo.items()
[('Abcd', 4), ('Abef', 6), ('Ghij', 8), ('Klmn', 10), ('Opqr', 12), ('Opqs', 14), ('Opqt', 16)]
>>> foo.keys()
['Abcd', 'Abef', 'Ghij', 'Klmn', 'Opqr', 'Opqs', 'Opqt']
>>> foo.values()
[4, 6, 8, 10, 12, 14, 16]
>>> bar=IndexedNames('abc ABC def ghi'.split())
Traceback (most recent call last):
KeyError: "Duplicate items in list: 'abc'"
>>> bar=IndexedNames('abc ABCD def ghi'.split())
Traceback (most recent call last):
KeyError: "'abc' is an abbreviation of 'abcd'"
>>> dow=IndexedNames('Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split())
>>> print dow.get('M')
0
>>> print dow.get('Tu')
1
>>> print dow.get('W')
2
>>> print dow.get('Th')
3
>>> print dow.get('F')
4
>>> print dow.get('Sa')
5
>>> print dow.get('Su')
6
>>> print dow.get('T')
None
>>> print dow.get('x')
None
>>> print dow.get('monday')
0
>>> print dow.get('mondayx')
None

<a name="abbrev.IndexedNames.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(name_list, start=0, step=1)
```

Store an index value, starting at 0 by default, for each name in
the list. Also precompute all distinct abbreviations for those
names, remembering each one by the index of the full name.

Every name in the list must be case-insensitively distinct from
every other name, an no full name may match the beginning of another
name. Otherwise, a KeyError will be raised.

<a name="abbrev.IndexedNames.__repr__"></a>
#### \_\_repr\_\_

```python
 | __repr__()
```

Return a string that could be passed to eval() to recreate this
object.

<a name="abbrev.IndexedNames.__contains__"></a>
#### \_\_contains\_\_

```python
 | __contains__(key)
```

Return true if key is either the name or index of an item stored
in this object.

<a name="abbrev.IndexedNames.__getitem__"></a>
#### \_\_getitem\_\_

```python
 | __getitem__(key)
```

If key is a string value, return the index of that string.
Otherwise, assume key is an index and return the corresponding
name.

<a name="abbrev.IndexedNames.get"></a>
#### get

```python
 | get(key, default=None)
```

If key is a string value, return the index of that string.
Otherwise, assume key is an index and return the corresponding
name. In either case, return the default value if the key is
not found.

<a name="abbrev.IndexedNames.items"></a>
#### items

```python
 | items()
```

Return a list of (name, index) tuples that defines this object's
value, ensuring that the names are returned in the same order as
they were originally presented to this object. The list returned is
suitable for constructing a dict.

<a name="abbrev.IndexedNames.keys"></a>
#### keys

```python
 | keys()
```

Return a list of the names stored in this object in the same
order in which they were originally presented to it.

<a name="abbrev.IndexedNames.values"></a>
#### values

```python
 | values()
```

Return a list of index values for the names stored in this
object, ensuring that the index values are in the same order as the
names.

<a name="abbrev.AbbrevDict"></a>
## AbbrevDict Objects

```python
class AbbrevDict(dict)
```

<a name="abbrev.AbbrevDict.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*args, **kwargs)
```

This is just like dict's constructor, but it also accepts a
keymod keyword argument. If given, keymod must be a function that
accepts a key value as its sole argument and returns the modified
version of that key (e.g. the lower-case version of the key).

