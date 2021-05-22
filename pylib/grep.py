#!/usr/bin/env python2

import re,sys

class Match(object):
  """This is a fairly thin wrapper around the normal _sre.SRE_Match
  object returned by _sre.SRE_Pattern's match() and search() methods."""

  def __init__(self,match):
    self.match=match

  def group(self,*args):
    """Same as normal group(*args) method except that a value of None is
    returned if there was no match."""

    if self.match:
      return self.match.group(*args)
    return None

  def groups(self,default=None):
    """Same as the normal groups([default]) method except that an empty
    tuple is returned if there was no match."""

    if self.match:
      return self.match.groups(default)
    return ()

  def groupDict(self):
    """Return a dictionary of named groups and the values they matched,
    which are empty strings for groups that did not participate in the
    match. If there was no match, return None."""

    if self.match:
      return self.match.groupdict()
    return None

  groupdict=groupDict

  def groupObject(self):
    """Return an anonymous object whose attributes are named by the named
    groups in the the RE that created this Match object. If the RE
    failed to match anything, a value of None is returned."""

    if self.match:
      return type('',(),self.match.groupdict())
    return None

  def start(self,group=0):
    """Same as the normal start([group]) method except that a value of -1
    is return ed is there was no match."""

    if self.match:
      return self.match.start(group)
    return -1

  def end(self,group=0):
    """Same as the normal end([group]) method except that a value of -1 is
    return ed is there was no match."""

    if self.match:
      return self.match.end(group)
    return -1

  def span(self,group=0):
    """Same as the normal end([span]) method except that the tuple (-1,-1)
    is return ed is there was no match."""

    if self.match:
      return self.match.span(group)
    return (-1,-1)


