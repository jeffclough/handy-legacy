import optparse,os,sys

dialect=dict(
  nato=dict([(w[0].lower(),w) for w in 'Alpha Bravo Charlie Delta Echo Foxtrot Golf Hotel India Juliet Kilo Lima Mike November Oscar Papa Quebec Romeo Sierra Tango Uniform Victor Whiskey Xray Yankee Zulu'.split()]),
  raf=dict([(w[0].lower(),w) for w in 'Affirm Baker Charlie Dog Easy Fox George How Interrogatory Johny King Love Mike Nab Oboe Prep Queen Roger Sugar Tare Uncle Victor William X-ray Yoke Zebra'.split()]),
  police=dict([(w[0].lower(),w) for w in 'Adam Boy Charlie David Edward Frank George Henry Ida John King Lincoln Mary Nora Ocean Peter Queen Robert Sam Tom Union Victor William X-ray Young Zebra'.split()]),
  us=dict([(w[0].lower(),w) for w in 'Able Baker Charlie Dog Easy Fox George How Item Jig King Love Mike Nan Oboe Peter Queen Roger Sugar Tare Uncle Victor William X-ray Yoke Zebra'.split()]),
  wu=dict([(w[0].lower(),w) for w in 'Adams Boston Chicago Denver Easy Frank George Henry Ida John King Lincoln Mary NewYork Ocean Peter Queen Roger Sugar Thomas Union Victor William X-ray Young Zero'.split()])
)

dialects=' '.join(sorted(dialect.keys()))

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
