#!/usr/bin/env python

"""
This module makes outputting sensible, correct english sentences much
more practical. For instance, as programmers, it's way too easy to write
code of this form:

  print "Found %d new customers this week"%new_cust

The problem is when new_cust is 1, right? And we're often apathetic
enough to take a "that's good enough" attitude about this kind of thing
because we don't want to write code like this:

  if dcount==1:
    print "We snipped 1 dog's tail this week."
  else:
    print "We snipped %d dogs' tails this week."

But what if we could do it this way instead:

  print "We snipped %s this week"%nounf('dog',dcount,'tail')

or

  print "Found %s this week"%nounf('customer'%new_cust,fmt="%(count)d new %(noun)s")

That's simple enough to do that even crusty old programmers (like me)
might find themselves inclined to write code that outputs more standard
english.

That's the idea behind this module. I think we (lazy) programmers would
be happy to write better code if it were just easier.

Most of this module is linguistic "internals." See the global functions
at the bottom for the practical part of the documentation.
"""

class Suffixer(object):
  """This is mostly a base class that provides only the most general
  functionality.

  Think of Suffixer (and its derivatives) instances as rules that know
  1) how to reconize when a given word is suitable for the rule, and 2)
  how and when to apply either the singular or plural suffix to that
  word, depending on a given count. For example, here's a very simple
  rule set that will work on a surprising range of english nouns:

    rules=[
      Suffix('','es',
        test=lambda s: any([
          s.endswith(e) for e in ('s','sh','ch','x')
      ])),
      Suffix('y','ies',replace=-1,
        test=lambda s: len(s)>2 and s[-1]=='y' and s[-2] not in 'aeiou'
      ),
      Suffix('','s'),
    ]

  Notice how the replace argument to Suffixer's constructor is used in
  rules[1]. The -1 value indicates that whatever suffix is applied to the
  root, should replace the last character of the given root. This is
  helpful for pluralizing "penny" to "pennies".

  Notice also that there's no "test" function for that last suffixing
  rule. That means that its willing to be applied to any word you give
  it. (And that's why it comes last.)

  You might apply this list of suffixing rules to a given noun like
  this:

    noun="cow"
    count=5
    for r in rules:
      if r.test(noun):
        word=r(noun,count)
        break
    print word

  The result is to print the word, "cows" because the first matching
  rule was rule[2], and there were 5 cows. But if you change the noun
  in the above example to "church", you'll see "churches" printed
  because "church" matches the conditions of rule[0].

  It's easy (and typical) to wrap all this in a convenient function, and
  maybe subclass Suffixer for special parts of speech, like nouns and
  verbs.

  The point of Suffixer is to provide a way to express suffixing rules
  in a way that can be specialized and extended to particular parts of
  speech in helpful ways. For instance NounSuffixer lets the caller say
  whether the suffixed root should be expressed possessively."""

  def __init__(self,singular,plural,replace=None,test=None):
    self.singular=singular
    self.plural=plural
    self.replace=replace
    # Ignore the caller's test function if we already have a test() method.
    if not hasattr(self,'test'):
      if test==None:
        self.test=lambda s:True
      else:
        self.test=test

  def __call__(self,root,count):
    "Return our root word suffixed appropriately for count's value."

    # Don't waste our time on an emptry string (or None):
    if not root:
      return ''
    # Make sure our root is a string.
    if not isinstance(root,basestring):
      try:
        root=str(root)
      except:
        raise ValueError('%r (type=%s) is not a string and cannot be converted to a string.'%(root,type(root)))
        
    # Use count to determine which suffix to use.
    if count==1:
      suffix=self.singular
    else:
      suffix=self.plural
    # Apply the suffix to our root.
    if self.replace==None:
      word=root+suffix
    else:
      word=root[:self.replace]+suffix

    return self.matchCapitalization(root,word)

  def matchCapitalization(self,root,word):
    if root[0].isupper() and not word[0].isupper():
      word=word[0].upper()+word[1:]
    return word

class NounSuffixer(Suffixer):

  def __init__(self,singular,plural,replace=None,test=None):
    super(NounSuffixer,self).__init__(singular,plural,replace,test)

  def __call__(self,root,count,pos=False):
    """Return our root word suffixed appropriate for count's value and
    approphized correctly to make it possessive if "pos" is True."""

    # Let our superclass do any pluralization we might need.
    word=super(NounSuffixer,self).__call__(root,count)
    if not word:
      return word

    if pos:
      # Apply "Chicago Manual of Style, 17th edition".
      if count==1:
        # Singular nouns are posessified with "'s", regardless of how they end.
        word+="'s"
      else:
        # With plural possessives, it does depand on the word ending.
        if word[-1]=='s':
          word+="'"
        else:
          word+="'s"

    return word

