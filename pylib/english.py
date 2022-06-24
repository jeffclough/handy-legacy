#!/usr/bin/env python3

"""
This module makes outputting sensible, correct english sentences much
more practical. For instance, as programmers, it's way too easy to write
code of this form:

  print("Found %d new customers this week"%new_cust)

The problem is when new_cust is 1, right? And we're often apathetic
enough to take a "that's good enough" attitude about this kind of thing
because we don't want to write code like this:

  if dcount==1:
    print("We snipped 1 dog's tail this week.")
  else:
    print("We snipped %d dogs' tails this week.")

But what if we could do it this way instead:

  print("We snipped %s this week."%nounf('dog',dcount,'tail'))

or

  print("Found %s this week"%nounf(
    'customer',new_cust,fmt="%(count)d new %(noun)s"
  ))

That's simple enough to do that even crusty old coders (like me) might
find themselves inclined to write code that outputs more standard
english.

That's the idea behind this module. I think we (lazy) programmers would
be happy to write better code if it were just easier.

Most of this module is linguistic "internals." See the functions at the
bottom for the practical part of the documentation.

Finally, if the English documentation for this module is confusing,
that's because English itself is a minefield of logical "gotchas." The
good news is the Python code that implements each class and funciton may
well be simpler to understand than the English text that documents it.
Don't be shy about looking at the code. :-)
"""

