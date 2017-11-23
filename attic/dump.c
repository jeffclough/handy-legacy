/******************************************************************************

PROGRAM: dump

AUTHOR:  Jeff Clough
	 Jeff.clough@oit.gatech.edu

HISTORY:
2003-02-04: This is the initial version of the program. I went ahead and added
a ton of features to it now so that I wouldn't have to add them piece-meal
later on. This is a program that I've used in a DOS/Windows environment for
uncounted ages, but like so much ancient knowledge, the source is lost in the
mists of antiquity. This is a complete rewrite. We'll call it version 1.0.

2003-02-11: I've added the -c (which required a change to -w's behavior) and
-f options. Right now -f is a little pointless, but it is a step in the
dreiction of adding binary file editing, both interactive and automated, to
this program. See history notes or TODOs below for more details on this.

TODO: Adding a curses interface to this would be a huge help. My old DOS
version of this program was able to scroll up and down through a file, used
color to highlight control characters, and had its own built-in search
capability.

TODO: I'd like this program to have the ability to send its output to an
editor process in a temporary file, allow that process to modify the file, and
then write the changes back to the original file that was dumped. The editor
process might be vi or a sed or awk script or something more sophisticated. I
believe that this architecture is superior to the relationship that exists
between vim and xxd because this allows for more versatility while retaining
the basic ability to edit a binary file interactively.

BUILDING INSTRUCTIONS:
I used gcc, so here's how that worked.

  gcc [-DLINUX] -lm -o dump dump.c

The -lm option was required in order to load the math library becuase I used
the log() and ceil() functions to compute the number of characters needed
to represent addresses and bytes in various bases.

******************************************************************************/

#include <ctype.h>
#include <fcntl.h>
#ifdef __GNUC__
#include <unistd.h>
#endif
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

/*
 * Because the logic of this program requires file offset to be unsigned, 
 * since some implementations of off_t are signed, I've decided to use my
 * own typedef: off
 */
typedef unsigned long off;

int  opt_abase=16;  /* Base for address formatting.                  */
int  opt_base=16;   /* Base for data output.                         */
off  opt_start=0;   /* Offset from which to begin the dump.          */
off  opt_length=0;  /* Number of bytes to dump.                      */
off  opt_stop=-1;   /* Offset where the dump should stop.            */
int  opt_text=0;    /* True if text is to be dumped as well.         */
char *opt_prog;     /* Name of this program.                         */
int  opt_outw=0;    /* Number of columns to format our output for.   */
int  opt_format=0;  /* True if we should output our output format.   */
int  opt_columns=0; /* Number of dumped bytes per row of output.     */
		    /* NOTE: columns must be an integral power of 2. */

int  addrw;      /* Width of the address in each row of output.          */
char *text=NULL; /* Holds the text output for a row if opt_text is true. */
char *filename;  /* Name of the file currently being processed.          */

/******************************************************************************
 * Given a file descriptor opened for reading, dump the contents of that file.
 * The dump will start at offset opt_start and run until offset opt_stop is
 * reached. Output in the base given by opt_base.
 */
int dump(int fd) {
  unsigned char buf[8192];
  off bo=0,o=0;
  unsigned bytesread,i,j,n;

  /*
   * Describe our output format if we need to.
   */
  if (opt_format) {
    putchar(' ');
    switch(opt_abase) {
      case 8:putchar('o');break;
      case 10:putchar('d');break;
      case 16:
      default:putchar('h');break;
    }
    switch(opt_base) {
      case 8:putchar('o');break;
      case 10:putchar('d');break;
      case 16:
      default:putchar('h');break;
    }
    if (opt_text)
      putchar('t');
    printf(" %d",opt_columns);
  }
  putchar('\n');

  /*
   * If we're not starting at the beginning of the file, take care of that now.
   */
  if (opt_start) {
    bo=opt_start&~(opt_columns-1);
    o=lseek(fd,bo,SEEK_SET);
    if (o==(off)-1) {
      perror(filename);
      return 1;
    }
    if (o<bo)   /* Start of dump is past end of file, */
      return 0; /* so there's no work to do here.     */
  }

  /*
   * Read and dump buffers until we get to the end of the file or until we get
   * to where the user has told us to stop.
   */
  while((bytesread=read(fd,buf,sizeof(buf)))>0) {
    /* A little when-to-stop logic if you please. */
    if (bo>=opt_stop)
      break;
    if (bo+bytesread>opt_stop)
      n=(unsigned)(opt_stop-bo);
    else
      n=bytesread;

    /*
     * Dump the content of the bufer to standard output.
     */
    for(i=0;i<n;i+=opt_columns) {
      if (text)
	memset(text,0,opt_columns+1);
      /* Write the address of this row of our dump. */
      switch(opt_abase) {
      case 8:printf("%0*lo",addrw,bo+i);break;
      case 10:printf("%0*lu",addrw,bo+i);break;
      case 16:
      default:printf("%0*lx",addrw,bo+i);
      }

      /*
       * Dump the data that should go on this row. Build our text string
       * at the same time if we're going to display it.
       */
      switch(opt_base) {
      case 8:
	for(j=0;j<opt_columns && i+j<n;++j) {
	  if ((j&3)==0)
	    putchar(' ');
	  printf("%03o ",buf[i+j]);
	  if (text)
	    text[j]=isprint(buf[i+j])?buf[i+j]:'.';
	}
	break;
      case 10:
	for(j=0;j<opt_columns && i+j<n;++j) {
	  if ((j&3)==0)
	    putchar(' ');
	  printf("%3d ",buf[i+j]);
	  if (text)
	    text[j]=isprint(buf[i+j])?buf[i+j]:'.';
	}
	break;
      case 16:
      default:
	for(j=0;j<opt_columns && i+j<n;++j) {
	  if ((j&3)==0)
	    putchar(' ');
	  printf("%02x ",buf[i+j]);
	  if (text)
	    text[j]=isprint(buf[i+j])?buf[i+j]:'.';
	}
      }
      /* Fill out the tail of any partial last row of data in the buffer. */
      for(;j<opt_columns;++j) {
	if ((j&3)==0)
	  putchar(' ');
	switch(opt_base) {
	case 8:
	case 10:
	  printf("    ");
	  break;
	case 16:
	default:
	  printf("   ");
	}
      }
      if (text)
	printf("%s\n",text);
      else
	putchar('\n');
    }
    /* Keep track of the beginning offset of the buffer within the file. */
    bo+=n;
  }
  
  return 0;
} /* int dump(int fd) */

