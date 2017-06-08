
# Lengthable is to be used as a metaclass of classes that support
# len(instance) calls.
class Lengthable(type):
  def __len__(self):
    return self.length()

class GroupParser(object):

  # GroupParser.Error exceptions are raised whenn things go wrong.
  class Error(Exception):
    pass

  # Enable len(some_GroupParser_object) to work.
  __metaclass__=Lengthable

  def __init__(self,**kwargs):
  
    self.groupers=kwargs.get('groupers',('()','[]','{}'))
    self.escape_char=kwargs.get('escape_char',None)
    self._init()

  def _init(self):
    "Called internally whenever this object needs to be initialized."

    self.parens=[]
    self.text=''
    self.next_index=0

  def length(self): 
    "Return the number of bracketed groups parsed from our text."

    return len(self.parens)

  def __getitem__(self,i):
    """Return the (start,stop,group_text) tuple at index i of our list
    of bracketted groups."""

    return tuple(
      self.parens[i]+[self.text[self.parens[i][0]:self.parens[i][1]+1]]
    )

  # This lets a GroupParser object behave like an iterator.
  def __iter__(self):
    return self

  # Here's where the iteration happens.
  def next(self):
    if self.next_index>=len(self.parens):
      raise StopIteration
    self.next_index+=1
    return self[self.next_index-1]

  def __call__(self,text):
    """Parse the bracketed groups in the given text, and return this
    object so that the caller can perform further operations on it."""

    self._init()
    self.text=text

    # Get a string consisting only of group starters.
    starters=''.join([
      self.groupers[i][0] for i in range(len(self.groupers))
    ])
    # start_of[')'] returns '(', and so forth.
    start_of=dict([
      (self.groupers[i][1],self.groupers[i][0]) for i in range(len(self.groupers))
    ])
    # Get a string consisting only of group stoppers.
    stoppers=''.join(start_of.keys())
    # Initialize a stack of indices into self.text that start groups.
    starts=[]
    # Remember the last place we saw our escape character, if any.
    escape_index=None
    for i in range(len(text)):
      if self.text[i]==self.escape_char:
        # Remember this escape character's location.
        escape_index=i
      elif self.text[i] in starters:
        if escape_index!=i-1:
          # Remember the start of this bracketed group.
          starts.append(i)
      elif self.text[i] in stoppers:
        if escape_index!=i-1:
          # Remember the end of this bracketed group, provided it matches the
          # most recently encountered starting character. Otherwise, complain
          # about unbalanced groups.
          if len(starts)>0 and start_of[self.text[i]]==self.text[starts[-1]]:
            self.parens.append([starts.pop(),i])
          else:
            if len(starts)>0:
              msg="Unbalanced group at index %d: %r"%(
                starts[-1],self.text[starts[-1]:i+1]
              )
            else:
              msg="%r at index %d has no beginning: %r"%(
                self.text[i],i,self.text[:i+1]
              )
            raise GroupParser.Error(msg)
    # Complain if there's a groupings we haven't found the end of.
    if len(starts)>0:
      i=starts[-1]
      raise GroupParser.Erorr(
        "No closure found for %r at index %d: %r"%(self.text[i],i,self.text[i:])
      )
    # Return this object to the caller can do more stuff with it.
    return self

if __name__=='__main__':
  s='This (is a (test).)'
  p=GroupParser()
  for i,j,t in p(s):
    print "%d -> %d ==> %r"%(i,j,t)