from typing import Callable

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Suffixer(object):
  """This is mostly a base class that provides only the most general
  functionality.

  Think of Suffixer instances, and those of its derivatives, as rules
  that know 1) how to reconize when a given word is suitable for the
  rule, and 2) how to apply either the singular or plural suffix to that
  word, depending on a given count. For example, here's a very simple
  rule set that will work on a surprising range of english nouns:

    rules=[
      Suffixer('','es',
        test=(lambda s: any([
          s.endswith(e) for e in ('s','sh','ch','x')
        ])),
        desc=('A word ending with "s", "sh", "ch", or "x" '
              'becomes plural by ending with "es" instead.')
      ),
      Suffixer('y','ies',replace=-1,
        test=(lambda s:
          len(s)>2 and s[-1]=='y' and s[-2] not in 'aeiou'
        ),
        desc=('A word ending with y becomes plural by ending with ies '
              'instead, unless preceded by a vowel.')
      ),
      Suffixer('','s'),
    ]

  Notice how the replace argument to Suffixer's constructor is used in
  rules[1]. The -1 value indicates that whatever suffix is applied to
  the root (we'll talk about root words below), it should replace the
  last character of the given root. This is helpful for pluralizing
  "penny" to "pennies".

  If no test funciton is given, but singular evaluates as True, Suffixer
  uses writes its own test function that returns true for any word
  ending with singular's value. If singular evaluates as False, Suffixer
  creates a function that always returns True.

  With that in mind, notice there's no test function given for that last
  suffixing rule, and suffix's value ('') means Suffixer uses a test
  function that always returns True. So that rule is willing to be
  applied to any root you give it. (And that's why it comes last.)

  Here's how we might express those rules in english:
  0. A word ending with "s", "sh", "ch", or "x" becomes plural by ending
     "es" instead.
  1. A word ending with y becomes plural by ending with ies instead,
     unless preceded by a vowel.
  2. All remaining words can be made plural by appending "s" to them.

  You might apply this list of suffixing rules to a given root noun like
  this:

    root="cow"
    count=5
    for r in rules:
      if r.test(root):
        word=r(root,count)
        break
    print(word)

  The result is to print the word, "cows" because the first matching
  rule was rule[2], and there were 5 cows. But if you change the noun
  in the above example to "church", you'll see "churches" printed
  because "church" matches rule[0]'s test.

  It's easy (and typical) to wrap all this in a convenient function, and
  maybe subclass Suffixer for special parts of speech, like one for
  nouns and another for verbs.

  The point of Suffixer is to provide a way to express suffixing rules
  in a way that can be specialized and extended to particular parts of
  speech in helpful ways. For instance, one of Suffixer's subclasses,
  NounSuffixer, lets the caller say whether the suffixed root should be
  expressed possessively. (See NounSuffixer for details.)"""

  def __init__(self,singular:str,plural:str,replace:int=None,test:Callable=None,desc:str=None):
    """Initialize this suffixing rule with the singular and plural
    suffixes and some other helper parameters.

    If only singular and plural are given, any singular ending is
    replaced with plural. Otherwise ...

    replace: This optional integer is the number of characters at the
    end of the root to be removed before the plural suffix is appended.

    test: This optional function takes the root as its argument and
    returns true if this suffixing rule applies to that root.

    desc: This optional string is the english description of this
    suffixing rule. If not given, the Suffixer instance will do its best
    to compose its own description."""

    self.singular=singular
    self.plural=plural
    if replace==None:
      replace=-len(singular)
      if replace==0:
        replace='append'
    self.replace=replace
    # Ignore the caller's test function if we already have a test() method.
    if not hasattr(self,'test'):
      if test:
        self.test=test
      else:
        if self.singular:
          self.test=lambda s:s.endswith(self.singular)
        else:
          self.test=lambda s:True
    if desc:
      self.desc=desc
    else:
      singular='Any word' if singular=='' else f'A word ending with "{singular}"'
      plural=f'"{plural}"'
      if replace=='append':
        self.desc=f"{singular} becomes plural by appending {plural}."
      else:
        self.desc=f"{singular} becomes plural by ending with {plural} instead."

  def __call__(self,root,count):
    "Return our root word suffixed appropriately for count's value."

    # Don't waste our time on an emptry string (or None):
    if not root:
      return ''
    # Make sure our root is a string.
    if not isinstance(root,str):
      try:
        root=str(root)
      except:
        raise ValueError(f"{root!r} (type={type(root)}) is not a string and cannot be converted to a string.")
        
    # Use count to determine which suffix to use.
    if count==1:
      suffix='' if self.replace=='append' else self.singular
    else:
      suffix=self.plural
    # Apply the suffix to our root.
    if isinstance(self.replace,int):
      word=root[:self.replace]+suffix
    else:
      word=root+suffix

    # Calling matchCapitalization() is needed because of how some of our
    # subclasses work.
    return self.matchCapitalization(root,word)

  def __repr__(self):
    """Return a string representing how this object was created."""

    #return "%s(%r,%r,replace=%r,test=%r,desc=%r)"%(
    #  self.__class__.__name__,self.singular,self.plural,self.replace,self.test,self.desc
    #)

    return
    f"{self.__class__.__name__}({self.singular!r},{self.plural!r},replace={self.replace},test={self.test},desc={self.desc})"

  def __str__(self):
    """Return this object's desc value, the one it was created with or,
    if none was given, the one it composed for itself."""

    return self.desc

  def matchCapitalization(self,root,word):
    if root[0].isupper() and not word[0].isupper():
      word=word[0].upper()+word[1:]
    return word

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NounSuffixer(Suffixer):
  '''This class builds on Suffixer, adding an understanding of possive
  nouns. It implements the rules laid out in "Chicago Manual of Style,
  17th edition."'''

  def __init__(self,singular,plural,replace=None,test=None,desc=None):
    """This consructor is just like Suffixer's constructor, but if the
    "desc" argument is not given (or None), any Suffixer-provided desc
    value is changed from "A word ..." to "A noun ..."."""

    super(NounSuffixer,self).__init__(singular,plural,replace,test,desc)
    if not desc:
      if self.desc.startswith('A word'):
        self.desc='A noun'+self.desc[6:]
      elif self.desc.startswith('Any word'):
        self.desc='Any noun'+self.desc[8:]

  def __call__(self,root,count,pos=False):
    """Return our root noun suffixed appropriatly for count's value and,
    if pos is some true value, apostrophized correctly to make it
    possessive."""

    # Let our superclass do any pluralization we might need.
    word=super(NounSuffixer,self).__call__(root,count)
    if not word:
      return word

    if pos:
      # Apply "Chicago Manual of Style, 17th edition".
      if count==1:
        # Singular posessives end with "'s", regardless of how the root ends.
        word+="'s"
      else:
        # With plural possessives, it depends on how the plural ends.
        if word[-1]=='s':
          word+="'"
        else:
          word+="'s"

    return word

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Make a map of irregularly pluralized nouns.
irregular_noun_plurals=dict(
  alumnus='alumni',
  appendix='appendices',
  atrium='atriums',
  buffalo='buffalo',
  cactus='cacti',
  child='children',
  chum='chums',
  cod='cod',
  cranium='craniums',
  deer='deer',
  die='dice',
  fish='fish',
  focus='foci',
  foot='feet',
  fungus='fungi',
  goose='geese',
  index='indices',
  louse='lice',
  moose='moose',
  mouse='mice',
  nucleus='nuclei',
  octopus='octopi',
  ox='oxen',
  person='people',
  quail='quail',
  radius='radii',
  sheep='sheep',
  shrimp='shrimp',
  stadium='stadiums',
  swine='swine',
  tooth='teeth',
  trout='trout',
  vacuum='vacuums',
  vertex='vertices',
  vortex='vortices',
)

