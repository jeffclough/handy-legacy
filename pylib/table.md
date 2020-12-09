# Table of Contents

* [table](#table)
  * [Table](#table.Table)
    * [Row](#table.Table.Row)
    * [formatInt](#table.Table.formatInt)
    * [formatFloat](#table.Table.formatFloat)
    * [formatString](#table.Table.formatString)
    * [formatOther](#table.Table.formatOther)

<a name="table"></a>
# table

A Table instance is fundamentally a list of rows, where each row is
another list. It is suitable for tabular data and can be manipulated
as such. A Table can optionally have column names, but they are not
included in the Table's data. Column names are case-sensitive.

One major difference between a Table and a list[][] is that a the
rows of a Table MUST all be the same length.

t=Table(columns=5)

t=Table(columns='Name Street City State Zip'.split())

t.append(row)

t.extend(iterable_producing_row_values)

t.count() returns number of rows.

t.insert(index,row)

t.pop(index=-1)

t.reverse()

t.sort(cmp=None,key-=None,reverse=False)

t.ouput(format='table',stream=sys.stdout,dialect='fixed') <-- the defalt
t.ouput(format='table',stream=sys.stdout,dialect='markdown')
t.ouput(format='csv',stream=sys.stdout,dialect=',r"mt\\f\n')
t.ouput(format='json',stream=sys.stdout)

t[row_num] refers directly to that row (not a copy).
t[row_num][col_num] refers directly to that cell of the table (not a copy).
t[row_num][col_name] refers directly to that cell of the table (not a copy).
t[col_name] returns a copy of that column's values.

<a name="table.Table"></a>
## Table Objects

```python
class Table(list)
```

<a name="table.Table.Row"></a>
## Row Objects

```python
class Row(list)
```

A Table.Row object is just like a Python list, but it knows what
Table instance it belongs to, which means that it knows what length
it should be.

Instantiating Table.Row does NOT add the new instance to its table.
Use Table's insert() or append() methods for that.

<a name="table.Table.Row.__setslice__"></a>
#### \_\_setslice\_\_

```python
 | __setslice__(i, j, seq)
```

Replace self[i:j] with y IFF len(y)==j-i.

<a name="table.Table.formatInt"></a>
#### formatInt

```python
 | formatInt(val, width=None)
```

Return this integer as a string. If width is not None, it must
be an integer giving the number of chacters the string must contain.

<a name="table.Table.formatFloat"></a>
#### formatFloat

```python
 | formatFloat(val, width=None)
```

Return this float as a string. If width is not None, it must be
an integer giving the number of chacters the string must contain.

<a name="table.Table.formatString"></a>
#### formatString

```python
 | formatString(val, width=None)
```

Return this string unmodified if width is None. Otherwise,
return it formatted in the given width, which must be an integer.

<a name="table.Table.formatOther"></a>
#### formatOther

```python
 | formatOther(val, width=None)
```

Do our best to convert this value to a string and then
return it formatted as such. If you'd like to handle certain
types differently, override this method in your own subclass.

