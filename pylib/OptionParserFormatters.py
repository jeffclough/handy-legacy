import optparse,os,textwrap

def getTerminalSize():
  '''This function came from StackOverflow.com (wonderful site) in an
  answer posted by Johannes WeiB (the B is really a beta symbol). He
  didn't know the source.'''

  import os
  env = os.environ
  def ioctl_GWINSZ(fd):
    try:
      import fcntl, termios, struct, os
      cr=struct.unpack(
        'hh',
        fcntl.ioctl(fd,termios.TIOCGWINSZ,'1234')
      )
    except:
      return
    return cr
  cr=ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
  if not cr:
    try:
      fd=os.open(os.ctermid(),os.O_RDONLY)
      cr=ioctl_GWINSZ(fd)
      os.close(fd)
    except:
      pass
  if not cr:
    cr=(env.get('LINES',25),env.get('COLUMNS',80))
  return int(cr[1]),int(cr[0])

terminal_columns,terminal_rows=getTerminalSize()

#terminal_rows,terminal_columns=[
#  int(x) for x in os.popen('stty size','r').read().split()
#]

# Set up our command line syntax so that we can parse the command line.
class IndentedHelpFormatterWithNL(optparse.IndentedHelpFormatter):
  '''This formatter class was shamelessly copied, and only slightly
  augmented to handle epilog strings, from Tim Chase's post to
  comp.lang.python on 2007-09-30. Thanks, Tim.'''

  def __init__(
    self,
    indent_increment=2,
    max_help_position=24,
    width=terminal_columns,
    short_first=1
  ):
    optparse.IndentedHelpFormatter.__init__(
      self,
      indent_increment,
      max_help_position,
      width,short_first
    )

  def __internal_message_formatter(self,message):
    if not message: return ""
    desc_width = self.width - self.current_indent
    indent = " "*self.current_indent
    # the above is still the same
    bits = message.split('\n')
    formatted_bits = [
      textwrap.fill(bit,
        desc_width,
        initial_indent=indent,
        subsequent_indent=indent)
      for bit in bits]
    result = "\n".join(formatted_bits) + "\n"
    return result

  def format_description(self,description):
    return self.__internal_message_formatter(description)

  def format_epilog(self,epilog):
    return '\n'+self.__internal_message_formatter(epilog)

  def format_option(self, option):
    # The help for each option consists of two parts:
    #   * the opt strings and metavars
    #   eg. ("-x", or "-fFILENAME, --file=FILENAME")
    #   * the user-supplied help string
    #   eg. ("turn on expert mode", "read data from FILENAME")
    #
    # If possible, we write both of these on the same line:
    #   -x    turn on expert mode
    #
    # But if the opt string list is too long, we put the help
    # string on a second line, indented to the same column it would
    # start in if it fit on the first line.
    #   -fFILENAME, --file=FILENAME
    #       read data from FILENAME
    result = []
    opts = self.option_strings[option]
    opt_width = self.help_position - self.current_indent - 2
    if len(opts) > opt_width:
      opts = "%*s%s\n" % (self.current_indent, "", opts)
      indent_first = self.help_position
    else: # start help on same line as opts
      opts = "%*s%-*s  " % (self.current_indent, "", opt_width, opts)
      indent_first = 0
    result.append(opts)
    if option.help:
      help_text = self.expand_default(option)
# Everything is the same up through here
      help_lines = []
      for para in help_text.split("\n"):
        help_lines.extend(textwrap.wrap(para, self.help_width))
# Everything is the same after here
      result.append("%*s%s\n" % (
        indent_first, "", help_lines[0]))
      result.extend(["%*s%s\n" % (self.help_position, "", line)
        for line in help_lines[1:]])
    elif opts[-1] != "\n":
      result.append("\n")
    return "".join(result)
