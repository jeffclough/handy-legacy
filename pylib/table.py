"""

A Table instance is fundamentally a list of rows, where each row is
another list. It is suitable for tabular data and can be manipulated
as such. A Table can optionally have column names, but they are not
included in the Table's data. Column names are case-sensitive.

One major difference between a Table and a list[][] is the rows of a
Table MUST all be the same length.

t=Table(columns=5)

t=Table(columns='Name Street City State Zip'.split())

t.append(row)

t.extend(iterable_producing_row_values(...))

t.count() returns number of rows.

t.insert(index,row)

t.pop(index=-1)

t.reverse()

t.sort(cmp=None,key=None,reverse=False)

t.ouput(format='table',stream=sys.stdout,dialect='box') <-- the defalt
t.ouput(format='table',stream=sys.stdout,dialect='markdown')
t.ouput(format='csv',stream=sys.stdout,dialect=',r'mt\\f\\n')
t.ouput(format='json',stream=sys.stdout)

t[row_num] refers directly to that row (not a copy).
t[row_num][col_num] refers directly to that cell of the table (not a copy).
t[row_num][col_name] refers directly to that cell of the table (not a copy).
t[col_name] returns a COPY of that column's values.


"""

import sys

def base26(n):
  "Return 'A' for n=0, 'B' for n=1, and so forth."

  s=''
  while True:
    n,r=divmod(n,26)
    s=chr(65+r)+s
    if not n:
      break
  return s

class Table(list):

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  class Error(Exception):
    pass

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  class Row(list):
    """A Table.Row object is just like a Python list, but it knows what
    Table instance it belongs to, which means it knows what length it
    should be, and there's a name for each of its elements, so they can
    be addressed by zero-based index or my name.

    Instantiating t.Row using Table t does NOT add the new instance to
    t. Use Table's t.insert() or t.append() methods for that."""

    def __init__(self,table,data=None):
      if not isinstance(table,Table):
        raise Table.Error('Row objects must belong to a given Table object.')
      self.owner=table
      if data!=None:
        # Let Python's own native list constructor do its thing.
        try:
          data=list(data)
        except:
          raise Table.Error('Cannot instantiate Table.Row from %s'%type(data))
        n=len(data)
        if n>self.owner.colcount:
          raise Table.Error('A %d-column table cannot accommodate a %d-column row!'%(self.owner.colcount,n))
        if n<self.owner.colcount:
          # Extend this row to fit the table.
          data.append([None]*(self.owner.colcount-n))
        list.__init__(self,data)

    def append(self,value):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
      super().append(value)

    def extend(self,iterable):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
      super().extend(iterable)

    def insert(self,index,value):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
      super().insert(index,value)

    def pop(self,index=-1):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
      super().pop(index)

    def remove(self,value):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
      super().remove(value)

    def reverse(self):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT be reversed.')
      super().reverse()

    def sort(self,cmp=None,key=None,reverse=False):
      if not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT be sorted.')
      super().sort(cmp,key,reverse)

    def __setslice__(self,i,j,seq):
      "Replace self[i:j] with seq IFF len(seq)==j-i."

      if len(seq)!=j-i and not self.owner._internal_change:
        raise Table.Error('Table rows MUST NOT change length.')
