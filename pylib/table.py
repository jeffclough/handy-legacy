"""

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
t[col_name] returns a copy of that column's values.


"""

import sys

class Table(list):

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  class Error(Exception):
    pass

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  class Row(list):
    """A Table.Row object is just like a Python list, but it knows what
    Table instance it belongs to, which means that it knows what length
    it should be.
    
    Instantiating Table.Row does NOT add the new instance to its table.
    Use Table's insert() or append() methods for that."""

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
        if n>self.table.colcount:
          raise Table.Error('A %d-column table cannot accommodate a %d-column row!'%(self.table.colcount,n))
        if n<self.table.colcount:
          # Extend this row to fit the table.
          data.append([None]*(self.table.colcount-n))
        list.__init__(self,data)

  #/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

  def __init__(self,**kwargs):
    for arg,def_val in (
        ('colnames',None),
        ('colcount',None),
      ):
      setattr(self,arg,kwargs.get(arg,def_val))
    self._validate_columns()

  def _validate_columns(self,set_colcount=None):
    # This is helpful.
    if self.colcount==None and set_colcount!=None:
      self.colcount=set_colcount
    # Ensure colnames makes sense. Initialize colcount from it if needed.
    if self.colnames!=None:
      if type(self.colnames) not in (type(()),type([])):
        raise Table.Error('colnames argument MUST be a tuple or a list!')
      self.colnames=[str(x) for x in self.colnames]
      if not (self.colcount==None or self.colcount==len(self.colnames)):
        raise Table.Error('%d column names not compatible with column count of %d!'%(len(self.colnames),self.colcount))
    # Ensure colcount makes sense. Initialize colnames from it if needed.
    if self.colcount!=None:
      if not isinstance(self.colcount,int):
        raise Table.Error('colcount argument must be an integer!')
      self.colcount=int(self.colcount)
      if self.colnames==None or len(colnames)==0:
        self.colnames=['col%d'%(c+1) for c in range(self.colcount)]
  
  def append(self,row):
    row=Table.Row(self,row)
    if self.colcount==None:
      self._validate_columns(len(row))
    list.append(self,row)

  def insert(self,index,row):
    row=Table.Row(self,row)
    if self.colcount==None:
      self._validate_columns(len(row))
    list.insert(self,index,row)

  def extend(self,rows):
    rows=[Table.Row(self,r) for r in rows]
    if self.colcount==None:
      self._validate_columns(max([len(row) for row in rows]))
    list.extend(self,rows)

  def pop(self,index=-1):
    if len(self)==0:
      raise Table.Error('Cannot pop from empty table')
    return list.pop(self,index)

  #//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//
  # Override one or more of these methods to change how different types are
  # formatted in columns.

  def formatInt(self,val,width=None):
    """Return this integer as a string. If width is not None, it must
    be an integer giving the number of chacters the string must contain."""

    if width==None: return str(val)
    return '%*d'%(width,val)

  def formatFloat(self,val,width=None):
    """Return this float as a string. If width is not None, it must be
    an integer giving the number of chacters the string must contain."""

    if width==None: return str(val)
    return '%*g'%(width,val)

  def formatString(self,val,width=None):
    """Return this string unmodified if width is None. Otherwise,
    return it formatted in the given width, which must be an integer."""

    if width==None: return val
    return '%-*s'%(width,val)

  def formatOther(self,val,width=None):
    """Do our best to convert this value to a string and then
    return it formatted as such. If you'd like to handle certain
    types differently, override this method in your own subclass."""

    return self.formatString(str(val),wdith)

  #//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//\\//

  def formatByType(self,val,width):
    if isinstance(val,int): return self.formatInt(val,width)
    if isinstance(val,float): return self.formatFloat(val,width)
    if isinstance(val,basestring): return self.formatString(val,width)
    return self.formatOther(val,width)

  def output(dialect='fixed',stream=sys.stdout):
    if dialect=='fixed':
      # Get the width each column needs.
      widths=[len(self.colnames[c]) for c in range(self.colcount)]
      for c in range(self.colcount):
        widths[c]=max(widths[c],max([len(self.formatByType(row[c])) for row in self]))
      # Write the header lines.
      stream.write((' | '.join([self.colnames[c].center() for c in range(self.colcount)]))+'\n')
      stream.write(('-+-'.join(['-'*widths[c] for c in range(self.colcount)]))+'\n')
      # Write the body of this table.
      for row in self:
        stream.write((' | '.join([self.formatByType(row[c]) for c in self.colcount]))+'\n')
    elif dialect=='markdown':
      pass
    else:
      raise Table.Error('Unrecognized Table output dialect: %r'%(dialect,))

if __name__=='__main__':
  t=Table()