/******************************************************************************
 * Tell the user how to use this program.
 */
int usage(int rc) {
  puts("Usage: dump [-dhotu] [-a{base}] [-s{start}] [-e{end}] [-l{len}]\n"
       "            [-w{width}] [filename ...]\n"
       "\n"
       "The dump program is an alternative to the more standard od program.\n"
       "Use it to examine the contents of files or standard input.\n"
       "\n"
       "-a    Set the radix for representing addresses to octal (-ao),\n"
       "      decimal (-ad), or hexadecimal (-ah). -ah is the default.\n"
       "\n"
       "-c    Sets the number of data columns to {width}. The value of {width}\n"
       "      must be a multiple of 4 from 4 to 256.\n"
       "\n"
       "-e    Sets the address within the dumped file(s) where output will\n"
       "      end. The last byte dumped will be the one immediately preceeding\n"
       "      this address. This defaults to the end of each respective file\n"
       "      and MUST NOT be specified if the -l option is used.\n"
       "\n"
       "-f    Follows the filename at the top of each dump with a terse\n"
       "      description of the format of the data that follows.\n"
       "\n"
       "-l    Sets the length of data (in bytes) to be dumped beginning with\n"
       "      the starting location. By default, the dump will proceed to\n"
       "      the end of the file. This option MUST NOT be specified if the\n"
       "      -e option is used.\n"
       "\n"
       "-dho  Set the radix for representing data to decimal, hexadecimal, or\n"
       "      octal, respectively. -h is the default.\n"
       "\n"
       "-s    Sets the address within the dumped file(s) where output will\n"
       "      commence. This defaults to 0 and will be rounded down to the\n"
       "      next lower multiple of the number of bytes in each row of\n"
       "      output if necessary.\n"
       "\n"
       "-t    Turns on text output. This displays at the end of each row of\n"
       "      output the text version of that row's data.\n"
       "\n"
       "-u    Shows this usage message.\n"
       "\n"
       "-w    Tells dump to assume that at least {width} characters per line\n"
       "      are available on the output device. {width} defaults to whatever\n"
       "      -c's argument requires, or to 80 in -c's absence.\n"
       "\n"
       "Numeric arguments to the options above may be specified in decimal (by\n"
       "default), in octal (if given a leading \"0\"), or in hex (if begun with \"0x\").\n"
       "\n"
       "An arbitrary number of filenames may be given on the command line. \"-\" may\n"
       "be used to refer to standard input. The dump of each file is performed\n"
       "according to the complete set of options on the command line.");
  return rc;
} /* int usage(int rc) */

/******************************************************************************
 * Handle the command line options and arguments.
 */
