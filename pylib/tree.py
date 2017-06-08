import sys

class Node(object):
  def __init__(self,val):
    """This most basic of Node types stores only a value."""

    self.val=val

  def __str__(self):
    return self.val

  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__,self.val)

class NTreeNode(Node):
  def __init__(self,val,**kwargs):
    """Initialize this node with a value.

    Optional keyword arguments:
    parent    - An existing NTreeNode object. This new node will be
                added to its children.
    children  - A list of NTreeNode objects. These will be the children
                of this new node.
    """

    super(NTreeNode,self).__init__(val)
    self.parent=kwargs.get('parent',None)
    self.children=kwargs.get('children',[])

    if self.parent!=None:
      # Make this new node a child of its parent.
      self.parent.children.append(self)

  def __repr__(self):
    if self.children:
      c=', children='+repr(self.children)
    else:
      c=''
    return '%s(%r%s)'%(self.__class__.__name__,self.val,c)

  def __getitem__(self,key):
    if str(self)==key:
      return self
    for node in self.children:
      try:
        return node[key]
      except KeyError:
        pass
    raise KeyError(key)

  def path(self,**kwargs):
    separator=kwargs.get('separator','/')
    formatter=kwargs.get('formatter',str)
    root=kwargs.get('root',None)
    if self.parent==None or self is root:
      return formatter(self)
    else:
      return self.parent.path(separator=separator,formatter=formatter,root=root)+separator+formatter(self)

class TreeWriter(object):
  def __init__(self,**kwargs):
    self.output=kwargs.get('output',sys.stdout)
    self.indent_width=kwargs.get('indent_width',4)
    self.child_finder=kwargs.get('child_finder',lambda node: node.children)
    self.child_counter=kwargs.get('child_counter',lambda node: len(node.children))
    self.formatter=kwargs.get('formatter',lambda node: str(node))

  def write(self,node,indent_str=''):
    # Output the node at hand.
    if indent_str!='':
      self.output.write(
        (indent_str[:-(self.indent_width)])+ '+'+('-'*(self.indent_width-1))
      )
    self.output.write(self.formatter(node)+'\n')

    # Recursively output each child node, managing indenture as we go.
    n=self.child_counter(node)
    new_indent_str='|'+(' '*(self.indent_width-1))
    for i,c in enumerate(self.child_finder(node),1):
      if i==n:
        new_indent_str=' '*self.indent_width
      self.write(c,indent_str+new_indent_str)

if __name__=='__main__':
  print """
Building a tree by specifying each node's children:
"""
  root=NTreeNode('A',children=[
    NTreeNode('B'),
    NTreeNode('C',children=[
      NTreeNode('E'),
      NTreeNode('F',children=[
        NTreeNode('I'),
        NTreeNode('J'),
        NTreeNode('K'),
      ]),
      NTreeNode('G'),
    ]),
    NTreeNode('D',children=[
      NTreeNode('H'),
    ])
  ])
  TreeWriter(indent_width=2).write(root)

  print """
Rebuiding that same tree by specifying each node's parent and outputting
each node with its full path:
"""
  root=NTreeNode('A') # Root has no parent and (for now) no children.
  for name in 'BCD': NTreeNode(name,parent=root)
  for name in 'EFG': NTreeNode(name,parent=root['C'])
  NTreeNode('H',parent=root['D'])
  for name in 'IJK': NTreeNode(name,parent=root['F'])
  TreeWriter(formatter=lambda node: node.path()).write(root)

  print """
We can also write only a branch of the tree and output each node's
full definition with repr() ... which can get messy.
"""
  TreeWriter(formatter=repr).write(root['F'])

  print """
Writing only a branch of a tree with path values still shows the full
path back to root of the whole tree by default, not just to the branch
origin.
"""
  branch=root['C']
  TreeWriter(formatter=lambda node: node.path()).write(branch)

  print """
Or we can tell NTreeNode.path() to limit itself to a gvien branch.
"""
  TreeWriter(formatter=lambda node: node.path(root=branch)).write(branch)

  print """
Getting the full definition of a tree is as easy as calling repr(root):
"""
  print repr(root)

  print """
In fact, we can use eval(repr(any_node)) to make a copy of all or part
of a tree structure, though copy.deepcopy(any_node) would be MUCH more
efficient.
"""
  branch=root['C']
  print repr(branch)
  print
  new_tree=eval(repr(branch))
  TreeWriter().write(new_tree)
