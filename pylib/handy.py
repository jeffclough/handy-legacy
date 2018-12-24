import os,pipes,re,sys

def file_walker(root,**kwargs):
  """This is a recursive iterator over the files in a given directory
  (the root), in all subdirectories beneath it, and so forth. The order
  is an alphabetical, depth-first traversal of the whole directory tree.

  Keyword Arguments:
    depth         (default: None) The number of directories this
                  iterator will decend below the given root path when
                  traversing the directory structure. Use 0 for only
                  top-level files, 1 to add the next level of
                  directories' files, and so forth.
    follow_links  (default: True) True if symlinks are to be followed.
                  This iterator guards against processing the same
                  directory twice, even if there's a symlink loop, so
                  it's always safe to leave this set to True.
    prune         (default: []) A list of regular expressions (either
                  strings or _sre.SRE_Pattern objects). If any of these
                  REs matches the name of an encountered directory, that
                  directory is ignored.
    include_dirs  (default: False) True if each directory encountered is
                  to be included in this iterator's values immediately before
                  the filename found in that directory. Directory names end
                  with the path separator appropriate to the host operating
                  system in order to distinguish them from filenames. If the
                  directory is not descended into because of depth-limiting or
                  pruning, that directory will not appear in this iterator's
                  values at all. The default is False, so that only
                  non-directory entries are included. 
  """

  # Get our keyword argunents, and do some initialization.
  max_depth=kwargs.get('depth',None)
  if max_depth==None:
    max_depth=sys.maxsize # I don't think we'll hit this limit in practice.
  follow_links=kwargs.get('follow_links',True)
  prune=list(kwargs.get('prune',[]))
  include_dirs=kwargs.get('include_dirs',False)
  been_there=set([])
  stack=[(0,root)] # Prime our stack with root (at depth 0).

  # Compile any strings in prune to regular expressions.
  for i in range(len(prune)):
    if isinstance(prune[i],basestring):
      prune[i]=re.compile(prune[i])

  while stack:
    depth,path=stack.pop()
    if include_dirs:
      yield path+os.sep
    flist=os.listdir(path)
    flist.sort()
    dlist=[]
    # First, let the caller iterate over these filenames.
    for fn in flist:
      p=os.path.join(path,fn)
      if os.path.isdir(p):
        # Just add this to this path's list of directories for now.
        dlist.insert(0,fn)
        continue
      yield p
    # Don't dig deeper than we've been told to.
    if depth<max_depth:
      # Now, let's deal with the directories we found.
      for fn in dlist:
        p=os.path.join(path,fn)
        # We might need to stack this path for our fake recursion.
        if os.path.islink(p) and not follow_links:
          # Nope. We're not following symlinks.
          continue
        rp=os.path.realpath(p)
        if rp in been_there:
          # Nope. We've already seen this path (and possibly processed it).
          continue
        m=None
        # Because of the way it's structured, this test MUST come last.
        for pat in prune:
          m=pat.match(fn)
          if m:
            # Nope. This directory name matches something in our prune list.
            break
        if not m:
          # Remember this path so we can visit it later.
          been_there.add(rp)
          stack.append((depth+1,p))

def shellify(val):
  """Return the given value quotted and escaped as necessary for a Unix
  shell to interpret it as a single value.

  >>> print shellify(None)
  ''
  >>> print shellify(123)
  123
  >>> print shellify(123.456)
  123.456
  >>> print shellify("This 'is' a test of a (messy) string.")
  'This '"'"'is'"'"' a test of a (messy) string.'
  >>> print shellify('This "is" another messy test.')
  'This "is" another messy test.'
  """

  if val==None:
    return "''"
  if isinstance(val,int) or isinstance(val,float):
    return val
  if not isinstance(val,basestring):
    val=str(val)
  return pipes.quote(val)

class TitleCase(str):
  """A TitleCase value is just like a str value, but it gets title-cased
  when it is created.

  >>> TitleCase('')
  ''
  >>> TitleCase('a fine kettle of fish')
  'A Fine Kettle of Fish'
  >>> TitleCase('    another     fine     kettle     of     fish    ')
  'Another Fine Kettle of Fish'
  >>> t=TitleCase("to remember what's yet to come")
  >>> t
  "To Remember What's Yet to Come"
  >>> t.split()
  ['To', 'Remember', "What's", 'Yet', 'to', 'Come']
  >>> str(type(t)).endswith(".TitleCase'>")
  True
  """
  
  # Articles, conjunctions, and prepositions are always lower-cased, unless
  # they are the first word of the title.
  lc=set("""
    a an the
    and but nor or
    is
    about as at by circa for from in into of on onto than till to until unto via with
  """.split())

  def __new__(cls,value=''):
    # Divide this string into words, and then process it that way.
    words=[w for w in value.lower().split() if w]

    # Join this sequence of words into a title-cased string.
    value=' '.join([
      words[i].lower() if words[i] in TitleCase.lc and i>0 else words[i].capitalize()
        for i in range(len(words))
    ])

    # Now become our immutable value as a title-cased string.
    return str.__new__(cls,value)

if __name__=='__main__':
  import doctest,sys
  t,f=doctest.testmod()
  if f>0:
    sys.exit(1)
