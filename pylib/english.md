# english.py

## Quick Start

### Handling Singular and Plural Nouns

Example:

~~~python3
from english import nounf

def story(count):
    print("I met %s today."%nounf('person',count))
    print("%s wore %s."%(nounf('person',count),nounf('hat',count)))
    print("I stole %s."%(nounf('person',count,'hat')))
    print()

story(1)
story(3)
~~~

Output:

    I met 1 person today.
    1 person wore 1 hat.
    I stole 1 person's hat.

    I met 3 people today.
    3 people wore 3 hats.
    I stole 3 people's hats.

### Expressing Lists of Items in English

Example:

~~~python3
from collections import namedtuple
import english

Flag=namedtuple('Flag',('country','colors'))

flags=(
    Flag('USA',('red','white','blue')),
    Flag('Albania',('red','black')),
    Flag('Finland',('blue','white')),
)

for f in flags:
    print(f"{f.country}'s flag is {english.join(f.colors)}.")
~~~~

Output:

    USA's flag is red, white, and blue.
    Albania's flag is red and black.
    Finland's flag is blue and white.

## Overview
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
Don't be shy about looking at the code. 😄

