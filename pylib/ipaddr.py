#!/usr/bin/env python
import exceptions,socket,struct,types
from string import *

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class IPAddrError(exceptions.Exception):
  '''This is the type of exception thrown from IPAddr and IPSubnet.'''

  def __init__(self,args=None):
    self.args=args

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class IPAddr:
  '''IPAddr is a class that encapsulates an IP address. While only a 32-bit
  integer is stored internally, IPAddr objects may be coerced into strings
  (dotted decimal) and lists and tuples.'''
  addr=0

  def __init__(self,s=None):
    if s:
      self.setval(s)

  def __hash__(self):
    '''Return this IP value as an integer for hashing purposes.'''

    return int(self)

  def __int__(self):
    '''Return the 32-bit integer value of this IP address.'''

    return int(self.addr&0x7fffffff)

  def __long__(self):
    '''Return the 32-bit integer value of this IP address.'''

    return long(int(self))

  def __index__(self):
    '''Same as int(self).'''

    return int(self)

  def __repr__(self):
    '''Return a string that eval() can use to create a copy of this object.'''

    return 'IPAddr((%d,%d,%d,%d))'%self.to_tuple()

  def __str__(self):
    '''Return a string that holds the value of this object in display format.'''
    return "%d.%d.%d.%d"%self.to_tuple()

  def __hex__(self):
    '''Like __str__() above, but uses dotted hexadecimal.'''

    return '.'.join(['%02x'%o for o in self.to_tuple()])

  def getMask(self):
    '''Return an IPAddr object containing a network mask appropriate for
    this IP address.'''

    a,b,c,d=self.to_tuple()
    if (a&0x80)==0x00 or a==10: # Calss A address or 10.0.0.0
      h=24
    elif a==0xac and (b>>4)==1: # 172.16.0.0 - 172.31.0.0
      h=20
    elif (a&0xc0)==0x80 or (a==0xc0 and b==0xa8): # Calss B address or 192.168.0.0
      h=16
    elif (a&0xe0)==0xc0: # Class C address
      h=8
    else: # Looback, broadcast, or just a plain crazy address
      h=0
    mask=(0xffffffff<<h)&0xffffffff
    return IPAddr(mask)

  def to_list(self):
    '''Return a list containing the 4 octets of this IP address.'''

    return [(self.addr>>shft)&0xff for shft in (24,16,8,0)]

  def to_tuple(self):
    '''Return a tuple containing the 4 octets of this IP address.'''

    return tuple(self.to_list())

  def nbo(self):
    '''Return the integer value of this IP address in network byte
    order, which might be the same as our native host byte order,
    depending on what type of machine we're running on.'''

    return socket.htonl(self.addr)

  def setval(self,other,nbo=False):
    '''Given a string (dotted decimal format), a list or tuple (of 4
    octet values), or an integer (a host byte order 32-bit IP address),
    set the value of this IPAddr object accordingly.

    If an integer value is given and the nbo argument is True, the
    integer is assumed to be given in network byte order. In this case
    the bytes are reversed IF NECESSARY in order to store the value
    internally in host byte order.'''

    # Convert from a list or tuple of octet values.
    if isinstance(other,types.ListType) or isinstance(other,types.TupleType):
      self.addr=0
      if len(other)<4 and not isinstance(other,types.ListType):
	other=list(other)
      while len(other)<4:
	other.append(0)
      if len(other)>4:
	raise IPAddrError,'Too many octets in IPAddress: %s'%str(other)
      for o in other:
	if o=='':
	  o=0
	try:
          if isinstance(o,basestring):
            n=int(o,0)
          else:
            n=int(o)
	except:
	  raise TypeError('Bad octet %r in IP address: %r'%(o,other))
	if n<0 or n>255:
          raise ValueError('Bad octet %r in IP address: %r'%(n,other))
	self.addr=(self.addr<<8)|n
      return self
    if isinstance(other,types.StringType):
      l=other.split('.')
      return self.setval(l)
    if isinstance(other,types.IntType) or isinstance(other,types.LongType):
      self.addr=int(other&0xffffffff)
      if nbo:
        self.addr=ntohl(self.addr)
      return self
    if isinstance(other,IPAddr):
      self.addr=other.addr
      return self
    raise TypeErorr('Attempted to coerce unsupported type %s with value %r to IPAddr'%(type(other),other))

  def __len__(self):
    '''All IP addresses (as far as this implementation is concerned) are
    four octets in length.'''

    return 4

  def __getitem__(self,i):
    '''Return the ith (cardinally speaking) octet of our IP address.'''

    if i&~3:
      raise IndexError,'IPAddr index out of range'
    return (self.addr>>(8*(3-i))) & 0xff

  def __setitem__(self,i,val):
    '''Set the ith (cardinally speaking) octet of our IP address. The
    left-most octet is at index 0.'''

    if i&~3:
      raise IndexError('IPAddr index out of range: %r'%i)
    try:
      n=int(val,0)
    except:
      raise TypeErorr('Attempted to coerce unsupported type %s with value %r to IPAddr octet'%(type(val),val))
    if n&~0xff:
      raise ValueErorr('IPAddr octet value out of range: %r'%n)
    shft=8*(3-i)
    mask=~(0xff<<shft)
    self.addr=(self.addr|mask)|(n<<shft)

  def __getslice__(self,i,j):
    '''Return the requested slice as a tuple.'''

    return self.to_tuple()[i:j]

  def __cmp__(self,other):
    '''Compare this IP address with another, which might be either an IPAddr
    object or a value that can be coerced into one.'''

    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    addr=other.addr
    # Now perform an unsigned comparison between two 32-bit integers.
    if (self.addr^addr)&0x80000000:
      n=(addr&0x80000000)-(self.addr&0x80000000)
    else:
      n=(self.addr&0x7fffffff)-(addr&0x7fffffff)
    return n

  def __lt__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr<other.addr

  def __le__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr<=other.addr

  def __eq__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr==other.addr

  def __ne__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr!=other.addr

  def __ge__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr>=other.addr

  def __gt__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self.addr>other.addr

  def __nonzero__(self):
    return self.addr!=0

  def __coerce__(self,other):
    if not isinstance(other,IPAddr):
      other=IPAddr(other)
    return self,other

  def __add__(self,other):
    return IPAddr(self.addr+other.addr)

  def __iadd__(self,other):
    self.addr+=other.addr
    return self

  def __sub__(self,other):
    return IPAddr(self.addr-other.addr)

  def __isub__(self,other):
    self.addr-=other.addr
    return self

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class IPSubnet:
  '''The IPSubnet class encapsulates an IP network address and a subnet mask.
  It stores these in two IPAddr objects internally.'''

  net=IPAddr()
  mask=IPAddr()

  def __init__(self,s=None):
    if s:
      self.setval(s)

  def __repr__(self):
    return 'IPSubnet((%s,%s))'%(repr(self.net),repr(self.mask))

  def __str__(self):
    return '%s/%s'%(str(self.net),str(self.mask))

  def __hex__(self):
    return '%s/%s'%(hex(self.net),hex(self.mask))

  def __contains__(self,obj):
    '''Given an IPAddr object, or some value that that can be coerced into
    an IPAddr object, return true if that IP address resides on our subnet.
    Otherwise, return False.'''

    if not isinstance(obj,IPAddr):
      obj=IPAddr(obj)
    return (obj.addr&self.mask.addr)==self.net.addr

  def setval(self,other):
    '''Set the value of this IPSubnet object as specified by other. The other
    parameter may be a string, list, or tuple. If a string is used, it may be
    formatted as:

    d.d.d.d 
      or
    d.d.d.d/d.d.d.d
      or
    d.d.d.d/size

    If other is a list or tuple, it must contain one or two values that can
    be coerced to IPAddr values. The first is the network address and the
    second is the subnet mask. If the subnet mask is omitted, it will be
    computed from the network address by translating any non-zero octets to
    a value of 255.'''

    if isinstance(other,types.StringType):
      if other.find('/')==-1:
        # Guess the subnet mask from the given IP address.
        addr=IPAddr(other)
        self.setval((addr,addr.getMask()))
      else:
        # We've been given a specific subnet mask ...
        addr,mask=other.split('/',1)
        try:
          # which might simply be the number of bits in the mask,
          n=int(mask,0)
          if n<0 or n>32:
            raise ValueError('Bad mask size (%r) used in IPSubnet %r'%(n,other))
          mask=IPAddr((-1<<(32-n))&0xffffffff)
        except:
          # or the actual bit pattern of the mask.
          pass
        self.setval((addr,mask))
      return self
    if isinstance(other,types.ListType) or isinstance(other,types.TupleType):
      if len(other)<1 or len(other)>2:
	raise IPAddrError,'Malformed subnet component list.'
      self.net=IPAddr(other[0])
      if len(other)>1:
	self.mask=IPAddr(other[1])
      else:
        self.mask=self.net.getMask()
	l=self.net.to_list()
      self.net.addr&=self.mask.addr

 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
 # # # # # # # # # # # #  U N I T   T E S T   C O D E  # # # # # # # # # # # #