class Grep(object):

  dummy_pattern=re.compile('dummy')

  def __init__(self,arg=None,**kwargs):
    '''Initialize this object. The arg parameter may be string to be
    compiled as a regular expression, an-already compiled regular
    expression, or a list or tuple of any combination thereof. You can
    also use this as a copy constructor by passing in another Grep (or
    subclass thereof) object as the arg parameter.

    Keyword arguments:

      flags:     Integer defaults to 0. The same as the re module's
                 flags argument.

      find_all:  Boolean defaults to False. If True, find ALL items in
                 the input iterable. This means that non-matching string
                 values will be returned, but the corresponding
                 [Match,...] arrays will be empty for them.

      invert:    Boolean defaults to False. Find non-matching items
                 rather than matching one. In this case, the [Match,...]
                 array of each returned tuple will be empty.

      match_all: Boolean defaults to False. Normally, an item from the
                 input iterable that matches ANY of the regular
                 expressions given to this Grep object will be returned
                 as a match. If match_all is True, an item must match
                 ALL the REs in order to qualify as a match. (This can be
                 used profitably in combination with the invert
                 argument, in which case you can think of this as a
                 doesnt_match_all flag.)

      value:     Function defaults to None. This function accecpts the
                 value of one item in the list of items to be searched
                 and returns the string value to use in the search on
                 that item. The only requirement is that it return a
                 string value. (Use this argument if your iterable
                 doesn't naturally and always return string values as
                 items (e.g. a list of mixed-type values or of database
                 rows).

    All but the flags keyword argument provide default values for the
    same arguments to Grep.__call__().
    '''

    # Get our keyword arguments, and reject any that shouldn't be there.
    self.flags=kwargs.pop('flags',0)
    self.find_all=kwargs.pop('find_all',False)
    self.invert=kwargs.pop('invert',False)
    self.match_all=kwargs.pop('match_all',False)
    self.value=kwargs.pop('value',None)
    for kw in kwargs:
      raise TypeError('Grep.__init__() got an unexpected keyword argument %r'%(kw,))

    # Get our RE pattern(s).
    self.pats=[]
    if isinstance(arg,Grep):
      # This is our copy constructor logic.
      self.pats=list(arg.pats)
      self.flags=arg.flags
      self.find_all=arg.find_all
      self.invert=arg.invert
      self.match_all=arg.match_all
      self.value=arg.value
    elif isinstance(arg,basestring):
      # Assume this string value is an RE to be compiled.
      self.pats=[re.compile(arg,self.flags)]
    elif isinstance(arg,type(Grep.dummy_pattern)):
      # Our argument is an already compile RE.
      self.pats=[arg]
    elif isinstance(arg,list) or isinstance(arg,tuple):
      # Our argument is a sequence of (hopefully) strings and/or
      # compiled RE objects. We'll compile any string values we find as
      # REs.
      for a in arg:
        if isinstance(a,basestring):
          self.pats.append(re.compile(a,self.flags))
        elif isinstance(a,re.RegexObject):
          self.pats.append(a)
        else:
          # As a final effort, try converting this value to a string and then
          # compiling that as a regular expression. If it raises an exception,
          # so be it.
          self.pats.append(re.compile(str(a),self.flags))

  def __repr__(self):
    '''Return a string that Python can evaluate to recreate this object.'''

    return 'Grep([%s],%s)'%(
      ','.join([repr(p.pattern) for p in self.pats]),
      ','.join(['%s=%r'%(var,getattr(self,var))
        for var in ('flags','find_all','invert','match_all','value')
      ])
    )

  def __str__(self):
    return repr(self)

  def __call__(self,input,**kwargs):
    '''This is an iterator that returns all matches from the input
    argument, which must be an iterable that contains or yields string
    values. (Non-string values can be managed using the value keyword
    argument. See __init__()'s description for details.) Tuples returned
    look like (string,i,[Match,...]) and contain:

      1. the whole string that matched
      2. the number (starting with 1) of the matched item in the input
         iterable
      3. the (possibly empty) list of Match objects that matched the
         ith item in the input iterable

    The keyword arguments are the same as those for Grep's constructor,
    except that there is no flags argument.

    While invert and match_all play well (and profitably) together, it
    makes no sense to use find_all with match_all. If you try, find_all
    will win and match_all will be implicitly ignored.

    Exmaples:
    Write to stdout only the lines from stdin that match any of
    our regular expressions.

      grep=Grep(array_of_REs)
      for line,n,matches in grep(sys.stdin):
        sys.stdout.write(line)


    Or if you're only going to do this once in your code, as seems
    likely when reading stdin, you could do it this way.

      for line,n,matches in Grep(array_of_REs)(sys.stdin):
        sys.stdout.write(line)


    Filter a list of filenames, leaving only those that match a given
    regular expression:

      def find_files(root):
        """Return a list of (path,filename) tuples, one for each file
        under the given root path."""

        file_list=[]
        for path,dirs,files in os.walk(root):
          for f in sorted(files):
            file_list.append((path,f))
        return file_list

      # Set up a Grep object with the RE that matches the files we want
      # and which operates on the second element of each tuple in the
      # list given to it.
      grep=Grep(args,value=lambda x:x[1])

      # Get a list of all (dir,filename) values for each file found
      # under the current directory.
      all_files=find_files('.')

      # Now keep only the files matching "foo*.bar".
      good_files=[item for item,n,matches in grep(all_files)]

    [Note that a much better way to accomplish the above assignment
    would be to subclass Grep as DirGrep (for example), whose __call__()
    operator accepts a root path rather than an input iterable. Ooo.
    Maybe I'll build that into the next version of this module. (Yeah.
    Right. Like THAT's gonna happen.)]
    '''

    # Get our keyword arguments, and reject any that shouldn't be there.
    # Set the Grep object's attributes as defaults.
    find_all=kwargs.pop('find_all',self.find_all)
    invert=kwargs.pop('invert',self.invert)
    match_all=kwargs.pop('match_all',self.match_all)
    value=kwargs.pop('value',self.value)
    for kw in kwargs:
      raise TypeError('Grep.grep() got an unexpected keyword argument %r'%(kw,))
  
    #print 'DEBUG: find_all=%r, match_all=%r, invert=%r'%(find_all,match_all,invert)
    #print 'DEBUG: value=%r'%value
    #for p in self.pats: print 'DEBUG: RE: %r'%p.pattern
    n=0
    for item in input:
      n+=1
      #print 'DEBUG:---------------------\nDEBUG: n=%r'%n

      #val=value(item) if value else item
      if value:
        val=value(item)
      else:
        val=item
      results=[Match(p.search(val)) for p in self.pats]
      #print 'DEBUG: results=%r'%results
      lr=len(results)

      matches=[m for m in results if m.match]
      #print 'DEBUG: matches=%r'%matches
      lm=len(matches)

      #print 'DEBUG: val=%r, lr=%r, lm=%r'%(val,lr,lm)
      if not find_all and (lm==lr if match_all else lm>0)==bool(invert):
        continue

      yield (item,n,matches)

