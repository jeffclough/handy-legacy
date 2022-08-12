#!/usr/bin/env python3

import signal,os

# This context manager class implements timeout functionality in a way
# that's easy to use within a "with" block.

class Timeout(object):
  """Use a Timout instance as a context manager for anything you need to
  be interrupted if it doesn't finish within a given number of seconds.
  For example:

      from timeout import Timeout

      ...

      try:
          with Timeout(8,"What's taking so long!?"):
              do_something_complicated()
      except Timeout.Error as e:
          print(str(e))

  If do_something_complicated() takes more than 8 seconds to return, a
  Timeout.Error exception is raised, which contains the exception
  message given when the Timeout instance is created.
  and processing continues after the except block. Otherwise all is
  well, and execution continues after the except block.

  This implementation of Timeout uses SIGALRM to do the heavy lifting, so it
  can hanle only integer values (seconds) for the time-out duration.

  Because a given process can have only one SIGALRM timer, ONLY ONE Timeout CAN
  BE IN OPERATION AT A TIME. Beginning a new Timeout opeation before an
  existing one has finished effectively removes the time-out constraint on the
  first, allowing it to run to completion (or forever). I'm mulling over
  different techniques for removing this restriction."""

  class Error(Exception):
    "Timeout.Error is raised if Timeout's timeer expires."

    pass

  def __init__(self,seconds=10,error_msg=None):
    """Initialize this Timeout instance with some number of seconds and
    an error (timeout) message to be used if a Timeout.Error exception
    needs to be raised.

    The seconds argument defaults to 10 and must be a non-zero integer
    number of seconds.

    The error_msg argument defaults to "Timed out after 10 seconds." If
    the seconds argument is something other than 10, error_msg will use
    that number in its default value.
    """

    self.seconds=seconds
    if error_msg:
      self.error_msg=error_msg
    else:
      if seconds==1:
        self.error_msg="Timed out after 1 second."
      else:
        self.error_msg="Timed out after %r seconds."%(self.seconds)

  def handler(self, signum, frame):
    raise self.Error(self.error_msg)

  def __enter__(self):
    # Set up our SIGALRM handler and start the timer.
    signal.signal(signal.SIGALRM,self.handler)
    signal.alarm(self.seconds)

  def __exit__(self, type, value, traceback):
    # Make sure out timer stops one way or another.
    signal.alarm(0)

  def __repr__(self):
    return '%s(%r,%r)'%(self.__class__.__name__,self.seconds,self.error_msg)

  def __str__(self):
    return "After %d seconds: %s"%(self.seconds,self.error_msg)

if __name__=='__main__':
  import argparse,pipes,subprocess,sys

  DEFAULT_TIMEOUT=10

  def die(msg=None,rc=1):
    if msg:
      print('%s: %s'%(os.path.basename(sys.argv[0]),msg),file=sys.stderr)
    sys.exit(rc)

  ap=argparse.ArgumentParser(
    description="""%%(prog)s runs the given command, passing it any arguments you provide, in a timed environment. By default, the command will be allowed to run for %d seconds. If the command terminates within this time, %%(prog)s will simply terminate with the exit code of the completed command. Otherwise, a message will be written to standard error, and %%(prog)s will terminate with an exit code of 1 (by default)."""%(DEFAULT_TIMEOUT,))
  ap.add_argument('-t','--timeout',action='store',type=int,default=DEFAULT_TIMEOUT,help="The number of seconds (a positive integer value) expressing how long the given command will be allowed to run. After this interval, it will be killed, and an error code will be returned to the operating system. (default: %(default)d)")
  ap.add_argument('-m','--message',action='store',help="This message is written to standard error if the given command is still running when the timeout interval elapses. (default: a message indicating how long the time-out took)")
  ap.add_argument('-r','--timeout-result',action='store',type=int,default=1,help="This is exit code returned to the operating system if the given command is still running when the timeout interval elapses. This must be an integer from 0 to 255. (default: %(default)d)")
  ap.add_argument('command',metavar='COMMAND [ARG]',nargs='*',help="The name of the command to be run and whatever arguments to give it.")

  opt=ap.parse_args()
  if opt.timeout<1:
    die("--timeout value of %d is not a positive integer."%(opt.timeout,))
  if not 0<=opt.timeout_result<=255:
    die("--timeout-result value of %d is not in the range from 0 to 255."%(opt.timeout_result,))
  if not opt.command:
    die("No command given.")

  try:
    cmd=' '.join([pipes.quote(x) for x in opt.command])
    with Timeout(opt.timeout,opt.message):
      rc=subprocess.call(
        cmd,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True
      )
      sys.exit(rc)
  except Timeout.Error as e:
    die(str(e),opt.timeout_result)
  except Exception:
    raise