class IrregularNounSuffixer(NounSuffixer):
  """This class builds on NounSuffixer and knows how to handle several
  common nouns with irregularly formed plurals (e.g. "die" becomes
  "dice," and "person" becomes "people"). And because this is a subclass
  of NounSuffixer, these singular or plural nouns can be posessive if
  the caller wishes it.

  IrregularNounSuffixer consults the english.irregular_noun_plurals
  dictionary to map a singular noun to the corresponding plural noun. It
  comes preloaded with several of the most commonly used nouns having
  irregularly formed plurals, but you can always add your own. For
  example, kleenex's plural is regularly kleenexes, but you can make it
  kleenices (just for fun) if you change the map like this:

      english.irregular_noun_plurals['kleenex']='kleenices'

  So we leave it to the calling code to decide things like wether the
  plural of box should be boxen. :-)

  Note this class's constructor takes no arguments. They wouldn't make
  sense here.

  """

  def __init__(self):
    # "replace=0" tells Suffixer to replace the whole word with the chosen
    # suffix, which for these irregular plurals, will be the whole singular
    # or plural form of the noun.
    super(IrregularNounSuffixer,self).__init__('','',replace=0)
    self.desc='Repalce an irregularly pluralized noun with its special plural form.'

  def __repr__(self):
    return "%s()"%self.__class__.__name__

  def __call__(self,root,count,pos=False):
    self.singular=root.lower()
    self.plural=irregular_noun_plurals[self.singular]
    word=super(IrregularNounSuffixer,self).__call__(root,count,pos)
    return word

  def test(self,root):
    return root.lower() in irregular_noun_plurals


 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Here begin some functions that wrap the classes above into something more
# immediately useful.

noun_suffixing_rules=[
  # Check for irregular cases first. The rules below don't apply to these.
  IrregularNounSuffixer(),

  # Words ending with "man" are often pluralized by replacing that with "men".
  NounSuffixer('man','men'),

  # Words ending with "is" are often pluralised by replacing that with "es".
  NounSuffixer('is','es',-2),

  # Words ending with "o" are often pluralized by adding "es".
  NounSuffixer('o','es','append'),

  # There are a few word-endings that call for "es" plural suffixes.
  NounSuffixer('','es','append',lambda s: any([s.endswith(ending) for ending in ('s','sh','ch','x')]),
    'A noun ending in "s", "sh", "ch", or "x" becomes plural by appending "es".'
  ),

  # Words ending with a consonant followed by "y" generally have "ies" plural suffixes.
  NounSuffixer('y','ies',-1,lambda s: len(s)>2 and s[-1]=='y' and s[-2] not in 'aeiou',
    'A noun ending with "y" becomes plural by ending with "ies" unless preceded by a vowel.'
  ),

  # Words ending with "f" or "fe" usually get special treatment.
  NounSuffixer('f','ves',-1,lambda s: s.endswith('f')),
  NounSuffixer('fe','ves',-2,lambda s: s.endswith('fe')),

  # Words ending with "craft" do not change when plural.
  NounSuffixer('craft','','append',desc="A nouns ending with \"craft\" doesn't change when plural."),

  # Words ending with "um" are often pluralised by replacing that with "a".
  NounSuffixer('um','a',-2,lambda s: s.endswith('um')),

  # For everything else, we'll guess that a simple "s" suffix will pluralize this noun.
  NounSuffixer('','s','append'),
]

def noun_rule_summary(width=78):
  """Return a multi-line string containing an enumerated description of
  each of our noun-suffixing rules in the order they are consulted by
  functions like nouner() and nounf()."""

  from textwrap import wrap
  out=[]
  rule_count=len(noun_suffixing_rules)
  num_width=len(str(rule_count))
  for i,r in enumerate(noun_suffixing_rules):
    out.extend(wrap(
      "%*d: %s"%(num_width,i+1,str(r)),
      width=width,
      initial_indent='',
      subsequent_indent=' '*(num_width+2)
    ))
  return '\n'.join(out)

def nouner(root,count,pos=False):
  """Return the form of the root word appropriate to the given count and
  posessiveness. The rules for doing this, which you can update if you'd
  like, are in the english.noun_suffixing_rules list. The first rule r
  for which r.test(root) method returns True is used, so the order of
  these rules is significant."""

  for r in noun_suffixing_rules:
    if r.test(root):
      word=r(root,count,pos)
      break
  return word

def nounf(root,count,pos=False,fmt=None,formatter=None):
  """This function is useful for constructing noun phrases like:

      "1 dog"
      "2 dogs"
      "1 person's hat"
      "5 people's hats"

  Return the formatted string containing nouner(root,count,pos) as
  "noun", the count as "count", and nouner(pos,count) as "pos" if pos
  evaluates to a non-false value.

  If pos is some false value, fmt defaults to "{count} {noun}".
  Otherwise, fmt defaults to "{count} {noun} {pos}", and pos is
  set to nouner(pos,count).
  
  If formatter is given, it must be a function accepting whatever value
  is in count and returning whatever value count should have in the
  returned string. One handy example is "lambda x:pnum(x)"."""

  noun=nouner(root,count,pos)
  if fmt==None:
    if pos:
      pos=nouner(pos,count)
      fmt="{count} {noun} {pos}"
    else:
      fmt="{count} {noun}"
  if formatter:
    count=formatter(count)
  return fmt.format(**locals())

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Other, english-related functions that don't fit elsewhere.

