'''

'''

class AdHoc(dict):
  '''The AdHoc class facilitates ad hoc objects. It's really just a
  dictionary that allows its entries to be accessed using attribute
  syntax. Or think of it as a meta one-off object class.

  AdHoc's constructor accepts the same arguments as dict's constructor.
  It processes the resulting dictionary by replacing any constituent
  dictionaries with AdHoc objects. It also scans for list and tuple
  values and replaces any dictionaries they contain with AdHoc objects.

  In addition to offering syntactically natural access to dictionaries,
  AdHoc also overloads repr() to produce a key-sorted string, and str()
  to produce a sorted and recursively indented string that's more
  suitable for human consumption.
  
  >>> o=AdHoc(a=1,b=2,c=3)
  >>> o.c
  3
  >>> o['c']
  3
  >>> o.c=4
  >>> sorted(o.items())
  [('a', 1), ('b', 2), ('c', 4)]
  >>> d=dict(a=1,b=2,c=dict(aa=11,bb=22,cc=33,dd=dict(aaa=111,bbb=222)),d=4,e=dict(dd=44,ee=5,ff=6))
  >>> r=AdHoc(**d)
  >>> repr(r)
  "{'a': 1, 'b': 2, 'c': {'aa': 11, 'bb': 22, 'cc': 33, 'dd': {'aaa': 111, 'bbb': 222}}, 'd': 4, 'e': {'dd': 44, 'ee': 5, 'ff': 6}}"
  >>> r.a
  1
  >>> r.c
  {'aa': 11, 'bb': 22, 'cc': 33, 'dd': {'aaa': 111, 'bbb': 222}}
  >>> r.c.aa
  11
  >>> r.c.dd.bbb
  222
  >>> r.toString()
  '{{\\n   a=1\\n   b=2\\n   c={{\\n      aa=11\\n      bb=22\\n      cc=33\\n      dd={{\\n         aaa=111\\n         bbb=222\\n      }}\\n   }}\\n   d=4\\n   e={{\\n      dd=44\\n      ee=5\\n      ff=6\\n   }}\\n}}'
  '''

  # This is the number of spaces by which toString recursively indents.
  INDENTURE=3

  def __init__(self,**kwargs):
    dict.__init__(self,kwargs)
    # If this dictionary contains other dictionaries, recurse.
    for k,v in self.items():
      if isinstance(v,dict):
        self[k]=AdHoc(**v)
      elif isinstance(v,list):
        l=[]
        for x in v:
          if isinstance(x,dict):
            l.append(AdHoc(**x))
          else:
            l.append(x)
        self[k]=l
      elif isinstance(v,tuple):
        l=[]
        for x in v:
          if isinstance(x,dict):
            l.append(AdHoc(**x))
          else:
            l.append(x)
        self[k]=tuple(l)

  def __getattr__(self,key):
    return self.get(key)

  def __setattr__(self,key,val):
    self[key]=val

  def __repr__(self):
    'Just like dict.__repr__, but sorts by key value.'

    return '{'+', '.join(['%r: %r'%(k,v) for k,v in sorted(self.items())])+'}'

  def __str__(self):
    '''Formats each entry as "key=value", one per line, and recursively
    indents.'''

    return self.toString()

  def toString(self,indent=0):
    '''Formats each entry as "key=value", one per line, and recursively
    indents.'''

    indent+=self.INDENTURE
    s='{{'
    for k,v in sorted(self.items()):
      s+='\n'+' '*indent+str(k)+'='
      if isinstance(v,AdHoc):
        s+=v.toString(indent)
      elif isinstance(v,list):
        ls='[\n'
        indent+=self.INDENTURE
        for x in v:
          ls+=' '*(indent)
          if isinstance(x,AdHoc):
            ls+=x.toString(indent)+',\n'
          else:
            ls+=str(x)+','
        indent-=self.INDENTURE
        ls+=' '*indent+']'
        s+=ls
      elif isinstance(v,tuple):
        ls='(\n'
        indent+=self.INDENTURE
        for x in v:
          ls+=' '*(indent)
          if isinstance(x,AdHoc):
            ls+=x.toString(indent)+',\n'
          else:
            ls+=str(x)+','
        indent-=self.INDENTURE
        ls+=' '*indent+')'
        s+=ls
      else:
        s+=str(v)
    s+='\n'+' '*(indent-self.INDENTURE)+'}}'
    return s

if __name__=='__main__':
  import doctest
  doctest.testmod()
