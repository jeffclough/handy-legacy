#!/usr/bin/env python3

"""
Read markdown and output formatted text.
"""

import _io,os,sys
from handy import ProgInfo

prog=ProgInfo()
tw,_=prog.getTerminalSize()

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# The MarkdownElement nested structure.

def numeric_counter(start=1,step=1):
  'A generator that counts up from "start" by "step."'

  i=start
  while True:
    yield i
    i+=step

def bullet_counter(start=0,step=None):
  '''A generator that returns a constant bullet character rather than an
  incrementing number. The "start" value is the nesting level (starting
  with 0) of the unordered list at hand. The "step" argument is ignored.
  This is an uncomfortable method signature for what this function does,
  but it's necessary to let MarkdownOrderedList and
  MarkdownUnorderedList share functionality implemented in
  MarkdownList.'''

  bullets='•○■□▶▷▰▱◆◇⦾◦◗'

  while True:
    yield bullets[start%len(bullets)]

class MarkdownElement(object):
  def __init__(self):
    # A list of this MarkdownElement's sub-elements.
    self.elements=[]

class MarkdownDocument(MarkdownElement):
  def __init__(self):
    super().__init__()

class MarkdownParagraph(MarkdownElement):
  def __init__(self):
    super().__init__()

class MarkdownHeading(MarkdownElement):
  def __init__(self,level)
    "A markdown heading of level 1-6."

    super().__init__()
    self.level=level

class MarkdownListItem(MarkdownElement):
  def __init__(self):
    super().__init__()

class MarkdownList(MarkdownElement):

  def __init__(self,level):
    '"level" is the nesting level of this list, starting with 0.'

    super().__init__()

    # Remember the nesting level of this list.
    self.level=level

    # Find the generator function that yields the enumeration for the items in
    # this list.
    self.getMarker=self.markers[level%len(self.markers)]

    # Other initializations for this list.
    self.items=[]

class MarkdownOrderedList(MarkdownList):
  markers=[
    numeric_counter,
  ]

  def __init__(self):
    super().__init__()

class MarkdownUnorderedList(MarkdownList):
  markers=[
    bullet_counter,
  ]

  def __init__(self):
    super().__init__()

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Parsing
  
class MarkdownParser(object):
  """A MarkdownParser instance parses input text to yield a nested data
  structure of instances of subclasses of MarkdownElement. Use a
  MarkdownWriter subclass instance to output the parsed markdown to some
  output stream."""

  def __init__(self,width=None,indent=2):
    self.width=width if width else prog.getTerminalSize()[0]
    self.indent=indent

  def __call__(self,text):
    """Format and output the markdown in the "text" argument to the
    "out" stream-like object.

    """

    # Figure out how to read lines from our "text" argument.
    if isinstance(text,_io.TextIOWrapper):
      reader=self.fileReader
    elif isinstance(text,(list,tuple)):
      reader=self.iterReader
    elif isinstance(text,str):
      reader=self.stringReader
    else:
      raise ValueError(f"MarddownFormatter cannot format values of type {type(text)}")

    # Read our text one line at a time, building our MarkdownElement structure
    # as we go. The root of this structure is a MarkdownDocument.
    doc=MarkdownDocument()
    # TODO: Now add elements to our document.
    

  def fileReader(self,f):
    """A generator yielding one line from file-like object "f" at a
    time."""

    for line in f:
      yield line.rstrip('\n')

  def iterReader(self,it):
    """A generator yielding one line from iterable "it" at a time."""

    for line in it:
      yield line

  def stringReader(self,s):
    """A generator yielding one line from string "s" at a time."""

    i=0
    n=len(s)
    while i<n:
      j=s.find(os.linesep,i)
      if j<0:
        yield s[i:] # Yield the remainder of this string.
        j=n         # Arrange to exit this loop.
      else:
        yield s[i:j] #Yield the next line in this string.
        j+=1
      i=j           # Set up to find the end of the next line in this string.

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# The MarkdownElement nested structure.

class MarkdownWriter(object):
  pass