def join(seq,con=None,sep=None):
  """Return the string values in the given sequence as an English
  sequence-phrase, employing the given conjunction and seaparator when
  called for by the rules of standard English. If seq is not a sequence,
  it MUST be an object with a split() method, which will be used to
  convert it to a sequence.
  
  The conjunction defaults to 'and'. The separator defaults to a comma,
  but see SEPERATOR DEFAULTS below.

  ITEMS
    0   An empty sequence returns an empty string.

    1   A one-item sequence simply returns that item.

    2   A two-item sequence, returns a string of the form:

        "1 {con} 2"

    3+  A sequence with more than two items, returns a string of the
        form:
  
        "1, 2, ..., {con} N"
      
        The separator ALWAYS precedes the conjunction in such a case. We
        are not barbarians.

  SEPARATOR DEFAULTS:
    ,   This is the first default and is most often used.

    ;   If a comma is found in any sequence item, semicolon is the next
        default.

    (   If both a comma and semicolon are found among the sequence
    {   items, each of these separators is tried in the order shown.
    [   These are bracketing separators and indicate a bracketing pair
    <   to surround each sequence item. Each one is tried until it is
    "   found that none of them, including its closing character, exists
    '   in any sequence item.

    If, weirdly, each of these potential separators is found among the
    sequence items, then the last one is used, and this function relies
    on the caller to have balanced all such groupings within each item.
    In this last case, I'm a little tempted to raise a ValueError
    containing an admonition to restructure what the caller wishes to
    express, but this isn't Grammarly.

  BRACKETING SEPARATORS
  You can actually force the use of (parentheses), {braces}, [square] or
  <angle> brackets, or single (') or double (") quotes around each
  sequence item by giving the opening character as the separator. This
  join() function will understand that each item should begin with that
  character and then end with its mate.

  A fairly subtle differences between bracketing and non-bracketing
  separators is the former are used with sequences of two or more items
  while the latter come into play only when there are three or more
  items.

    > english.join(('a and b',),sep='(')
    'a and b'

    > english.join(('a and b','c or d'),sep='(')
    '(a and b) and (c or d)'

    > english.join(('a and b','c or d','e but not f'),sep='(')
    '(a and b), (c or d), and (e but not f)'

  When using quotes as the separator, we do our best to make sure the
  commas precede each closing quote.
    
     > print(english.join(('a and b','c or d','e but not f'),sep='"'))
    "a and b," "c or d," and "e but not f"

  But we're smart enough not to double up commas:

    > print(english.join(('weird,','maybe wrong','¯\_(ツ)_/¯'),'but','"'))
    "weird,", "maybe wrong," but "¯\_(ツ)_/¯"

  All this can produce some odd-looking output, but it's as right as we
  know how to make it:

    > print(english.join(list(',;(){}[]<>')))
    ",", ";," "(," ")," "{," "}," "[," "]," "<," and ">"

  Notice the separator defaulted to the double quote because that's the
  next separator in line after the '<' default separator, which one of
  the sequence items contained."""

  # Values of sep and require openning and closing characters.
  pairs={
    '(':')',
    '{':'}',
    '[':']',
    '<':'>',
    '"':'"',
    "'":"'",
  }

  if not isinstance(seq,(dict,list,tuple)):
    if hasattr(seq,'split') and callable(seq.split):
      seq=seq.split()
    try:
      seq=tuple(seq)
    except:
      raise TypeError(f"{__name__}.join() requires a sequnece or something with a split() method.")
  if len(seq)==0: return ''
  if len(seq)==1: return str(seq[0])
  if con==None:
    con='and'
  if sep==None:
    if any([',' in item for item in seq]):
      if any([';' in item for item in seq]):
        for o,c in pairs.items():
          if not any([o in item or c in item for item in seq]):
            break
        sep=o
      else:
        sep=';'
    else:
      sep=','
  if sep in pairs:
    o,c=sep,pairs[sep] # Set the opening and closing characters.
  else:
    o=c=None
  if len(seq)==2:
    if o: # This is the only time separators apply to a 2-item sequence.
      # Handle bracketing separators for 2 items.
      return f"{o}{seq[0]}{c} {con} {o}{seq[1]}{c}"
    # Handle non-bracketing separators for 2 items.
    return f"{seq[0]} {con} {seq[1]}"
  # We know we're dealing with at least three items after this point.
  if o:
    if o in ('"',"'"):
      # Ensure commas precede closing quotes whenever possible.
      return f"{' '.join([o+x+((c+',') if x.endswith(',') else (','+c)) for x in seq[:-1]])} {con} {o}{seq[-1]}{c}"
    # Hand non-quote, bracketing separators.
    return f"{' '.join([o+x+c+',' for x in seq[:-1]])} {con} {o}{seq[-1]}{c}"
  # Handle non-bracketing separators.
  return f"{' '.join([x+sep for x in seq[:-1]])} {con} {seq[-1]}"

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Human beings need only so many significant digits. The SigDig class extends
# float with a __str__() method that respects that.
#