class IrregularNounSuffixer(NounSuffixer):

  # Make a map of irregularly pluralized nouns.
  _irregular_noun_plurals=dict((
    ('alumnus','alumni'),
    ('appendix','appendices'),
    ('buffalo','buffalo'),
    ('cactus','cacti'),
    ('child','children'),
    ('cod','cod'),
    ('deer','deer'),
    ('die','dice'),
    ('fish','fish'),
    ('focus','foci'),
    ('foot','feet'),
    ('fungus','fungi'),
    ('goose','geese'),
    ('index','indices'),
    ('louse','lice'),
    ('man','men'),
    ('moose','moose'),
    ('mouse','mice'),
    ('nucleus','nuclei'),
    ('octopus','octopi'),
    ('ox','oxen'),
    ('person','people'),
    ('quail','quail'),
    ('radius','radii'),
    ('sheep','sheep'),
    ('shrimp','shrimp'),
    ('swine','swine'),
    ('tooth','teeth'),
    ('trout','trout'),
    ('vortex','vortices'),
    ('woman','women'),
  ))

  def __init__(self):
    super(IrregularNounSuffixer,self).__init__('','',replace=None,test=None)

  def __call__(self,root,count,pos=False):
    if count==1:
      word=root
    else:
      word=self._irregular_noun_plurals[root.lower()]
    return self.matchCapitalization(root,word)

  def test(self,word):
    return word.lower() in self._irregular_noun_plurals

_noun_suffixing_rules=[
  # Check for irregular cases first. The rules below don't apply to these.
  IrregularNounSuffixer(),

  # Words ending with "is" are often pluralised by replacing that with "es".
  NounSuffixer('is','es',-2,lambda s: s.endswith('is')),

  # There are a few word-endings that call for "es" plural suffixes.
  NounSuffixer('','es',None,lambda s: any([s.endswith(ending) for ending in ('s','sh','ch','x')])),

  # Words ending with a consonant followed by "y" generally have "ies" plural suffixes.
  NounSuffixer('y','ies',-1,lambda s: len(s)>2 and s[-1]=='y' and s[-2] not in 'aeiou'),

  # Words ending with "f" or "fe" usually get special treatment.
  NounSuffixer('f','ves',-1,lambda s: s.endswith('f')),
  NounSuffixer('fe','ves',-2,lambda s: s.endswith('fe')),

  # Words ending with "um" are often pluralised by replacing that with "a".
  NounSuffixer('um','a',-2,lambda s: s.endswith('um')),

  # For everything else, we'll guess that a simple "s" suffix will pluralize this noun.
  NounSuffixer('','s',None),
]

def nouner(root,count,pos=False):
  """Return the form of the root word appropriate to the given count and
  posessiveness."""

  for r in _noun_suffixing_rules:
    if r.test(root):
      word=r(root,count,pos)
      break
  return word

def nounf(root,count,pos=False,fmt=None):
  """This function is useful for constructing noun phrases like:

      "1 person's hat"
      "5 people's hats"

  Return the formatted string containing nouner(root,count,pos) as
  "word", the count as "count", as nouner(pos,count) as "pos" if it
  evaluates to a true value.

  If pos is some false value, fmt defaults to "%(count)d %(noun)s".
  Otherwise, fmt defaults to "%(count)d %(noun)s %(pos)s", and pos is
  set to nouner(pos,count)."""

  noun=nouner(root,count,pos)
  if fmt==None:
    if pos:
      pos=nouner(pos,count)
      fmt="%(count)d %(noun)s %(pos)s"
    else:
      fmt="%(count)d %(noun)s"
  return fmt%(locals())

if __name__=='__main__':
  import doctest,sys

  def tests():
    """
    >>> nouner('alumnus',1)
    'alumnus'
    >>> nouner('Alumnus',1)
    'Alumnus'
    >>> nouner('alumnus',5)
    'alumni'
    >>> nouner('Alumnus',5)
    'Alumni'
    >>> nouner('index',5)
    'indices'
    >>> nouner('Index',5)
    'Indices'
    >>> nouner('watch',1)
    'watch'
    >>> nouner('watch',2)
    'watches'
    >>> nouner('penny',1)
    'penny'
    >>> nouner('penny',2)
    'pennies'
    >>> nouner('elf',1)
    'elf'
    >>> nouner('elf',2)
    'elves'
    >>> nouner('life',1)
    'life'
    >>> nouner('life',2)
    'lives'
    >>> nouner('axis',1)
    'axis'
    >>> nouner('axis',2)
    'axes'
    >>> nouner('curiculum',1)
    'curiculum'
    >>> nouner('curiculum',2)
    'curicula'
    >>> nouner('dog',1)
    'dog'
    >>> nouner('dog',2)
    'dogs'
    >>> nounf('dog',5)
    '5 dogs'
    >>> NounSuffixer('n','p',-1)('cat',1)
    'can'
    >>> NounSuffixer('n','p',-1)('cat',2)
    'cap'
    >>> "I have %s."%nounf('fish',1)
    'I have 1 fish.'
    >>> "I have %s."%nounf('fish',2)
    'I have 2 fish.'
    >>> "I have %s."%nounf('ox',1)
    'I have 1 ox.'
    >>> "I have %s."%nounf('ox',2)
    'I have 2 oxen.'
    >>> "I have %s."%nounf('emu',1)
    'I have 1 emu.'
    >>> "I have %s."%nounf('emu',0)
    'I have 0 emus.'
    >>> nounf('dog',1,'tail')
    "1 dog's tail"
    >>> nounf('dog',2,'tail')
    "2 dogs' tails"
    """

  t,f=doctest.testmod()
  if f>0:
    sys.exit(1)

