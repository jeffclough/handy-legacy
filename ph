#!/usr/bin/env python

import argparse,json,os,re,socket,sys

p=argparse.ArgumentParser(
  description="This is a PH (a.k.a. CCSO) command line client. See RFC 2378 for technical details.\n"
)
p.add_argument('-v',dest='verbose',action='count',default=0,help="Enables diagnostic output.")
p.add_argument('--host',dest='host',action='store',default='ph.gatech.edu',help="Name of PH server. (default: %(default)s)")
p.add_argument('--port',dest='port',action='store',type=int,default=105,help="Port the PH server is listening on. (default: %(default)s)")
p.add_argument('--format',dest='format',choices=('human','json','json-pretty','raw'),default='human',help="Output format. (default: %(default)s)")
p.add_argument('name',nargs=argparse.REMAINDER,help="Name of the person to be looked up, optionally followed by the word \"return\" and either a list of either field names or the word \"all\".")
arg=p.parse_args()
arg.name=' '.join([x.strip() for x in arg.name])
if arg.name=='':
  p.print_help()
  sys.exit(0)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

line_parser=re.compile(r'(?P<more>-)?(?P<code>\d+):(?P<message>.*)')
message_parser=re.compile(r'(?P<item>\d+):\s*(?P<field>[^:]+):\s*(?P<value>.*)')

class CcsoEntryParser(object):
  def __init__(self,sock,bufsize=1024):
    self.sock=sock
    self.bufsize=bufsize
    self.buf=''
    self.lastline=''
    self.result=''

  def linesFromBuffer(self):
    i=self.buf.find('\n')
    while i>=0:
      self.lastline=self.buf[:i]
      if arg.verbose>5:
        print 'CcsoEntryParser.linesFromBuffer() yields %r (%d bytes)'%(self.lastline,len(self.lastline))
      yield self.lastline
      self.buf=self.buf[i+1:]
      i=self.buf.find('\n')

  def linesFromSocket(self):
    prefix=''
    self.buf=self.sock.recv(self.bufsize)
    n=len(self.buf)
    if arg.verbose>6:
      print 'CcsoEntryParser.linesFromSocket() read %d bytes: %r'%(n,self.buf)
    while n==self.bufsize:
      if prefix:
        self.buf=prefix+self.buf
        prefix=''
      for line in self.linesFromBuffer():
        yield line
      prefix=self.buf
      self.buf=self.sock.recv(self.bufsize)
      n=len(self.buf)
      if arg.verbose>6:
        print 'CcsoEntryParser.linesFromSocket() read %d bytes: %r'%(n,self.buf)
    else:
      if prefix:
        self.buf=prefix+self.buf
      for line in self.linesFromBuffer():
        yield line

  def entries(self):
    prev_item=0
    d={}
    for line in self.linesFromSocket():
      m=line_parser.match(line)
      if not m:
        sys.stderr.write('Bad response line: %r\n'%(line,))
        return
      #print line
      more,code,message=m.groups()
      code=int(code)
      if code!=200:
        sys.stderr.write('Error: %d %s\n'%(code,message))
        return
      m=message_parser.match(message)
      if not m:
        self.result=(code,message)
        break
      item,field,value=m.groups()
      if item>prev_item:
        # If this is a new item, return (yield) the old one and start the next.
        if d:
          yield d
          d={}
        prev_item=item
      # Add this line to the current dictionary.
      d[field]=value
    if d:
      # Only yield the last dictionary if it's not empty.
      yield d

def format_human(entry,stream=sys.stdout):
  # Get the length of the longest field name.
  w=max([len(x) for x in entry])
  # Get an alphabetic list of fields.
  fields=sorted(entry.keys())
  # Send the output to the given stream.
  stream.write('-----------------------------\n')
  for f in fields:
    stream.write('%*s: %s\n'%(w,f,entry[f]))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ph=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
ph.connect((arg.host,arg.port))
ph.sendall(arg.name+'\n')
resp=CcsoEntryParser(ph,bufsize=4096)
if arg.format=='human':
  i=0
  for ent in resp.entries():
    i+=1
    format_human(ent)
  if i>0:
    print '-----------------------------'
elif arg.format.startswith('json'):
  entries=[]
  for ent in resp.entries():
    entries.append(ent)
  json.dump([entries,resp.result],sys.stdout,indent=(None,4)[arg.format=='json-pretty'])
  print ''
elif arg.format=='raw':
  for line in resp.linesFromSocket():
    print line