from math import log10

def pnum(val,sep=',3',digits=3):
  """People can have a hard time interpreting large numbers at a glance,
  and many places past the decimal point are typically ignored. This
  function accepts a numeric value and some formatting parameters and
  returns the value as a string. This will only ever be used to limit
  how many places to the right of the decimal point to express. Digits
  to the left are always expressed.

  val     The numeric (int, long, or float) to be expressed as a string.
  sep     Specifies how group and separate digits. The first character
          is the seperator, and the optional remainder of the string is
          the number of digits per group. If sep is None, no separation
          is performed. (default: ',3')
  digits  The minimum number of significant digits to express, which may
          be on either side of the decimal. (default: 3)
  """

  assert isinstance(val,(int,float)),"pnum()'s val must have a numeric type."
  assert isinstance(digits,int) and digits>=0,"pnum()'s digits must be a non-negative integer."
  #debug("pnum(%r,%r,%r)"%(val,sep,digits)).indent()

  # Parse our sep argument into sep and dist values.
  if sep:
    if len(sep)>1:
      dist=int(sep[1:])
      sep=sep[0]
    else:
      dist=3

  # Remember and remove any sign on the front of our value.
  sign=('','-')[val<0]
  if sign:
    val=-val

  # Decide how many decimal places we need.
  if val==0:
    intdigs=1
  else:
    intdigs=int(log10(val))+1
  prec=digits-intdigs
  if prec<0:
    prec=0
  # In case rounding chnages the number of digits to the left of the decimal:
  sval='%0.*f'%(prec,val)
  val=float(sval)

  # Get our integer digits and separate them into dist-character groups.
  s=str(int(val))
  d=len(s)
  if sep and d>dist:
    l=[x for x in [s[i:i+dist] for i in range(d-dist,-1,-dist)]+[s[:d%dist]] if x]
    l.reverse()
    s=sep.join(l)

  # Add back any places past the decimal.
  d=sval.find('.')
  if d>=0:
    s+=sval[d:].rstrip('.0')

  # Put our value sign back.
  s=sign+s

  #debug.undent()("returning %r"%(s,))
  return s

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# HumanBytes and its subclasses are for expressing quantities of bytes in a
# form that's easier for a human to read than "459892347923 bytes." It's much
# easier to read "459.89 GB."
#

class HumanBytes(object):
  """HumanBytes and its subclasses are for expressing quantities of
  bytes in a form that's easier for people to read than "459892347923
  bytes." It's much easier to read "459.89 GB."
  """

  def __init__(self,divisor,units,formatter=None):
    """Initialize this HumanBytes object with enough information for it
    to format itself.

    divisor    The number of bytes being expressed is repeatedly divided
               by this divisor until that value falls below the divisor
               or we run out of units strings.
    units      A sequence of strings expressing increasing units of
               bytes.
    formatter  Optionally, a function accepting a numeric value and
               returning that number formatted in a string as desired by
               the caller."""

    self.divisor=float(divisor)
    self.units=tuple(units)
    if formatter==None:
      self.formatter=lambda x:pnum(x,sep=None,digits=3)
    else:
      self.formatter=formatter

  def __repr__(self):
    return '%s(%d,%r,%r)'%(__class__.__name__,divisor,units,formatter)

  def _findUnits(self,val):
    """FOR INTERNAL USE ONLY: Divide val by our divisor as many times as
    needed to find the appropriate units to use with it. Return a tuple
    of the resulting val value (after repeated division) and the units
    string for that new value."""

    #debug("%s._findUnits(%r)"%(self.__class__.__name__,val)).indent()
    # Find the right units to use, dividing val by our divisor as we go.
    for i in range(len(self.units)):
      if val<self.divisor:
        break
      if val>=self.divisor:
        val/=self.divisor
    else:
      i-=1

    #debug.undent()("returning (%r,%r)"%(val,self.units[i]))
    return val,self.units[i]

  def format(self,val,formatter=None):
    """Divide val by this object's divisor until its value falls below
    that divisor, incrementing the units as we go. Return the formatted
    string."""

    #debug("%s.format(%r,%r)"%(self.__class__.__name__,val,formatter)).indent()
    val,units=self._findUnits(val)
    if formatter==None:
      #debug("setting formatter=%r"%(self.formatter,))
      formatter=self.formatter
    #debug("val=%r, units=%r"%(val,units))
    s=nounf(units,val,formatter=formatter)
    #debug.undent()("returning %r"%(s,))
    return s