if __name__=='__main__':
  import optparse,os
  from OptionParserFormatters import IndentedHelpFormatterWithNL

  op=optparse.OptionParser(
    formatter=IndentedHelpFormatterWithNL(2,8),
    usage="%prog [OPTIONS] [FILE] RE ...",
    description="""This is the test mode of my grep Python module, but you can also use it as a kind of screwey (see the very backward-looking usage above) replacement for your native grep command. Note that this command can be given only one input file, but many regular expressions.""",
    epilog="""The exit status is 0 if the match was successfull. Otherwise, a value of 1 is returned. If an error occurrs, a value >= 2 is returned. 

If -l is used with --find-files, no filenames are output. The caller must test the exit code to know whether a match was found (or not found, if -v was also given)."""
  )
  op.add_option('-i',dest='ignore_case',action='store_true',default=False,help="Ingore case.")
  op.add_option('-l',dest='list_only',action='store_true',default=False,help="Only list the names of files where matches are found. Don't show the actual matches. In this mode, the input file is searched only until the first match.")
  op.add_option('--find-all',dest='find_all',action='store_true',default=False,help="Output all lines, including those that do not match any pattern.")
  op.add_option('--match-all',dest='match_all',action='store_true',default=False,help="Matching lines must match all paterns rather than at least one pattern.")
  op.add_option('--matches-only',dest='matches_only',action='store_true',default=False,help="Show only the matching portion(s) of each line.")
  op.add_option('-n',dest='line_numbers',action='store_true',default=False,help="Each output line is preceded by its line number, starting at 1.")
  op.add_option('--find-files',dest='find_files',action='store',default=None,help="Rather than searching standard input, find filenames matching the given regular expressions.")
  op.add_option('-v',dest='invert',action='store_true',default=False,help="Output non-matching lines rather than matching ones.")
  opt,args=op.parse_args()

  def die(msg,rc=1):
    if msg:
      sys.stderr.write('%s: %s\n'%(op.get_prog_name(),msg))
    sys.exit(rc)

  if opt.invert and opt.matches_only:
    die('option error: --matches_only and --invert make no sense when used together.')

  # Set up our Grep options.
  flags=0
  if opt.ignore_case: flags|=re.IGNORECASE
  grep_options=dict(
    find_all=opt.find_all,
    match_all=opt.match_all,
    invert=opt.invert,
    flags=flags,
  )

  if opt.find_files:
    # This mode works a little like the standard find command.

    def find_files(root):
      """Return (path,filename) tuple or each file under the
      given root."""

      file_list=[]
      for path,dirs,files in os.walk(root):
        for f in sorted(files):
          file_list.append((path,f))
      return file_list

    grep=Grep(args,value=lambda x:x[1],**grep_options)
    all_files=find_files(opt.find_files)
    good_files=[dirfile for dirfile,n,matches in grep(all_files)]
    print '\n'.join([os.path.join(*dirfile) for dirfile in good_files])

  else:

    # This mode works kind of like the standard grep command.

    # Figure out what the user put on the command line.
    if len(args)>0 and not sys.stdin.isatty():
      filename='stdin'
      infile=sys.stdin
    elif len(args)>1:
      filename=args.pop(0)
      infile=open(filename)
    else:
      op.print_usage()
      sys.exit(2)

    return_code=1
    for line,n,matches in Grep(args,**grep_options)(infile):
      return_code=0
      if opt.list_only:
        print filename
        break
      prefix=''
      if opt.find_all: prefix+=('> ' if matches else '  ')
      if opt.line_numbers: prefix+='%d: '%n
      if opt.matches_only:
        if len(matches)==1:
          sys.stdout.write(prefix+matches[0].group()+'\n')
        else:
          sys.stdout.write(prefix+('-'.join(['<'+m.group()+'>' for m in matches]))+'\n')
      else:
        sys.stdout.write(prefix+line)

  sys.exit(return_code)