if __name__=='__main__':
  tlist=[('130.207.165',
	  '130.207.164.254',
	  '130.207.164.255',
	  [130,207,165,0],
	  (130,207,165,1),
	  0x82cfa5fe, # 130.207.165.254
	  '130.207.165.255',
	  '130.207.166.0',
	  '130.207.166.1'),
	 ('10.0.0.0',
	  '9.0.255.254',
	  '9.0.255.255',
	  '10.0.0.1',
	  '10.0.1.0',
	  '10.0.255.254',
	  '10.0.255.255',
	  '10.1.0.0',
	  '11.0.0.0',
	  '11.0.0.1'),
	 ]
  # Test construction of IPAddr and IPSubnet and subnet containership.
  for t in tlist:
    subnet=IPSubnet(t[0])
    print 'Subnet=%s'%str(subnet)
    for a in t[1:]:
      addr=IPAddr(a)
      if addr in subnet:
	print '\t%s\tin'%str(addr)
      else:
	print '\t%s\tout'%str(addr)

  # Test more construction variations, repr() and eval() compatibilty,
  # comparison of IPAddr objects with various types of values, etc.
  x=IPAddr('1.2.3.4')
  print 'x is %s'%x
  print 'hex(x) is %r'%hex(x)
  print 'x is 0x%08x when stringified with 0x%%08x'%x
  print 'repr(x) is "%s"'%repr(x)
  print 'y=x'
  y=x
  print 'y-=1'
  y-=1
  print 'x is %s, y is %s'%(x,y)
  print 'y=IPAddr(x)'
  y=IPAddr(x)
  print 'y is %s'%y
  print 'x==y is %r'%(x==y)
  print 'x=="1.2.3.3" is %r'%(x=='1.2.3.3')
  print 'y=x+1'
  y=x+1
  print 'x is %s, y is %s'%(x,y)
  print 'y+=1'
  y+=1
  print 'y is %s'%y
  print 'x<y is %r'%(x<y)
  print 'x<=y is %r'%(x<=y)
  print 'x==y is %r'%(x==y)
  print 'x!=y is %r'%(x!=y)
  print 'x>=y is %r'%(x>=y)
  print 'x>y is %r'%(x>y)

  # Test subnet functionality.
  subnet=IPSubnet('127.0.0.0')
  print 'subnet is %s'%subnet
  s='127.0.0.0/255.255.255.254 128.61.0.0/255.255.0.0 130.207.0.0/255.255.0.0 143.215.0.0/255.255.0.0 199.77.128.0/255.255.128.0'
  print s
  t=tuple(map(lambda x:IPSubnet(x),s.split()))
  print t