class DecimalHumanBytes(HumanBytes):
  """DecimalHumanBytes instances use a divisor of 10**3 to express a
  given number of bytes in a form easy for humans to interpret. These
  are the available units, while are expressed as plural when
  appropriate:

      byte
      kilobyte
      megabyte
      gigabyte
      terabyte
      petabyte
      exabyte
      zettabyte
      yottabyte"""

  def __init__(self,formatter=None):
    """Initialize this DecimalHumanBytes object, optionally providing a
    formatter function that takes a numeric value and returns that
    number formatted in a string."""

    super(self.__class__,self).__init__(1000,(
      'byte','kilobyte','megabyte','gigabyte','terabyte','petabyte','exabyte','zettabyte','yottabyte'
    ),formatter=formatter)

class BinaryHumanBytes(HumanBytes):
  """BinaryHumanBytes instances use a divisor of 2**10 to express a
  given number of bytes in a form easy for humans to interpret. These
  are the available units, while are expressed as plural when
  appropriate:

      byte
      kibibyte
      mebibyte
      gibibyte
      tebibyte
      pebibyte
      exbibyte
      zebibyte
      yobibyte
"""

  def __init__(self,formatter=None):
    """Initialize this BinaryHumanBytes object, optionally providing a
    formatter function that takes a numeric value and returns that
    number formatted in a string."""

    super(self.__class__,self).__init__(1024,(
      'byte','kibibyte','mebibyte','gibibyte','tebibyte','pebibyte','exbibyte','zebibyte','yobibyte'
    ),formatter=formatter)

class DecHumanBytes(HumanBytes):
  """DecHumanBytes instances use a divisor of 10**3 to express a given
  number of bytes in a form easy for humans to interpret. These are the
  available units:

      B
      KB
      MB
      GB
      TB
      PB
      EB
      ZB
      YB"""

  def __init__(self,formatter=None):
    """Initialize this DecHumanBytes object, optionally providing a
    formatter function that takes a numeric value and returns that
    number formatted in a string."""

    super(self.__class__,self).__init__(1000,(
      'B','KB','MB','GB','TB','PB','EB','ZB','YB'
    ),formatter=formatter)

  def format(self,val,formatter=None):
    """Divide val by this object's divisor until its value falls below
    that divisor, incrementing the units as we go. Return the formatted
    string."""

    if formatter==None:
      formatter=self.formatter
    val,units=self._findUnits(val)
    return "{0} {1}".format(formatter(val),units)

class BinHumanBytes(HumanBytes):
  """BinHumanBytes instances use a divisor of 10**3 to express a given
  number of bytes in a form easy for humans to interpret. These are the
  available units:

      B
      KB
      MB
      GB
      TB
      PB
      EB
      ZB
      YB"""

  def __init__(self,formatter=None):
    """Initialize this BinHumanBytes object, optionally providing a
    formatter function that takes a numeric value and returns that
    number formatted in a string."""

    super(self.__class__,self).__init__(1024,(
      'B','KB','MB','GB','TB','PB','EB','ZB','YB'
    ),formatter=formatter)

  def format(self,val,formatter=None):
    """Divide val by this object's divisor until its value falls below
    that divisor, incrementing the units as we go. Return the formatted
    string."""

    if formatter==None:
      formatter=self.formatter
    val,units=self._findUnits(val)
    return "{0} {1}".format(formatter(val),units)

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# A subclass of str that ensures "Title Case" capitalization.

class TitleCase(str):
  """A TitleCase value is just like a str value, but it gets title-cased
  upon creation. (And since Python strings are immutable, forevermore
  shall it remain.)"""

  #
  # There's interesting material on this topic at the "Title Case Converter"
  # page at https://titlecaseconverter.com.
  #
  # The implementation below is comically simplistic by comparison. If you need
  # something less riddled with caveats, feel free to use this as a starting
  # point. :-)
  #

  coordinating_conjunctions='and but for nor or so yet'.split()


  # Articles, conjunctions, and prepositions are always lower-cased, unless
  # they are the first or last word of the title.
  lc_words=set("""
    a an the
    and but for nor or so yet
    as at by for in of off on to up via
  """.split())

  def __new__(self,value=''):
    """Capitalize each word in value unless it's in TitleCase.lc_words,
    unless it's the first or last word in the string. We ALWAYS
    capitalize first and last words."""

    words=[w for w in value.lower().split() if w]
    last=len(words)-1
    for i in range(last+1):
      if i in (0,last) or words[i] not in self.lc_words:
        words[i]=words[i].capitalize()
    return str.__new__(self,' '.join(words))

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Test code. The code below runs only run if this module is run as the main
# module.

