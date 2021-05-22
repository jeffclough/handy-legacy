/*
 * PROGRAM: freq
 *
 * AUTHOR:  Jeff Clough
 *	    jeff.clough@oit.gatech.edu
 *
 * HISTORY:
 * 2003-01-24: I've been using this program for many years, but I couldn't
 * find any of my old sources for it, so I wrote it from scratch AGAIN today.
 * So I'll call this version 1.0.
 *
 * 2003-01-28: v1.1 - Freq can now read from files named on its command line.
 * A dash argument ("-") on the command line means standard input. I also
 * added the agregate, hex, percent, and zero modes in this release. The
 * usage() function has been updated to reflect this new capability and syntax.
 *
 * TODO-1: There are enough options now to justify the use of getopt(). This
 * would also facilitate the ability to turn options back off as well.
 *
 * TODO-2: It might be nice to be able to specify the precision of the
 * percent mode output either by multiple -p options or by an argument to -p.
 *
 * TODO-3: Add a -g (for "graph") to change the output from a tabular format
 * to a histogram (one line per character value).
 *
 * ABSTRACT:
 * Freq's purpose in life is to do a sort of frequency analys on the
 * characters in a file. It reads only from standard input and writes its
 * results only to standard output.
 *
 * The output consists of a table of characters. Hex values for the characters
 * are along the top and left of the output. The body of the table contains
 * raw counts of each character found in the file.
 *
 * Freq is particularly useful for discovering whether a file contains
 * unwanted control characters. I also use it for analyzing the type of line
 * endings that a file uses. For Microsoft text file, it is usually a bad
 * thing if the number of '\n' characters does not match the number of '\r'
 * characters.
 *
 * BUILDING INSTRUCTIONS:
 * I used gcc, so here's how that worked.
 *
 *    gcc -lm -o freq freq.c
 *
 * The -lm option was required in order to load the math library because I
 * used the log10() and ceil() functions to compute column widths from
 * base-10 integer values.
 */
#include <fcntl.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

/*
 * On systems that do not define O_LARGEFILE, set this value to 0 so that
 * it will not affect the value of the flag sent to open().
 */
#ifndef O_LARGEFILE
#define O_LARGEFILE 0
#endif

#define COLS 16 /* Number of columns in output. (MUST be an integral  */
		/* power of 2.)					      */

int agregate=0;
int hex=0;
int percent=0;
int verbose=0;
int zero=0;

unsigned long count[256];

int freq(int fd);
void freqout(void);
int usage(int rc);

/******************************************************************************
 * Count the the occurances of each distinct character that can be read from
 * the given file descriptor. Store these counts in the global count[] array.
 */
int freq(int fd) {
  unsigned char buf[8192];
  int width[COLS];
  int i,n;

  /* Count the occurances of each distinct character coming from stdin. */
  if (!agregate)
    memset(count,0,sizeof(count));
  while((n=read(fd,buf,sizeof(buf)))>0)
    for(i=0;i<n;++i)
      ++count[buf[i]];

  return 0;
} /* int freq(int fd) */

/******************************************************************************
 * Output the content of the global count[] array. This functionality was
 * removed fromthe freq() function in order to implement the -a command line
 * option.
 */
