import os

# Get the character size of this terminal when this module is loaded.
try:
  tty_rows,tty_columns=[int(x) for x in os.popen('stty size','r').read().split()]
except:
  tty_rows,tty_columns=25,80

class Progress(object):
  def __init__(self,limit,**kwargs):
    "Initialize this Progress object with an upper limit."

    # The caller MUST pass in at least an upper limit value.
    self.limit=limit

    # Remember our keyword arguments or use their defaults.
    for var,val in (
      ('fmt','(%d)'),
      ('trailer','='),
      ('mark','>'),
      ('leader','-'),
      ('end','|'),
      ('width',tty_columns-1),
    ):
      if kwargs==None:
        setattr(self,var,val)
      else:
        setattr(self,var,kwargs.get(var,val))
      if getattr(self,var)==None:
        if var=='width':
          width=tty_columns-1
        else:
          setattr(self,var,'')

    # Set our starting position to 0.
    self.position=0

  def __call__(self,position):
    """Accept a new position for this Progress object and return
    this object."""

    self.position=position
    if self.position<0:
      self.position=0
    elif self.position>self.limit:
      self.position=self.limit
    return self

  def __str__(self):
    "Output a string describing the state of this Progress object."

    # Get the string version of our position and remember its length.
    if self.fmt:
      try:
        pos_str=self.fmt%(self.position,)
      except TypeError,e:
        if str(e).startswith('not all arguments'):
          pos_str=self.fmt
        else:
          raise
    else:
      pos_str=''
    pos_len=len(pos_str)

    # Compute the ideal position of our marker in the width set up for this
    # object, and use this to start building our return value.
    pos=int((float(self.position)/self.limit)*self.width)
    # Crate our trailer position string (if any).
    if pos_str:
      if pos>pos_len:
        s=self.trailer*(pos-pos_len)
      else:
        s=''
      s+=pos_str
    else:
      s=self.trailer*pos
    # Append our position marker if possible.
    if self.mark:
      if not s:
        # Just start with the position marker with no trailer.
        s=self.mark
      else:
        if s[0]==self.trailer:
          # Remove the first leader character and append the position marker.
          s=s[1:]+self.mark
    # Append the leader.
    s+=self.leader*(self.width-len(s))
    # Append our end mark if possible.
    if self.end and s[-1] in (self.leader,self.mark):
      s=s[:-1]+self.end

    # Return our position string.
    return s

if __name__=='__main__':
  try:
    import argparse,sys,time

    ap=argparse.ArgumentParser(
      description="Output a progress bar."
    )
    ap.add_argument('--newline','-n',action='store_true',help="Write a newline character to standard output after every progress bar. By default, only a carriage return is output, returning the cursor to the left-most column of the terminal.")
    ap.add_argument('--fmt',action='store',default='(%d)',help="Format string for the numeric value of this progress bar. (default: %(default)s)")
    ap.add_argument('--mark',action='store',default='>',help="Character that marks the porgress bar's current position. (default: %(default)s)")
    ap.add_argument('--trailer',action='store',default='=',help="Character to fill in the bar to the left of (trailing behind) the current position. (default: %(default)s)")
    ap.add_argument('--leader',action='store',default='-',help="Character to fill in the bar to the right of (leading) the current position. (default: %(default)s)")
    ap.add_argument('--end',action='store',default='|',help="Character that marks the right side of the bar. (default: %(default)s)")
    ap.add_argument('--width',action='store',type=int,default=tty_columns-1,help="The number of characters to fit the progress bar into. (default: %(default)s)")
    ap.add_argument('--test',action='store',type=float,default=0,help="Write all progress bar values to standard output and exit. The optional value of this option is the number of seconds (which may be a floatin point value) to delay between each iteration.")
    ap.add_argument('pos',action='store',type=float,help="The position you want this progress bar to express.")
    ap.add_argument('limit',action='store',type=float,help="The upper limit of the pos argument.")
    opt=ap.parse_args()

    p=Progress(
      opt.limit,
      fmt=opt.fmt,
      mark=opt.mark,
      trailer=opt.trailer,
      leader=opt.leader,
      end=opt.end,
      width=opt.width
    )

    if opt.test>0:
      for i in range(int(opt.limit)+1):
        time.sleep(opt.test)
        sys.stdout.write(str(p(i)))
        if opt.newline:
          sys.stdout.write('\n')
        else:
          sys.stdout.write('\r')
        sys.stdout.flush()
      if not opt.newline:
        sys.stdout.write('\n')
      sys.exit(0)

    sys.stdout.write(str(p(opt.pos)))
    if opt.newline:
      sys.stdout.write('\n')
    else:
      sys.stdout.write('\r')
  except KeyboardInterrupt:
    sys.exit(1)
  sys.exit(0)
