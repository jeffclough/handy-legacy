import pipes,re

def shellify(val):
  """Return the given value quotted and escaped as necessary for a Unix
  shell to interpret it as a single value.

  >>> print shellify(None)
  ''
  >>> print shellify(123)
  123
  >>> print shellify(123.456)
  123.456
  >>> print shellify("This 'is' a test of a (messy) string.")
  'This '"'"'is'"'"' a test of a (messy) string.'
  >>> print shellify('This "is" another messy test.')
  'This "is" another messy test.'
  """

  if val==None:
    return "''"
  if isinstance(val,int) or isinstance(val,float):
    return val
  if not isinstance(val,basestring):
    val=str(val)
  return pipes.quote(val)

class TitleCase(str):
  """A TitleCase value is just like a str value, but it gets title-cased
  when it is created.

  >>> TitleCase('')
  ''
  >>> TitleCase('a fine kettle of fish')
  'A Fine Kettle of Fish'
  >>> TitleCase('    another     fine     kettle     of     fish    ')
  'Another Fine Kettle of Fish'
  >>> t=TitleCase("to remember what's yet to come")
  >>> t
  "To Remember What's Yet to Come"
  >>> t.split()
  ['To', 'Remember', "What's", 'Yet', 'to', 'Come']
  >>> str(type(t)).endswith(".TitleCase'>")
  True
  """
  
  # Articles, conjunctions, and prepositions are always lower-cased, unless
  # they are the first word of the title.
  lc=set("""
    a an the
    and but nor or
    about as at by circa for from in into of on onto than till to until unto via with
  """.split())

  def __new__(cls,value=''):
    # Divide this string into words, and then process it that way.
    words=[w for w in value.lower().split() if w]

    # Join this sequence of words into a title-cased string.
    value=' '.join([
      words[i].lower() if words[i] in TitleCase.lc and i>0 else words[i].capitalize()
        for i in range(len(words))
    ])

    # Now become our immutable value as a title-cased string.
    return str.__new__(cls,value)

if __name__=='__main__':
  import doctest,sys
  t,f=doctest.testmod()
  if f>0:
    sys.exit(1)
