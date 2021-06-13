#!/usr/bin/env python3

"""
This module provides a very simple way to translate text into any of
several dialects of phonetic alphabet.
"""

dialect=dict(
  nato=dict([(w[0].lower(),w) for w in 'Alpha Bravo Charlie Delta Echo Foxtrot Golf Hotel India Juliet Kilo Lima Mike November Oscar Papa Quebec Romeo Sierra Tango Uniform Victor Whiskey Xray Yankee Zulu'.split()]),
  raf=dict([(w[0].lower(),w) for w in 'Affirm Baker Charlie Dog Easy Fox George How Interrogatory Johny King Love Mike Nab Oboe Prep Queen Roger Sugar Tare Uncle Victor William X-ray Yoke Zebra'.split()]),
  police=dict([(w[0].lower(),w) for w in 'Adam Boy Charlie David Edward Frank George Henry Ida John King Lincoln Mary Nora Ocean Peter Queen Robert Sam Tom Union Victor William X-ray Young Zebra'.split()]),
  us=dict([(w[0].lower(),w) for w in 'Able Baker Charlie Dog Easy Fox George How Item Jig King Love Mike Nan Oboe Peter Queen Roger Sugar Tare Uncle Victor William X-ray Yoke Zebra'.split()]),
  wu=dict([(w[0].lower(),w) for w in 'Adams Boston Chicago Denver Easy Frank George Henry Ida John King Lincoln Mary NewYork Ocean Peter Queen Roger Sugar Thomas Union Victor William X-ray Young Zero'.split()])
)

dialects=sorted(dialect.keys())

def wordify(s,**kwargs):
  """Return the phonetic-alphabetic translation of the given string.

  Keyword Arguments:
  dialect - Valid values are nato (the default), raf, police, us, and wu.
  ignore_case - True if all characters are to be regarded as lower case."""

  d=dialect[kwargs.get('dialect','nato')]
  ic=kwargs.get('ignore_case',False)

  output=[]
  for word in s.split():
    for ch in word:
      w=d.get(ch.lower(),ch)
      if not ic and ch.isupper():
        w=w.upper()
      output.append(w)
  return ' '.join(output)

if __name__=='__main__':
  import argparse,os,sys
  import english

  # The name of this executable decides the default dialect, if possible.
  prog=os.path.basename(sys.argv[0])
  default_dialect=prog if prog in dialects else 'nato'

  ap=argparse.ArgumentParser(
    #formatter_class=argparse.RawDescriptionHelpFormatter,
    description=f"""This program spells words in a phonetic alphabet. For
    instance, in the NATO dialect, 'a' becomes 'Alpha', b becomes 'Bravo', and
    so on. The phonetic spelling of each word is written to one line of
    standard output. Supported dialects are {english.join(dialects)}."""
  )
  ap.add_argument('-d','--dialect',metavar='D',choices=dialects,default=default_dialect,help="The phonetic dialect to be used. (default: %(default)s)")
  ap.add_argument('-i','--ignore-case',action='store_true',help="Ignore the case of the input. By default, F ==> FOXTROT while f ==> Foxtrot, for example.")
  ap.add_argument('-l','--list',action='store_true',default=False,help="Just list the default or given phonetic dialect.")
  ap.add_argument('-L','--list-all',action='store_true',default=False,help="List words from all available dialects in tabular form.")
  ap.add_argument('text',action='store',nargs='*',help="One or more words to output phonetically.")
  opt=ap.parse_args()
  opt.text=' '.join(opt.text) # Convert this list to a string.
  if opt.dialect not in dialects:
    print(f"{prog}: Unknown dialect {opt.dialect}",file=sys.stderr)
    sys.exit(1)

  if opt.list_all:
    colsep='  '
    pd=dialect
    # Compute the width needed for each dialect column.
    wid=[0]*len(dialects)
    for i in range(len(wid)):
      wid[i]=max([len(w) for w in list(pd[dialects[i]].values())+[dialects[i]]])
    # Output the table of phonetic dialects.
    print('   %s'%(colsep.join(['%-*s'%(wid[i],dialects[i]) for i in range(len(dialects))])))
    print('   %s'%(colsep.join(['%s'%('-'*wid[i]) for i in range(len(dialects))])))
    for ch in sorted(pd[dialects[0]].keys()):
      print('%s: %s'%(ch,colsep.join(['%-*s'%(wid[i],pd[dialects[i]][ch]) for i in range(len(dialects))])))
    sys.exit(0)
  elif opt.list:
    # Print the default or specified dialect.
    d=dialect[opt.dialect]
    for ch in sorted(d.keys()):
      print('%s: %s'%(ch,d[ch]))
    sys.exit(0)

  if opt.text:
    print(wordify(opt.text,dialect=opt.dialect,ignore_case=opt.ignore_case))
  else:
    # We'll read standard input, if any, rather than use command line arguments.
    if os.isatty(sys.stdin.fileno()):
      ap.print_help() # Show usage message.
      sys.exit(0)
    else:
      for line in sys.stdin:
        print(wordify(line))
