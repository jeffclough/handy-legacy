#include <errno.h>
#include <fcntl.h>
#include <libgen.h> /* for basename() */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/*
 * ELEMENTS(a), assuming that a is an array, evaluates to the number of
 * elements declared for that array.
 */
#define ELEMENTS(a) (sizeof(a)/sizeof(*a))

char *progname;
int usage(int rc);
int secdel(const char* filename);

/******************************************************************************
 * Securely delete every file given as an argument to this command.
 */
int main(int argc,char **argv) {
  int rc,badrc;

  /* Get the name of this program. */
  progname=basename(*argv);

  /* Verify that we have a good command line. */
  if (argc<2)
    return usage(1);

  /* Securely delete every file named on the command line. */
  badrc=0;
  while(*++argv) {
    if ((rc=secdel(*argv))!=0) {
      badrc=rc;
      perror(*argv);
    }
  }

  /* If an error occurred on any file, return the code for the last such file.
   * Otherwise, return a value of 0.
   */
  return badrc;
} /* int main(int argc,char **argv) */

/******************************************************************************
 * Securely delete the given file. This involves overwriting it with various
 * bits, truncating it, and then unlinking it. Return non-zero if there is
 * an error during this process.
 */
int secdel(const char* filename) {
  static unsigned char buf[256];
  static unsigned char bytes[]={0xaa,0x55};
  struct stat sb;
  unsigned char ch;
  unsigned long fsize; /* (size of file) / 256 */
  int f,i,j,rc;

  if ((f=open(filename,O_RDWR))<0) return errno;
  if (fstat(f,&sb)) return errno;
  fsize=sb.st_size/sizeof(buf)+1;
  for(i=0;i<=ELEMENTS(bytes);++i) {
    if (i<ELEMENTS(bytes))
      memset(buf,bytes[i],sizeof(buf));
    else {
      srand(time(NULL)); /* In case sranddev() fails. */
      /*sranddev(); not supported on Linux */
      for(j=0;j<ELEMENTS(buf);++j)
	buf[j]=(unsigned char)(rand()&0xff);
    }
    for(j=0;j<fsize;++j)
      write(f,(void*)buf,sizeof(buf));
  }
  close(f);

  /* Truncate this file to 0 bytes. */
  f=open(filename,O_RDWR|O_TRUNC);
  close(f);

  /* Remove this file from the filesystem. */
  rc=unlink(filename);
  return rc;
} /* int secdel(const char* filename) */

/******************************************************************************
 * Tell the user what this program does and how to call it.
 */
int usage(int rc) {
  fprintf(stderr,"Usage: %s file ...\n",progname);
  fputs("Every file given as an argument is securely (irretrievably) deleted.\n",stderr);
  return rc;
}