if __name__=='__main__':
  import doctest,os,sys

  if os.path.isdir(os.path.join(os.path.basename(sys.argv[0]),'pylib')):
    # Make sure we're working with the local modules.
    sys.path.insert(0,os.path.join(os.path.basename(sys.argv[0]),'pylib'))

  def tests():
    """
    >>> #
    >>> # Testing TitleCase
    >>> # It's a class, not a function. But it does double-duty.
    >>> #
    >>> TitleCase('')
    ''
    >>> TitleCase('a fine kettle of fish')
    'A Fine Kettle of Fish'
    >>> TitleCase('    another     fine     kettle     of     fish    ')
    'Another Fine Kettle of Fish'
    >>> t=TitleCase("to remember what's yet to come")
    >>> t
    "To Remember What's yet to Come"
    >>> t.split()
    ['To', 'Remember', "What's", 'yet', 'to', 'Come']
    >>> str(type(t)).endswith(".TitleCase'>")
    True
    >>> TitleCase('from in into of on onto than till to')
    'From in Into of on Onto Than Till To'
    >>> #
    >>> # Testing nouner()
    >>> #
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
    >>> nouner('potato',58)
    'potatoes'
    >>> #
    >>> # Testing nounf()
    >>> #
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
    >>> "I stepped on %s."%nounf('person',3,'foot')
    "I stepped on 3 people's feet."
    >>> "I made %s today."%nounf('fireman',3,'hat')
    "I made 3 firemen's hats today."
    >>> "There were %s in the garden this year."%nounf('potato',58)
    'There were 58 potatoes in the garden this year.'
    >>> #
    >>> # Testing english.join()
    >>> #
    >>> join(('',))
    ''
    >>> join(('this',))
    'this'
    >>> join(('this','that'))
    'this and that'
    >>> join(('this','that','the other'))
    'this, that, and the other'
    >>> join(('this','that','the other'),con='or')
    'this, that, or the other'
    >>> flag_colors=(
    ...   ('red','white','blue'),
    ...   ('green','red','white'),
    ...   ('red','white'),
    ... )
    >>> flags=tuple([join(f) for f in flag_colors])
    >>> join(flags[:2],con='or')
    'red, white, and blue or green, red, and white'
    >>> join(flags,con='or')
    'red, white, and blue; green, red, and white; or red and white'
    >>> flags=tuple([join(f,sep=';') for f in flag_colors])
    >>> join(flags,con='or')
    'red; white; and blue, green; red; and white, or red and white'
    >>> join(('the comma (,) is nice','the semi-colon (;) should be used when needed','combining them can be tricky'),'but')
    '{the comma (,) is nice}, {the semi-colon (;) should be used when needed}, but {combining them can be tricky}'
    >>> join('apples oranges')
    'apples and oranges'
    >>> join('apples oranges bananas','or','<')
    '<apples>, <oranges>, or <bananas>'
    >>> join(('a and b',),sep='(')
    'a and b'
    >>> join(('a and b','c or d'),sep='(')
    '(a and b) and (c or d)'
    >>> join(('a and b','c or d','e but not f'),sep='(')
    '(a and b), (c or d), and (e but not f)'
    >>> print(join(('weird,','maybe wrong','¯\_(ツ)_/¯'),'but','"'))
    "weird,", "maybe wrong," but "¯\_(ツ)_/¯"
    >>> #
    >>> # Test Suffixer's error handling.
    >>> #
    >>> x=Suffixer(('this is also','a mistake'),None)
    >>> join(x)
    Traceback (most recent call last):
      ...
    TypeError: __main__.join() requires a sequnece or something with a split() method.
    >>> #
    >>> # Test pnum().
    >>> #
    >>> pnum(1.0)
    '1'
    >>> pnum(12)
    '12'
    >>> pnum(123)
    '123'
    >>> pnum(1234)
    '1,234'
    >>> pnum(12345)
    '12,345'
    >>> pnum(123456)
    '123,456'
    >>> pnum(1234567)
    '1,234,567'
    >>> pnum(1234567,sep='.4')
    '123.4567'
    >>> pnum(-12345678,sep='.4')
    '-1234.5678'
    >>> pnum(1.23456)
    '1.23'
    >>> pnum(1.23456,digits=4)
    '1.235'
    >>> #
    >>> # Test HumanBytes and its subclasses.
    >>> #
    >>> h=DecimalHumanBytes()
    >>> h.format(0)
    '0 bytes'
    >>> h.format(1)
    '1 byte'
    >>> h.format(2)
    '2 bytes'
    >>> h.format(999)
    '999 bytes'
    >>> h.format(1000)
    '1 kilobyte'
    >>> h.format(1250)
    '1.25 kilobytes'
    >>> h.format(9000)
    '9 kilobytes'
    >>> h.format(10000)
    '10 kilobytes'
    >>> h.format(12345)
    '12.3 kilobytes'
    >>> h.format(12345,formatter=lambda x:pnum(x,digits=4))
    '12.35 kilobytes'
    >>> h.format(10**9)
    '1 gigabyte'
    >>> h.format(459892347923)
    '460 gigabytes'
    >>> h=DecHumanBytes()
    >>> h.format(0)
    '0 B'
    >>> h.format(1)
    '1 B'
    >>> h.format(2)
    '2 B'
    >>> h.format(999)
    '999 B'
    >>> h.format(1000)
    '1 KB'
    >>> h.format(1250)
    '1.25 KB'
    >>> h.format(9000)
    '9 KB'
    >>> h.format(10000)
    '10 KB'
    >>> h.format(12345)
    '12.3 KB'
    >>> h.format(12345,formatter=lambda x:pnum(x,digits=4))
    '12.35 KB'
    >>> h.format(10**9)
    '1 GB'
    >>> h.format(459892347923)
    '460 GB'
    >>> h=BinaryHumanBytes()
    >>> h.format(0)
    '0 bytes'
    >>> h.format(1)
    '1 byte'
    >>> h.format(2)
    '2 bytes'
    >>> h.format(1023)
    '1023 bytes'
    >>> h.format(1024)
    '1 kibibyte'
    >>> h.format(1280)
    '1.25 kibibytes'
    >>> h.format(9216)
    '9 kibibytes'
    >>> h.format(10240)
    '10 kibibytes'
    >>> h.format(12544)
    '12.2 kibibytes'
    >>> h.format(12544,formatter=lambda x:pnum(x,digits=4))
    '12.25 kibibytes'
    >>> h.format(2**30)
    '1 gibibyte'
    >>> h.format(460*(2**30)-1)
    '460 gibibytes'
    >>> h=BinHumanBytes()
    >>> h.format(0)
    '0 B'
    >>> h.format(1)
    '1 B'
    >>> h.format(2)
    '2 B'
    >>> h.format(1023)
    '1023 B'
    >>> h.format(1024)
    '1 KB'
    >>> h.format(1280)
    '1.25 KB'
    >>> h.format(9216)
    '9 KB'
    >>> h.format(10240)
    '10 KB'
    >>> h.format(12544)
    '12.2 KB'
    >>> h.format(12544,formatter=lambda x:pnum(x,digits=4))
    '12.25 KB'
    >>> h.format(2**30)
    '1 GB'
    >>> h.format(460*(2**30)-1)
    '460 GB'
    """

  import argparse

  ap=argparse.ArgumentParser(description="Test the english.py module in some way.")
  ap.add_argument('--con',action='store',help="The conjunction to use with --join.")
  ap.add_argument('--count',action='store',default=1,help="Use this number when deciding whether a word should be singular or plural.")
  ap.add_argument('--debugger',action='store_true',help="Engage pdb within this script once we get through the setup. This is not for the uninitiated. See https://docs.python.org/3/library/pdb.html#debugger-commands for a command summary.")
  ap.add_argument('--join',action='store_true',help="Join our WORDs into an english list.")
  ap.add_argument('--noun',action='store_true',help="One or more (separated by spaces or commas) nouns to test.")
  ap.add_argument('--noun-phrase',action='store_true',help="Use --count and (optionally) --obj to output the corresponding noun phrase for every WORD argument on the command line.")
  ap.add_argument('--noun-rules',action='store_true',help="List the rules for making plural nouns.")
  ap.add_argument('--obj',action='store',help="The object to be used with nouner() and nounf().")
  ap.add_argument('--sep',action='store',help="The separator to use with --join.")
  ap.add_argument('--test',action='store_true',help="Run all internal tests.")
  ap.add_argument('words',metavar='WORD',action='store',nargs='*',help="List of terms to act upon.")
  opt=ap.parse_args()

  if opt.debugger:
    # Start Python's debugger.
    import pdb
    pdb.set_trace()

  # Handle any options that require no WORD arguments.
  if opt.noun_rules:
    print(noun_rule_summary())
  elif opt.test:
    f,t=doctest.testmod(report=False)
    if f>0:
      print('*********************************************************************\n')
    print("Passed %d of %s."%(t-f,nounf('test',t)))
    sys.exit((1,0)[f==0])
  else:
    if not opt.words:
      print("At lease one WORD arguemnt must be given.")
      ap.print_help()
      sys.exit(1)
    # Options requiring one or more WORD arguments are handled below.
    if opt.join:
      print(join(opt.words,con=opt.con,sep=opt.sep))
    elif opt.noun:
      for w in opt.words:
        print(f"{w}:\n    {nounf(w,1,opt.obj)}\n    {nounf(w,2,opt.obj)}")
    elif opt.noun_phrase:
      for w in opt.words:
        print(nounf(w,opt.count,opt.obj))
    else:
      ap.print_help()
