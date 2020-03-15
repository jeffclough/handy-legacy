#!/usr/bin/env python


__all__=['Rule','Suffix','Declension','NounDeclension','VerbDeclension']
import sys

try:
  # We might need to use a namedtuple under Python versions < 2.6.
  from collections import namedtuple
  Rule=namedtuple('Rule','test suffix')
  Suffix=namedtuple('Suffix','singular plural replace')
except:
  # Once we know what the above namedtuples should look like, generate
  # their definitions under Python 2.7 and paste in here. For now, we'll
  # simply re-raise the exception.
  raise

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Declension(object):

  @classmethod
  def findSuffixFor(cls,root):
    """Return the appropriate Suffix object for this root word. If no
    matching rule is found, return the last rule defined for this
    class."""

    # Get the Suffix structure to express singular and plural forms for root.
    suffix=cls._number_rules[-1].suffix
    for r in cls._number_rules:
      if r.test(root):
        if hasattr(r.suffix,'__call__'):
          suffix=r.suffix(root)
        else:
          suffix=r.suffix
        break
    return suffix

  @classmethod
  def format(cls,root,count,fmt="%(n)d %(w)s"):

    word=cls.decline(root,count)
    return fmt%(dict(w=word,n=count))

  @classmethod
  def decline(root,count,suffixes=None):
    """Given a number in root, return the proper English declension of
    the word in the root argument. If a suffixes argument is given, it
    MUST be a sequence where the first item is the singular suffix and
    the second is the plural suffix"""

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Set up some rules for "pluralizing" nouns.
#

#
# These words don't pluralize according to "the rules." Feel free to add
# your own. Use this as a template:
#
#   Declension.NounDeclension._irregular_plurals['some_word']=Suffix(...)
#
# For example, a helpful Suffix instance for "index" would be:
#
#   Suffix('index','indices',-6)
#
# _irregular_plurals[word] --> Suffix instance for that word.
#
_irregular_plurals=dict([(s,Suffix(s,p,-len(s))) for s,p in (
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
)])
del s,p # Don't leave these lying around.

_number_rules_for_nouns=[
  # Check for irregular cases first.
  Rule(
    (lambda s: s in _irregular_plurals),
    lambda s: _irregular_plurals[s]
  ),
  # Words ending with "is" are often pluralised by replacing that with "es".
  Rule(
    (lambda s: s.endswith('is')),
    Suffix('is','es',-2)
  ),
  # There are a few word-endings that call for "es" plural suffixes.
  Rule(
    (lambda s: any([s.endswith(ending) for ending in ('s','sh','ch','x')])),
    Suffix('','es',None)
  ),
  # Words ending with a consonant followed by "y" generally have "ies" plural suffixes.
  Rule(
    (lambda s: len(s)>2 and s[-1]=='y' and s[-2] not in 'aeiou'),
    Suffix('y','ies',-1)
  ),
  # Words ending with "f" or "fe" usually get special treatment.
  Rule (
    (lambda s: s.endswith('f')),
    Suffix('f','ves',-1)
  ),
  Rule (
    (lambda s: s.endswith('fe')),
    Suffix('fe','ves',-2)
  ),
  # Words ending with "um" are often pluralised by replacing that with "a".
  Rule(
    (lambda s: s.endswith('um')),
    Suffix('um','a',-2)
  ),
  # For everything else, we'll guess that a simple "s" suffix will pluralize this noun.
  Rule(
    (lambda s: True),
    Suffix('','s',None)
  ),
]

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NounDeclension(Declension):
  """
  >>> noun=NounDeclension()
  >>> noun.decline('alumnus')
  'alumnus'
  >>> noun.decline('Alumnus')
  'Alumnus'
  >>> noun.decline('alumnus',5)
  'alumni'
  >>> noun.decline('Alumnus',5)
  'Alumni'
  >>> noun.decline('index',5)
  'indices'
  >>> noun.decline('Index',5)
  'Indices'
  >>> noun.decline('watch',1)
  'watch'
  >>> noun.decline('watch',2)
  'watches'
  >>> noun.decline('penny',1)
  'penny'
  >>> noun.decline('penny',2)
  'pennies'
  >>> noun.decline('elf',1)
  'elf'
  >>> noun.decline('elf',2)
  'elves'
  >>> noun.decline('life',1)
  'life'
  >>> noun.decline('life',2)
  'lives'
  >>> noun.decline('axis',1)
  'axis'
  >>> noun.decline('axis',2)
  'axes'
  >>> noun.decline('curiculum',1)
  'curiculum'
  >>> noun.decline('curiculum',2)
  'curicula'
  >>> noun.decline('dog',1)
  'dog'
  >>> noun.decline('dog',2)
  'dogs'
  >>> noun.format('dog',5)
  '5 dogs'
  >>> noun.decline('cat',1,suffix=Suffix('n','p',-1))
  'can'
  >>> noun.decline('cat',2,suffix=Suffix('n','p',-1))
  'cap'
  >>> "I have %s."%noun.format('fish',1)
  'I have 1 fish.'
  >>> "I have %s."%noun.format('fish',2)
  'I have 2 fish.'
  >>> "I have %s."%noun.format('ox',1)
  'I have 1 ox.'
  >>> "I have %s."%noun.format('ox',2)
  'I have 2 oxen.'
  >>> "I have %s."%noun.format('emu',1)
  'I have 1 emu.'
  >>> "I have %s."%noun.format('emu',0)
  'I have 0 emus.'
  """

  _number_rules=_number_rules_for_nouns

  @classmethod
  def decline(cls,root,count=1,possessive=False,suffix=None):
    # Don't waste our time on an empty string (or None).
    if not root:
      return ''

    # Validate root's type.
    if not isinstance(root,basestring):
      try:
        root=str(root)
      except:
        super_cls=super(NounDeclension,cls)
        raise ValueError("%s.%s.decline() requires its first argument to be a string or an object that can be made into one, not %r (of type %s)."%(super_cls.__name__,cls.__name__,root,type(root)))

    # Remember our plurality.
    plural=count!=1

    # If the caller didn't give us a Suffix structure to apply, take a guess at one.
    if suffix==None:
      suffix=cls.findSuffixFor(root.lower()) # The lower-case here is important.

    # Construct our noun, assuming it's not possessive.
    if suffix.replace==None:
      word=root+suffix[count!=1]
    else:
      word=root[:suffix.replace]+suffix[plural]

    # Match capitalization 
    if root[0].isupper() and not word[0].isupper():
      word=word[0].upper()+word[1:]

    # Plural possessives (usually


    return word

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class VerbDeclension(Declension):
  pass

if __name__=='__main__':
  import doctest,sys
  from pprint import pprint

  t,f=doctest.testmod()
  if f>0:
    sys.exit(1)