#     if len(seq)==j-i:
#       for c in range(i,j):
#         self[c]=seq[c-i]
      super().__setslice__(i,j,seq)

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  def __init__(self,colnames=None,colcount=None):

    self.colnames=colnames
    self.colcount=colcount

    self._validate_columns()

    # This _internal_change value will be True only to allow the lengths of our
    # rows to change, e.g. while adding or removing a column. Keep this in mind
    # if using a Table in a multi-threaded environment.
    self._internal_change=False

  def _validate_columns(self,set_colcount=None):
    # This is helpful.
    if self.colcount is None and set_colcount is not None:
      self.colcount=set_colcount

    if self.colnames:
      # Ensure colnames makes sense. Initialize colcount from it if needed.
      if not isinstance(self.colnames,(tuple,list)):
        raise Table.Error('If given, colnames argument MUST be a tuple or a list!')
      self.colnames=[str(x) for x in self.colnames]
      if not self.colcount:
        self.colcount=len(self.colnames)
      elif self.colcount!=len(self.colnames):
        raise Table.Error(
          f"{len(self.colnames)} column names not compatible "
          "with column count of {self.colcount}!"
        )
    elif self.colcount:
    # Ensure colcount makes sense. Initialize colnames from it if needed.
      if not isinstance(self.colcount,int):
        raise Table.Error('colcount argument must be an integer!')
      if not self.colnames:
        self.colnames=[base26(c) for c in range(self.colcount)]

    # Ensure we can identify our columns both by name and by number.
    self.colid={self.colnames[c]:c for c in range(self.colcount)}
    self.colid.update({c:c for c in range(self.colcount)})

   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # Row operations specialized to distinguish Table from list.

  def append(self,row):
    row=Table.Row(self,row)
    if not self.colcount:
      self._validate_columns(len(row))
    list.append(self,row)

  def insert(self,index,row):
    row=Table.Row(self,row)
    if not self.colcount:
      self._validate_columns(len(row))
    list.insert(self,index,row)

  def extend(self,rows):
    rows=[Table.Row(self,r) for r in rows]
    if not self.colcount:
      self._validate_columns(max([len(row) for row in rows]))
    list.extend(self,rows)

  def pop(self,index=-1):
    if not len(self):
      raise Table.Error('Cannot pop from empty table')
    return list.pop(self,index)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def formatByType(self,val,width=None):
    """Format the given value according to its type and the given width.
    If width is not given, it is formatted without padding. Numeric
    values are right-justified. All others are left-justified. Override
    this method if you prefer more customized formatting."""

    # Right-justify numbers and left-justify everything else.
    if isinstance(val,int):
      s=f"{val:>{width}d}" if width else str(val)
    elif isinstance(val,float):
      s=f"{val:>{width}g}" if width else str(val)
    elif isinstance(val,str):
      s=f"{val:<{width}s}" if width else str(val)
    else:
      # We don't recognize this type, but maybe it knows how to stringify itself.
      s=f"{str(val):<{width}s}" if width else str(val)
    return s

  def output(self,dialect='box',stream=sys.stdout):
    if dialect in ('ascii','box'):
      if dialect=='box':
        div=' │ '
        hdiv='─┼─'
        hline='─'
      else:
        div=' | '
        hdiv='-+-'
        hline='-'
      # Get the width each column needs.
      widths=[len(self.colnames[c]) for c in range(self.colcount)]
      for c in range(self.colcount):
        widths[c]=max(widths[c],max([len(self.formatByType(row[c])) for row in self]))
      # Write the header lines.
      print(div.join([self.colnames[c].center(widths[c]) for c in range(self.colcount)]),file=stream)
      print(hdiv.join([hline*widths[c] for c in range(self.colcount)]),file=stream)
      # Write the body of this table.
      for row in self:
        print(div.join([self.formatByType(row[c],widths[c]) for c in range(self.colcount)]),file=stream)
    elif dialect=='markdown':
      pass
    else:
      raise Table.Error(f"Unrecognized Table output dialect: {dialect!r}")

if __name__=='__main__':
  import CSV as csv
  from pprint import pprint

  # Annual gas use for my 2007 Yaris.
  test_data_lines="""\
Year,Tanks,Miles,Galons,$/Gal,Total Cost
2007,78,26760,729.23,2.65,1931.64
2008,85,26522,705.6,3.17,2235.73
2009,79,26333,725.05,2.11,1527.62
2010,71,23997,675.41,2.58,1745.51
2011,83,27435,774.08,3.41,2636.03
2012,89,27509,800.23,3.5,2803.84
2013,86,26969,795.1,3.41,2711.69
2014,79,24139,733.85,3.23,2371.21
2015,77,23537,737.36,2.3,1699.14
2016,85,25435,815.09,2.05,1671.76
2017,81,23219,744.2,2.26,1681.05
2018,67,19648,632.2,2.6,1646.36
2019,68,20246,645.24,2.46,1588.2
2020,33,9780,304.18,1.98,602.66
2021,31,8800,273.02,2.8,765.27
2022,32,9573,306.37,3.6,1103.53
this,is,a,test,of,strings""".split('\n')

  def numeric(val):
    "Return the numeric version of this value if possible."

    try:
      return int(val)
    except ValueError:
      try:
        return float(val)
      except:
        pass
    if type(val)!=str:
      val=str(val)
    return val

  reader=csv.reader(test_data_lines)
  test_data=[row for row in reader]
  columns=test_data[0]
  data=[[numeric(c) for c in row] for row in test_data[1:]]

  t=Table(columns)
  t.extend(data)
  t.output()
  print()
  t.output(dialect='ascii')