int main(int argc,char **argv) {
  int dw,tw; /* Data width and total width. */
  int ch;    /* Holds command line options. */

  /*
   * Handle command line options.
   */
  opt_prog=*argv;
  while((ch=getopt(argc,argv,"a:c:de:fhl:os:tuw:"))!=EOF)
    switch(ch) {
    case 'a':
      printf("DBG: optarg=\"%s\"\n",optarg);
      opt_abase=0;
      if (sscanf(optarg,"%d",&opt_abase)!=1) {
	fprintf(stderr,"%s: Cannot address base value: %s\n",opt_prog,optarg);
	return 1;
      }
      printf("DBG: opt_abase=%d\n",opt_abase);
      switch(opt_abase) {
      case 'd':opt_abase=10;break;
      case 'h':opt_abase=16;break;
      case 'o':opt_abase=8;break;
      default:
	fprintf(stderr,"%s: Invalid address base: %c\n",opt_prog,opt_abase);
	return 1;
      }
      break;
    case 'c':
      if (sscanf(optarg,"%i",&opt_columns)!=1) {
	fprintf(stderr,"%s: Cannot parse column number: %s\n",opt_prog,optarg);
	return 1;
      }
      if (opt_columns<4 || opt_columns>256) {
	fprintf(stderr,"%s: Column count must be in the range from 4 to 256.\n",
	        opt_prog);
	return 1;
      }
      if ((opt_columns&3)!=0) {
	fprintf(stderr,"%s: Column count must be a multiple of 4.\n",
	        opt_prog);
	return 1;
      }
      break;
    case 'd':
      opt_base=10;
      break;
    case 'e':
      if (sscanf(optarg,"%li",&opt_stop)!=1) {
	fprintf(stderr,"%s: Cannot parse end position: %s\n",opt_prog,optarg);
	return 1;
      }
      break;
    case 'f':
      opt_format=1;
      break;
    case 'h':
      opt_base=16;
      break;
    case 'o':
      opt_base=8;
      break;
    case 'l':
      if (sscanf(optarg,"%li",&opt_length)!=1) {
	fprintf(stderr,"%s: Cannot parse length value: %s\n",opt_prog,optarg);
	return 1;
      }
      break;
    case 's':
      if (sscanf(optarg,"%li",&opt_start)!=1) {
	fprintf(stderr,"%s: Cannot parse start position: %s\n",opt_prog,optarg);
	return 1;
      }
      break;
    case 't':
      opt_text=1;
      break;
    case 'u':
      return usage(0);
    case 'w':
      if (sscanf(optarg,"%i",&opt_outw)!=1) {
	fprintf(stderr,"%s: Cannot parse output width: %s\n",opt_prog,optarg);
	return 1;
      }
      break;
    default:
      return usage(1);
    }

  /*
   * Ensure that our options make sense.
   */
  if (opt_stop!=(off)-1 && opt_length!=0) {
    fprintf(stderr,"%s: Only one of -e and -l may be given.",opt_prog);
    return 1;
  }
  if (opt_length>0)
    opt_stop=opt_start+opt_length;
  if (opt_stop<=opt_start) {
    fprintf(stderr,"%s: Starting offset (%lu) must preceed ending offset (%lu)\n",opt_prog,opt_start,opt_stop);
    return 1;
  }

  /*
   * Compute how many bytes we'll dump on each row of output.
   */
#define OUTLINESIZE(addrwidth,datawidth)         \
  ((addrwidth)+1+opt_columns*((datawidth)+1)+    \
  ((opt_columns-4)>>2)+(opt_text?opt_columns:0))

  addrw=(int)ceil(log(0x8000000L)/log(opt_abase));
  dw=(int)ceil(log(0x80)/log(opt_base));
  if (opt_columns) {
    tw=OUTLINESIZE(addrw,dw);
    if (opt_outw==0)
      opt_outw=tw;
    else
      if (opt_outw<tw) {
	fprintf(stderr,"%s: %d bytes per line%s require at least %d characters "
	    "per output line.",
	    opt_prog,opt_columns,opt_text?" with ASCII text appended":"",tw);
	return 1;
      }
  }
  else {
    if (opt_outw==0)
      opt_outw=80;
    for(opt_columns=256;opt_columns>0;opt_columns>>=1) {
      tw=OUTLINESIZE(addrw,dw);
      if (tw<=opt_outw)
	break;
    }
    if (opt_columns==0) {
      if (opt_text)
	fprintf(stderr,"%s: Given base-%d addreses, base-%d data, "
	    "and text, at least %d opt_columns of output are needed.",
	    opt_prog,opt_abase,opt_base,tw);
      else
	fprintf(stderr,"%s: Given base-%d addreses and base-%d data, "
	    "at least %d opt_columns of output are needed.",
	    opt_prog,opt_abase,opt_base,tw);
      return 1;
    }
  }

  /*
   * Allocate string space for the text portion of our output if our
   * output will have a text portion.
   */
  if (opt_text)
    text=malloc(opt_columns+1);

  /*
   * Handle command line arguments.
   */
  if (optind>=argc) {
    filename="stdin";
    dump(fileno(stdin));
  }
  else
    for(;optind<argc;++optind) {
      char *arg;
      arg=argv[optind];
      if (strcmp(arg,"-")==0) {
	filename="stdin";
	printf("%s:",filename);
	dump(fileno(stdin));
	if (optind+1<argc)
	  putchar('\n');
      }
      else {
	int fd;
	if ((fd=open(arg,O_RDONLY|O_NOCTTY))<0) {
	  perror(arg);
	  return 1;
	}
	filename=arg;
	printf("%s:",filename);
	dump(fd);
	close(fd);
	if (optind+1<argc)
	  putchar('\n');
      }
    }

  /* Some house cleaning. */
  if (text)
    free(text);
  return 0;
} /* int main(int argc,char **argv) */
