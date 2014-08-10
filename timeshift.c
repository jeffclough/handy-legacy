#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <utime.h>

#define ATIME 1
#define MTIME 2

/*
 * These macros evaluate to the number of seconds in each time period.
 */
#define MINUTES	60
#define HOURS	(MINUTES * 60)
#define DAYS	(HOURS * 24)
#define WEEKS	(DAYS * 7)
#define YEARS	(DAYS * 365)

typedef struct {
  unsigned y,M,w,d,h,m,s; /* years, months, weeks, days, hours, mins, secs */
  int sign;		  /* <0 to reverse time, or >0 to advance it	   */
} timeshift_t;

char *progname;

char *BaseName(const char* path);
int showtime(char *path);
int timeshift(int timetype,int dt,char *path);
int usage(int rc);

/* I just used this function for debugging. It's small, so I left it in. */
char *stringtime(time_t t) {
  static char s[64];
  strftime(s,sizeof(s),"%Y-%m-%d %H:%M:%S",localtime(&t));
  return s;
}

int main(int argc,char **argv) {
  int timetype=0;
  int sign,dt=0;
  char *cp;

  /* Get the basename of this executable file.
   */
  progname=BaseName(*argv);

  /* Parse our timeshift parameter.
   */
  if (argc<2)
    return usage(0);
  if (strcmp(argv[1],"0")==0) {
    dt=0;
    ++argv;
  }
  else {
    for(cp=*++argv;*cp && *cp!='-' && *cp!='+';++cp)
      switch(*cp) {
	case 'a':timetype|=ATIME;break;
	case 'm':timetype|=MTIME;break;
	default: 
	  if (isdigit(*cp))
	    fprintf(stderr,"%s: missing '+' or '-' before time shift value.\n",
		progname);
	  else
	    fprintf(stderr,"%s: %c is not a valid type of time.\n",progname,*cp);
	  return usage(2);
      }
    if (*cp!='-' && *cp!='+') {
      fprintf(stderr,"%s: Missing '-' or '+' in timeshift value.\n",progname);
      return usage(2);
    }
    sign=*cp++=='+'?1:-1;
    if (!*cp) {
      fprintf(stderr,"%s: No time found in timeshift value.\n",progname);
      return usage(2);
    }
    /* Now parse the time components from the remainder of s. */
    while(*cp) {
      /* Get the value of this component in v. */
      unsigned v=0;
      for(;isdigit(*cp);++cp)
	v=v*10+*cp-'0';
      /* Get the units of this value and store it accordingly. */
      switch(*cp++) {
	case 'y': v*=YEARS; break;
	case 'w': v*=WEEKS; break;
	case 'd': v*=DAYS; break;
	case 'h': v*=HOURS; break;
	case 'm': v*=MINUTES; break;
	case 's':
	case '\0':
	  break;
	default:
	  fprintf(stderr,"%s: %c is not a valid type of time.",progname,*(cp-1));
	  return usage(2);
      }
      dt+=sign*v;
    }
  }

  /* Now timshift each of the paths on our command line by dt seconds. */
  if (!*++argv) {
    fprintf(stderr,"%s: no path found on command line.\n",progname);
    return usage(2);
  }
  for(;*argv;++argv)
    if (dt) {
      if (timeshift(timetype,dt,*argv)) {
	fprintf(stderr,"%s: %s: %s\n",progname,*argv,strerror(errno));
	return 1;
      }
    }
    else /* A dt value of 0 just shows the time for each file. */
      showtime(*argv);

  return 0;
} /* int main(int argc,char **argv) */

/******************************************************************************
 * Get the basename of path, but protect it from mutilation.
 */
char *BaseName(const char* path) {
  char *s=NULL;
  if (path && *path) {
    char *cp=strdup(path);
    s=strdup(basename(cp));
    free(cp);
  }
  return s;
} /* static char *BaseName(const char* path) */

/******************************************************************************
 * Offset the access and/or modification times of path by the number of seconds
 * given in dt. The timetype value is a bitwise combination of ATIME and
 * MTIME, and will default to ATIME|MTIME if niether is given, in which
 * case both access and modification times of path will be set. A value of 0
 * is returned on success. Otherwise, errno indicates what went wrong.
 */
int timeshift(int timetype,int dt,char *path) {
  struct stat pi;
  struct utimbuf tb;

  /* Default to setting both access and modification time. */
  if ((timetype & (ATIME|MTIME)) == 0)
    timetype|=ATIME|MTIME;

  /* Get the current attributes of this directory entry. */
  if (stat(path,&pi))
    return 1;


  /* Offset the time(s) by the amount given in dt. */
  if (timetype & ATIME)
    pi.st_atime+=dt;
  if (timetype & MTIME)
    pi.st_mtime+=dt;
  

  /* Update the attributes of the given directory entry with its new times. */
  tb.actime=pi.st_atime;
  tb.modtime=pi.st_mtime;
  if (utime(path,&tb))
    return 1;

  return 0;
} /* int timeshift(int timetype,timeshift_t *ts,char *path) */

/******************************************************************************
 * Just show the time of the given file at YYYY-MM-DD HH:MM:SS.
 */
int showtime(char *path) {
  struct stat pi;

  if (stat(path,&pi))
    return 1;
  printf("%s %s\n",stringtime(pi.st_mtime),path);
  return 0;
} /* int showtime(char *path) */

/******************************************************************************
 * Breifly explain to stderr how to use this program. Return the value of rc.
 */
int usage(int rc) {
  int pnlen;
  pnlen=strlen(progname);
  fprintf(stderr,"\nusage: %s [am]{+|-}t path ...\n",progname);
  fputs("where t is a concatenation of at least one string of the form \"nu\"\n"
      "such that n is an unsigned integer value and u specifies the units\n"
      "expressed by that integer as 'y', 'w', 'd', 'h', 'm', or 's' to\n"
      "represent years, weeks, days, hours, minutes, or seconds. By default,\n"
      "both access and modification time are changed by the given time\n"
      "value, but placing an 'a' or 'm' before the sign on the time change\n"
      "will restrict the change to only access or modification\n"
      "time.\n\n",stderr);
  fprintf(stderr,"Example: %s +5h2m43s myfoto.jpg\n"
      "will advance the access and modification times of myfoto.jpg by\n"
      "5 hours, 2 minutes, and 43 seconds from their current values.\n",
      progname);
  return rc;
} /* int usage(int rc) */

