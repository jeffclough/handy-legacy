#!/usr/bin/env python

##
## If make this file a Python module by renaming it to have a .py extension,
## you can use it to as a CCSO Python API.
##
## See the code at the bottom of this file for examples of how to use the
## Search and Entry classes defined below.
##

import re,socket

re_line_parser=re.compile(r'(?P<more>-)?(?P<code>\d+):(?P<message>.*)')
re_message_parser=re.compile(r'(?P<item>\d+):\s*(?P<field>[^:]+):\s*(?P<value>.*)')

class Error(Exception):
  "The classes in this module raise this type of exception."

  pass

class Entry(object):
  """This thin wrapper around a dictionary holds a single item's data and
  and is returned from the Search.responses() generator function."""

  def __init__(self,field_dict):
    self.d=field_dict

  def __str__(self):
    "Return a multi-line string expressing the values in this entry."

    fields=self.d.keys()
    fields.sort()
    w=max([len(x) for x in fields])
    return '\n'.join(['%*s: %s'%(w,f,self.d[f]) for f in fields])

  def __repr__(self):
    return '%s(%s)'%(
      self.__class__.__name__,
      '{%s}'%', '.join(['%r: %r'%(f,self.d[f]) for f in sorted(self.d.keys())])
    )

class Search(object):
  """Execute a search on the given query to the given host and port. The
  timeout argument is in seconds and is as long as we'll wait for more
  data from the server. It should be greater than 0."""

  def __init__(self,host,query,port=105,timeout=0.2):
    self.host=host
    self.port=port
    self.query=query
    self.timeout=timeout
    self.sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    self.sock.connect((self.host,self.port))
    self.sock.send(self.query+'\n')
    self.sock.settimeout(self.timeout)
    self.file=self.sock.makefile('r')
    self.result=None

  def responses(self):
    """This generator function provides an iterator through the items in
    the server's response. It yields one Entry object per iteration."""

    prev_item=0
    d={}
    try:
      for line in self.file:
        m=re_line_parser.match(line)
        if not m:
          raise Error('Bad response line: %r\n'%(line,))
        more,code,message=m.groups()
        code=int(code)
        if code!=200:
          raise Error('Error %d, %s\n'%(code,message))
        m=re_message_parser.match(message)
        if not m:
          self.result=(code,message)
          break
        item,field,value=m.groups()
        item=int(item)
        if item>prev_item:
          # If this is a new item, return (yield) the old one and start the next.
          if d:
            yield Entry(d)
            d={}
          prev_item=item
        # Add this line to the current dictionary.
        d[field]=value
    except socket.timeout:
      pass
    if d:
      # Only yield the last dictionary if it's not empty.
      yield Entry(d)

  def rawResponses(self):
    """Rather than iterating with whole Entry objects, this generator
    function yields individual lines (complete with line endings) from
    the server. The response data is not interpreted or transformed in
    any way."""

    try:
      for line in self.file:
        yield line
    except socket.timeout:
      pass

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__=='__main__':
  # The code below runs ONLY if this file is executed directly.

  import argparse,csv,json,sys

  p=argparse.ArgumentParser(
    description="This is a PH (a.k.a. CCSO) command line client. See RFC 2378 for technical details. The default output format is very human-readable, but JSON, CSV, Python, and raw output are also available. See the various values of the --format option.\n"
  )
  #p.add_argument('-v',dest='verbose',action='count',default=0,help="Enables diagnostic output.")
  p.add_argument('--host',dest='host',action='store',default='ph.gatech.edu',help="Name of PH server. (default: %(default)s)")
  p.add_argument('--port',dest='port',action='store',type=int,default=105,help="Port the PH server is listening on. (default: %(default)s)")
  p.add_argument('--format',dest='format',choices=('human','csv','json','json-pretty','python','raw'),default='human',help="Output format. Most of these are self-explanatory, but \"raw\" writes the unprocessed CCSO response to standard output. (default: %(default)s)")
  p.add_argument('name',nargs=argparse.REMAINDER,help="Name of the person to be looked up, optionally followed by the word \"return\" and either a list of either field names or the word \"all\".")
  arg=p.parse_args()
  arg.name=' '.join([x.strip() for x in arg.name])
  if arg.name=='':
    p.print_help()
    sys.exit(0)

  try:
    q=Search(arg.host,arg.name,port=arg.port)
    if arg.format=='human':
      i=0
      for ent in q.responses():
        i+=1
        print '-----------------------------'
        print ent
      if i>0:
        print '-----------------------------'
    elif arg.format.startswith('json'):
      data=dict(
        responses=[ent.d for ent in q.responses()],
        result=q.result # <--- Meaningful ONLY after q.responses() iterator finishes!
      )
      json.dump(data,sys.stdout,indent=(None,4)[arg.format=='json-pretty'])
      print ''
    elif arg.format.startswith('csv'):
      # Read ALL the entries.
      entries=[ent.d for ent in q.responses()]
      # Get a sorted sequence of unified fields present in the response.
      fields=set([])
      fields.update(*tuple([set(d.keys()) for d in entries]))
      fields=sorted(list(fields))
      # Add the header row above the entries.
      entries.insert(0,dict([(f,f) for f in fields]))
      # Convert each entry into a simple data row.
      for i in range(len(entries)):
        entries[i]=tuple([entries[i].get(f,'') for f in fields])
      # Write the CSV output.
      csv.writer(sys.stdout).writerows(entries)
    elif arg.format=='python':
      for ent in q.responses():
        print repr(ent.d)
    elif arg.format=='raw':
      for line in q.rawResponses():
        sys.stdout.write(line)
  except Exception,e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)