void freqout(void) {
  double p[256];
  int width[COLS];
  int i,n,w;

  /* Compute the column widths we'll need. */
  if (percent) { /* Percentage output needs space for fractional part. */
    double total=0;
    /* Compute the total character count. */
    for(i=0;i<256;++i)
      total+=count[i];
    /* Fill p[] with percentage values. */
    for(i=0;i<256;++i)
      p[i]=((double)count[i]/total)*100;
    /* Computer column widths for these percentages. */
    for(i=0;i<COLS;++i)
      width[i]=9;
    for(i=0;i<256;++i)
      if (width[i%COLS]<(int)p[i])
	width[i%COLS]=(int)p[i];
    for(i=0;i<COLS;++i)
      width[i]=(int)ceil(log10(width[i]))+3;
  }
  else { /* We must compute the width of each column individually. */
    for(i=0;i<COLS;++i)
      width[i]=99; /* Require a minimum of 2 characters for column headings. */
    for(i=0;i<256;++i)
      if (width[i%COLS]<count[i])
	width[i%COLS]=count[i];
    if (hex) {
      double log16;
      log16=log(16);
      for(i=0;i<COLS;++i)
	width[i]=(int)ceil(log(width[i])/log16)+1;
    }
    else
      for(i=0;i<COLS;++i)
	width[i]=(int)ceil(log10(width[i]))+1;
  }

  /* 
   * As an upper bound for indexing count[] during output, find the index
   * of the highest non-zero value in count[], round up to the next multiple
   * of COLS, and set n to that value.
   */
  for(n=255;n>0 && count[n]==0;--n);
  n=(n&~(COLS-1))+COLS;

  /* Verbose mode outputs a sort of cheat-sheet for the user. */
  if (verbose) {
    int nv;
    nv=n<=0x80?n:0x80; /* Don't try to print unprintable caracters. */
    for(i=0;i<nv;++i) {
      if ((i&(COLS-1))==0)
	printf("%02x",i);
      if (i<' ')
	printf("%*s%c",width[i%COLS]-1,"^",i+'@');
      else
	printf("%*c",width[i%COLS],i);
      if ((i&(COLS-1))==(COLS-1))
	puts("");
    }
  }

  /* Display the results. */
  if (verbose)
    printf("--"); /* We'll print a little divider if in verbose mode. */
  else
    printf("  ");
  for(i=0;i<COLS;++i)
    printf("%*s%02x",width[i]-2,"",i);
  puts("");
  for(i=0;i<n;++i) {
    if ((i&(COLS-1))==0)
      printf("%02x",i);
    if (percent)
      if (zero && p[i]==0.0)
	printf("%*s",width[i%COLS],". ");
      else
	printf("%*.1f",width[i%COLS],p[i]);
    else
      if (zero && count[i]==0)
	printf("%*c",width[i%COLS],'.');
      else
	if (hex)
	  printf("%*lx",width[i%COLS],count[i]);
	else
	  printf("%*lu",width[i%COLS],count[i]);
    if ((i&(COLS-1))==(COLS-1))
      puts("");
  }
} /* void freqout() */

/******************************************************************************
 * Display a brief message describing how to use this program.
 */
int usage(int rc) {
  puts("usage: freq [-ahv] [-] [file]...\n"
      "-? shows this usage message.\n"
      "-a agregates all input files into one output table.\n"
      "-h outputs counts in hexadecimal rather than decimal.\n"
      "-p outputs counts in percentages rather than as raw counts. -p takes\n"
      "   precedence over -h.\n"
      "-v displays an ASCII chart above the normal output.\n"
      "-z replaces zero counts with \".\" entries for the sake of visual\n"
      "   clarity.\n"
      "\n"
      "Freq performs a sort of frequency analysis on its input files. Its\n"
      "output for each file consists of a table that shows the number of\n"
      "occurrances of each character. Output is truncated when all\n"
      "remaining lines of output would show nothing but zero counts, so\n"
      "output from text files typically only go down to character 0x7f.");

  return rc;
} /* int usage(int rc) */

/******************************************************************************
 * Handle command line options and arguments. Call freq() and freqout() as
 * appropriate.
 */
int main(int argc,char **argv) {
  int args=0; /* This will count the arguments we process. */

  /* Handle any command line switches. */
  while(*++argv) {
    char *arg;
    arg=*argv;
    if (*arg=='-') {
      if (arg[1])
	while(*++arg)
	  switch(*arg) {
	  case 'a':
	    ++agregate;
	    memset(count,0,sizeof(count));
	    break;
	  case 'h':
	    ++hex;
	    break;
	  case 'p':
	    ++percent;
	    break;
	  case 'v':
	    ++verbose;
	    break;
	  case 'z':
	    ++zero;
	    break;
	  default:
	    return usage(1);
	  }
      else {
	++args;
	freq(fileno(stdin));
	if (!agregate) {
	  puts("stdin:");
	  freqout();
	}
	continue;
      }
    }
    else {
      int fd;
      ++args;
      if ((fd=open(arg,O_RDONLY|O_NOCTTY|O_LARGEFILE))<0) {
	perror(arg);
	return 1;
      }
      freq(fd);
      close(fd);
      if (!agregate) {
	printf("%s:\n",arg);
	freqout();
      }
    }
  }
  if (args==0) { /* If we've done no work so far, read from standard input. */
    freq(0);
    if (!agregate) {
      puts("stdin:");
      freqout();
    }
  }
  if (agregate) {
    puts("agregate counts:");
    freqout();
  }
  
  return 0;
} /* int main(int argc,char **argv) */
