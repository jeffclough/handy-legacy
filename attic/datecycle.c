/******************************************************************************
 * SYNOPSIS
 *  datecycle [-nTvz] [-f fmt] [-g group] [-l count[h|d|w|m|y|K|M|G]]
 *	      [-m mode] [-o old_dir] [-u user] path ...
 *
 * DESCRIPTION
 *  datecycle maintains the specified number, period, or size of previous
 *  versions of the file secified by path by renaming the file with a suffix
 *  corresponding to the current date and time, and then removing the oldest
 *  versions of that file until the limit of previous files is met.
 *
 *  If there is an error while processing a given path argument, an
 *  appripriate error message is written to standard error and then
 *  processing continues with any remaining path arguments.
 *
 *  -f specifies the format of the suffix to be appended to the name of the
 *     file in question in order to distinguish them from each other. The
 *     strftime() function's format syntax is used here, and it defaults to
 *     ".%Y%m%d%H%M". Observe that the '.' that separates the name of the
 *     original file from the data given in the suffix is part of the 
 *     suffix format. The TZ environment variable is used in the date and
 *     time that are formatted into the suffix.
 *
 *  -g specifies the group that should own created files.
 *
 *  -l specifies the limit of previous versions of a given file to keep. It
 *     defaults to a value of "14d", which keeps 14 days of versions of the
 *     file. If count ends with h, d, w, m, or y, then any files older than
 *     count hours, days, weeks, months, or years are deleted. If count ends
 *     with K, M, or G, then the oldest version of the file in question is
 *     deleted until the total size of all previous versions is less than
 *     count kilobytes, megabytes, or gigabytes. No units are specified,
 *     then count is simply the number of previous version of the flie to
 *     be kept.
 *
 *  -m specifies octal permissions to set any created files to.
 *
 *  -n tells datecycle to only pretend to age file files in question.
 *     Operations that would have been performed will be described in text
 *     written to standard output instead.
 *
 *  -o specifies the directory where previous versions of the file in
 *     question are to be placed and can be found. This defaults to the
 *     directory where the original file's dreictory.
 *
 *  -T tells datecycle to use the current date and time when aging path.
 *     The default behavior is to use the time of path's last modification.
 *
 *  -u specifies the user who should own created files.
 *
 *  -v turns on verbose mode, sending diagnostic messages to standard
 *     error.
 *
 *  -V prints the version of datecycle to standard output.
 *
 *  -z specifies that path is to be cycled, even if it is an empty file.
 *     The default behavior is that the file specified by path will be
 *     ignored if it has a size of zero bytes.
 *
 * EXIT STATUS
 *   0 - Cycle completed without incident.
 *   1 - path not found.
 *   2 - access violation.
 *   3 - Unsupported time format ("%Ex" or "%Ox")
 *  10 - Invalid command line option or missing argument.
 *
 * BUGS
 *  In order to keep the code simple, 31 days are assumed to be in every
 *  month, and only 365 days are assumed to be in ever year.
 *
 *  If an error is encountered while cycling any of a list of paths
 *  given on the command line, datecycle's exit status will reflect only
 *  the last error encountered. 
 *****************************************************************************/

#include <ctype.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <libgen.h> /* For dirname() and basename() */
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include "ls_class.h"

#define VERSION "datecycle v1.0, compiled " __DATE__ " " __TIME__ "\n" \
		"Copyright Georgia Institute of Technology, 2004"

#ifndef O_LARGEFILE
  #define O_LARGEFILE 0
#endif

#define DEBUG printf(__FILE__ "(%d)\n",__LINE__);
#define DBG printf(__FILE__ "(%d): ",__LINE__);

/* Set some default behaviors for this program.
 */
#define DEFAULT_FORMAT ".%Y%m%d%H%M"

/* Define some exit status values.
 */
#define ERROR_NONE    0
#define ERROR_NOPATH  1
#define ERROR_NODIR   2
#define ERROR_ACCESS  3
#define ERROR_SPACE   4
#define ERROR_BADFMT  5
#define ERROR_UIDGID  6
#define ERROR_CMDLINE 10

/* Define some bitwise flag values for datecycle().
 */
#define DC_ZERO    1
#define DC_FAKE    2
#define DC_VERBOSE 4
#define DC_CURTIME 8

/* Define modes for max_time_length() function.
 */
#define MTL_FILENAME  0x01 /* Allow only characters valid for file names.  */
#define MTL_SUFFIX    0x00 /* Return size needed for strftime(3)'s output. */
#define MTL_REGEXP    0x02 /* Return size needed for matching RE string.   */

/* Define a type for our limit value.
 */
typedef unsigned long limit_t;

char *progname=NULL;

int datecycle(const char *path,const char *fmt,const char *olddir,
	      const char* uname,const char* gname,int mode,int flags);
int remove_old_files(const char* path,const char* fmt,const char* olddir,
		     limit_t limit,int units,int flags);
static char *BaseName(const char* path);
static char *DirName(const char* path);
static int copyfd(int from_fd,int to_fd);
static int deletefromdir(const char* dir,const char* fn);
static off_t filesize(const char* path);
static blkcnt_t filesizek(const char* path);
static int filemode(const char* path);
static time_t filetime(const char* path,int which);
static int is_directory(const char* path);
static int is_regfile(const char* path);
static int ls(const char* dir,struct dirent*** entlist,
	      int (*select)(const struct dirent*),
	      int (*compar)(const struct dirent**,const struct dirent**));
static int max_time_length(const char* fmt,int mode,char* sRE,int nRE);

int main(int argc,char **argv) {
  /* Set default values for our command line options.
   */
  int   opt_flags=0;
  char *opt_fmt=".%Y%m%d%H%M";
  char *opt_limit="14d";
  limit_t opt_limit_val;
  int   opt_units='\0';
  char *opt_olddir=NULL;
  char *opt_uname=NULL;
  char *opt_gname=NULL;
  int	opt_mode=-1;
  int   opt_z=0;
  int ch,rc;
  char *cp;

  /* Get the basename of this executable file.
   */
  progname=BaseName(*argv);

  /* Parse our command line options.
   */
  while((ch=getopt(argc,argv,"f:g:l:m:no:Tu:vVz"))!=EOF)
    switch(ch) {
    case 'f':
      opt_fmt=optarg;
      break;
    case 'g':
      opt_gname=optarg;
      break;
    case 'l':
      if (optarg && *optarg)
	opt_limit=optarg;
      else {
	fprintf(stderr,"%s: -l must have a non-blank argument.\n",progname);
	return ERROR_CMDLINE;
      }
      break;
    case 'm':
      opt_mode=0;
      for(cp=optarg;*cp && *cp>='0' && *cp<='7';++cp)
	opt_mode=(opt_mode<<3)|((*cp)-'0');
      if (*cp) {
	fprintf(stderr,"%s: -m must have an octal argument.\n",progname);
	return ERROR_CMDLINE;
      }
      break;
    case 'n': /* -n implies -v */
      opt_flags|=DC_FAKE|DC_VERBOSE;
    case 'o':
      opt_olddir=optarg;
      break;
    case 'T':
      opt_flags|=DC_CURTIME;
    case 'u':
      opt_uname=optarg;
      break;
    case 'v':
      opt_flags|=DC_VERBOSE;
      break;
    case 'V':
      puts(VERSION);
      break;
    case 'z':
      opt_flags|=DC_ZERO;
    default:
      fprintf(stderr,"%s: unrecognized option: -%c\n",progname,ch);
      return ERROR_CMDLINE;
    }

  /* Parse our limit value a bit.
   */
  opt_limit_val=atoi(opt_limit);
  if (isdigit(opt_units=opt_limit[strlen(opt_limit)-1]))
    opt_units='\0';

  /* Validate any user or group information we've been given.
   */
  if (opt_uname && *opt_uname && !isdigit(*opt_uname) && !getpwnam(opt_uname)) {
    fprintf(stderr,"%s: unrecognized user name: %s\n",progname,opt_uname);
    return ERROR_UIDGID;
  }
  if (opt_gname && *opt_gname && !isdigit(*opt_gname) && !getgrnam(opt_gname)) {
    fprintf(stderr,"%s: unrecognized group name: %s\n",progname,opt_gname);
    return ERROR_UIDGID;
  }

  /* Cycle each file named on the command line.
   */
  rc=ERROR_NONE;
  for(;optind<argc;++optind) {
    int retcode;
    retcode=datecycle(argv[optind],opt_fmt,opt_olddir,opt_uname,opt_gname,opt_mode,opt_flags);
    if (retcode!=ERROR_NONE)
      switch(rc=retcode) {
	case ERROR_NOPATH:
	  fprintf(stderr,"%s: %s: file not found\n",progname,argv[optind]);
	  break;
	case ERROR_NODIR:
	  fprintf(stderr,"%s: %s: directory not found\n",progname,argv[optind]);
	  break;
	case ERROR_ACCESS:
	  fprintf(stderr,"%s: access violation while cycling %s\n",progname,argv[optind]);
	  break;
	case ERROR_SPACE:
	  fprintf(stderr,"%s: insufficient disk space while processing %s\n",progname,argv[optind]);
	  break;
	case ERROR_BADFMT:
	  fprintf(stderr,"%s: bad time format \"%s\"\n",progname,opt_fmt);
	  break;
	case ERROR_UIDGID:
	  fprintf(stderr,"%s: bad user or group id while cycling %s\n",progname,argv[optind]);
	  break;
	default:
	  fprintf(stderr,"%s: unrecognized error (%d) on file %s",progname,rc,argv[optind]);
      }
    else {
      retcode=remove_old_files(argv[optind],opt_fmt,opt_olddir,opt_limit_val,opt_units,opt_flags);
      if (retcode!=ERROR_NONE)
	switch(rc=retcode) {
	  case ERROR_NOPATH:
	    fprintf(stderr,"%s: %s: file not found\n",progname,argv[optind]);
	    break;
	  case ERROR_NODIR:
	    fprintf(stderr,"%s: %s: directory not found\n",progname,argv[optind]);
	    break;
	  case ERROR_ACCESS:
	    fprintf(stderr,"%s: access violation while cycling %s\n",progname,argv[optind]);
	    break;
	  case ERROR_SPACE:
	    fprintf(stderr,"%s: insufficient disk space while processing %s\n",progname,argv[optind]);
	    break;
	  case ERROR_BADFMT:
	    fprintf(stderr,"%s: bad time format \"%s\"\n",progname,opt_fmt);
	    break;
	  case ERROR_UIDGID:
	    fprintf(stderr,"%s: bad user or group id while cycling %s\n",progname,argv[optind]);
	    break;
	  default:
	    fprintf(stderr,"%s: unrecognized error (%d) on file %s",progname,rc,argv[optind]);
	}
    }
  }

  return ERROR_NONE;
} /* int main(int argc,char **argv) */

/******************************************************************************
 * NAME
 *  datecycle - Maintain previous versions of a given file by renaming them
 *  according to the current date.
 * 
 * SYNOPSIS
 *  typedef unsigned long limit_t;
 *  int datecycle(const char *path,const char *fmt,
 *                limit_t limit,int units,const char *olddir,
 *                const char* uname,const char* gname,int flags);
 *  
 * DESCRIPTION
 *  The datecycle() function renames, and possibly moves to a different
 *  directory, the file named by path.
 *   
 *  path is the name of the file to be aged and stored among its previous
 *  versions.
 *
 *  fmt is the format of the suffix (compatible with strftime()) to be used
 *  in the names of previous versions of path.
 *
 *  limit is the limit in terms of file count, age, or total size that
 *  determines which previous versions to keep and which ones to delete.
 *  While this is typically a positive integer value, the special cases of
 *  0 (indicating that no previous versions should be kept) and -1
 *  (indicating that no previous versions are to be deleted) are also
 *  permitted.
 *
 *  units is a single character that determines the units applied to the
 *  interpretation of the value of the limit argument above:
 *    '\0' or ' ' - keep only limit previous versions of this file.
 *    'y' -  keep only limit years's worth of previous copies of this file.
 *    'm' -  keep only limit month's worth of previous copies of this file.
 *    'w' -  keep only limit week's worth of previous copies of this file.
 *    'd' -  keep only limit day's worth of previous copies of this file.
 *    'h' -  keep only limit hour's worth of previous copies of this file.
 *    'K' -  keep only limit kilobytes of previous copies of this file.
 *    'M' -  keep only limit megabytes of previous copies of this file.
 *    'G' -  keep only limit gigabytes of previous copies of this file.
 *
 *  olddir may be used to specify the directory where previous versions of
 *  the file at hand are stored. If this is NULL or an empty string,
 *  previous versions of path are assumed to be stored in basedir(path).
 *  If specified, this directory will be created if necessary.
 *
 * EXIT STATUS
 *  0 - All is well.
 *  1 - The file path could not be found.
 *  2 - The target directory could not be found.
 *  3 - An access violation occurred.
 *  4 - Ran out of space while aging file.
 *  5 - Unsupported time format ("%Ex", "%Ox", "%n", "%t", or other bad char).
 *  6 - Bad user/group.
 */
int datecycle(const char *path,const char *fmt,const char *olddir,
	      const char* uname,const char* gname,int mode,int flags) {
  time_t tPath;
  char *sTargetDir=NULL;
  char *sSuffix=NULL;
  char *sPathBase=NULL;
  char *sAgedFile=NULL;
  char *sSuffixRE=NULL;
  char *sAgedSpec=NULL;
  char *sCompressedRE="(.(C|Z|gz|z))?$";
  char *cp,*s;
  int nTimeLength;
  uid_t nUid=-1;
  gid_t nGid=-1;
  ls_t *list=NULL;
  regex_t re;
  int i,n,rc=ERROR_NONE;

  /* Handle uname and gname parameters.
   */
  if (uname && *uname)
    if (strchr("012345678",*uname))
      nUid=atoi(uname);
    else {
      struct passwd *pw;
      if ((pw=getpwnam(uname))==NULL) {
	rc=ERROR_UIDGID;
	goto bailout;
      }
      else
	nUid=pw->pw_uid;
    }
  if (gname && *gname)
    if (strchr("0123456789",*gname))
      nGid=atoi(gname);
    else {
      struct group *gr;
      if ((gr=getgrnam(gname))==NULL) {
	rc=ERROR_UIDGID;
	goto bailout;
      }
      else
	nGid=gr->gr_gid;
    }

  /* Verify that path exists, and get its time of last modification. Treat
   * the attempt to age anything other than a regular as an access violation.
   * Also, do nothing to this file if it has a size of zero bytes, unless
   * the DC_ZERO flag is set, in which case we should process it normally.
   */
  if (path)
    if (is_regfile(path)) {
      tPath=flags&DC_CURTIME?time(NULL):filetime(path,1);
      if (mode==-1)
	mode=filemode(path);
    }
    else
      rc=errno==ENOENT?ERROR_NOPATH:ERROR_ACCESS;
  else
    rc=ERROR_NOPATH;
  if (rc!=ERROR_NONE)
    goto bailout;
  if (filesize(path)==0 && (flags&DC_ZERO)==0)
    goto bailout;

  /* Ensure that we have at least the default format and validate it. Then
   * compose the actual suffix that we'll use.
   */
  if (!fmt || !*fmt)
    fmt=DEFAULT_FORMAT;
  if ((nTimeLength=max_time_length(fmt,MTL_FILENAME|MTL_SUFFIX,NULL,0))<0)
    rc=ERROR_BADFMT;
  else {
    struct tm tm;
    sSuffix=malloc(nTimeLength+1);
    localtime_r(&tPath,&tm);
    if ((nTimeLength=strftime(sSuffix,nTimeLength+1,fmt,&tm))<1)
      rc=ERROR_BADFMT;
  }
  if (rc!=ERROR_NONE)
    goto bailout;

  /* Figure out where to put previous versions of path.
   */
  sTargetDir=olddir && *olddir?strdup(olddir):DirName(path);
  if (*(cp=sTargetDir+strlen(sTargetDir)-1)=='/')
    *cp='\0';
  if (!is_directory(sTargetDir)) {
    rc=errno==ENOENT?ERROR_NODIR:ERROR_ACCESS;
    goto bailout;
  }

  /* Compose the new name for our file.
   */
  sPathBase=BaseName(path);
  n=strlen(sTargetDir)+strlen(sPathBase)+nTimeLength+2;
  sAgedFile=malloc(n);
  snprintf(sAgedFile,n,"%s/%s%s",sTargetDir,sPathBase,sSuffix);

  /* Age the file. Use rename() in preference to copying the data.
   */
  if (flags&DC_VERBOSE)
    fprintf(stderr,"Rename %s\n"
		   "    to %s\n",path,sAgedFile);
  if ((flags&DC_FAKE)==0) {
    i=0;
    if ((is_regfile(sAgedFile) && (n=O_APPEND)==O_APPEND) ||
	((i=rename(path,sAgedFile))!=0 && (n=O_CREAT)==O_CREAT)) {
      int inf,outf;
      if (i && errno!=EXDEV) {
	rc=ERROR_ACCESS;
	goto bailout;
      }
      if ((outf=open(sAgedFile,O_RDWR|O_LARGEFILE|n,mode))<0) {
	rc=ERROR_ACCESS;
	goto bailout;
      }
      if ((inf=open(path,O_RDONLY|O_LARGEFILE,mode))<0) {
	close(outf);
	rc=ERROR_ACCESS;
	goto bailout;
      }
      if (copyfd(inf,outf))
	rc=errno==ENOSPC?ERROR_SPACE:ERROR_ACCESS;
      close(inf);
      close(outf);
      if (rc==ERROR_NONE)
	unlink(path);
    }
  }
  if (rc!=ERROR_NONE)
    goto bailout;

  /* Create an empty replacement for the file we've just aged. Set it's
   * user and group ownership if we've been given that information.
   */
  if (flags&DC_VERBOSE)
    fprintf(stderr,"Create %s\n",path);
  if ((flags&DC_FAKE)==0)
    if ((n=open(path,O_RDWR|O_CREAT,mode))<0)
      rc=ERROR_ACCESS;
    else
      close(n);
  if (nUid!=-1 || nGid!=-1) {
    if (flags&DC_VERBOSE)
      if (nUid==-1)
	printf("chgrp %d %s\n",nGid,path);
      else
	if (nGid==-1)
	  printf("chown %d %s\n",nUid,path);
	else
	  printf("chown %d:%d %s\n",nUid,nGid,path);
    if ((flags&DC_FAKE)==0 && chown(path,nUid,nGid))
      rc=ERROR_ACCESS;
  }
  if (rc!=ERROR_NONE)
    goto bailout;

  /* Yes, I know I'm using a goto. Get over it. The technique that I'm using
   * here is the closest thing this outdated language has to a destructor.
   * And it makes this function more readable and more maintainable.
   */
bailout:
  if (sTargetDir) free(sTargetDir);
  if (sSuffix) free(sSuffix);
  if (sPathBase) free(sPathBase);
  if (sAgedFile) free(sAgedFile);
  if (sSuffixRE) free(sSuffixRE);
  if (sAgedSpec) free(sAgedSpec);
  if (list) ls_destroy(&list);

  return rc;
} /* int datecycle(const char *path,const char *fmt,const char *olddir,
		   const char* uname,const char* gname,int mode,int flags) */

/******************************************************************************
 * NAME
 *  remove_old_files - Removes the minimum number of old versions of a file
 *  in order to meet the specified limit.
 *
 * SYNOPSIS
 *  int remove_old_files(const char* path,const char* fmt,const char* olddir,
 *			 limit_t limit,int units,int flags);
 *  
 * DESCRIPTION
 *  This function deletes the oldest versions of a given file until the
 *  specified limit (in terms of file count, date, or total size) is met.
 *  Old versions of path are sought in olddir if specified, or otherwise in
 *  the directory specified for path. The default directory is used as a
 *  last resort. A file is assumed to be an old version of path if it has
 *  the same filename, but with a suffix that strftime(3) might have
 *  produced from the format string in fmt. The remove_old_files() function
 *  also allows for further file extensions of .C, .Z, .z, and .gz.
 *
 *  path   is the full path name of the file which is to have the oldest of
 *	   its previous versions removed.
 *
 *  fmt	   is the strftime(3)-style format of the suffix to be applied to
 *	   the filename portion of path in order to specify old versions
 *	   of path.
 *
 *  olddir is the name of the directory where previous versions of path
 *	   may be found. If olddir is NULL or empty, the directory specified
 *	   in path is used. Failing this, the current directory is used.
 *
 *  limit  is the quantity of resources that previous versions of path
 *	   will be permitted to occupy. This may be in terms of number of
 *	   files, age or files, or total size of files, depending on the
 *	   value of the units argument below.
 *
 *  units  contains a single character that specifies the units in which the
 *	   limit argument above is expressed. Valid values for units are:
 *
 *	    'f' - number of files
 *	    'h' - hours
 *	    'd' - days
 *	    'w' - weeks
 *	    'm' - months
 *	    'y' - years
 *	    'K' - kilobytes
 *	    'M' - megabytes
 *	    'G' - gigabytes
 *
 *	    A null character ('\0') or a space (' ') are equivalent to 'f'.
 *	    For 'f', enough of the oldest versions of path will be removed
 *	    to bring the number of previous versions down to limit. For any
 *	    of the time units, any files older than that amount of time will
 *	    be removed. For the size units, enough of the oldest versions of
 *	    path will be removed so that the total size of the remaining
 *	    versions is no more than limit.
 * 
 * BUGS
 *  When limit is expressed in terms of time, it is converted to seconds in
 *  order to simplify this function's logic. For the sake of expediency,
 *  every month is assumed to have 31 days in it, and every year is assumed
 *  to have 385 days.
 */
int remove_old_files(const char* path,const char* fmt,const char* olddir,
		     limit_t limit,int units,int flags) {
  char *sTargetDir=NULL;
  char *sSuffix=NULL;
  char *sPathBase=NULL;
  char *sAgedFile=NULL;
  char *sSuffixRE=NULL;
  char *sAgedSpec=NULL;
  char *sCompressedRE="(.(C|Z|gz|z))?$";
  char *cp,*s;
  int nTimeLength;
  uid_t nUid=-1;
  gid_t nGid=-1;
  ls_t *list=NULL;
  regex_t re;
  limit_t x;
  int i,n,rc=ERROR_NONE;

  /* Figure out where to put previous versions of path.
   */
  sTargetDir=olddir && *olddir?strdup(olddir):DirName(path);
  if (*(cp=sTargetDir+strlen(sTargetDir)-1)=='/')
    *cp='\0';
  if (!is_directory(sTargetDir)) {
    rc=errno==ENOENT?ERROR_NODIR:ERROR_ACCESS;
    goto bailout;
  }

  /* Ensure that we have at least the default format and create an RE from
   * it for matching against previous versions of path in sTargetDir.
   */
  if (!fmt || !*fmt)
    fmt=DEFAULT_FORMAT;
  if ((n=max_time_length(fmt,MTL_FILENAME|MTL_REGEXP,NULL,0))<0) {
    rc=ERROR_BADFMT;
    goto bailout;
  }
  sSuffixRE=malloc(++n);
  if ((n=max_time_length(fmt,MTL_FILENAME|MTL_REGEXP,sSuffixRE,n))<0) {
    rc=ERROR_BADFMT;
    goto bailout;
  }
  sPathBase=BaseName(path);
  n+=strlen(sPathBase)+strlen(sCompressedRE)+2;
  sAgedSpec=malloc(n);
  snprintf(sAgedSpec,n,"^%s%s%s",sPathBase,sSuffixRE,sCompressedRE);

  /* Convert limit to the correct numeric unit: seconds for a time limit
   * or kilobytes for a size limit. Also modify our units parameter to be
   * one of 'f' (file count), 'k' (kilobytes), or 's' (seconds).
   */
  switch(units) {
    case '\0':
    case ' ':
    case 'f':
      units='f';
      break;
    case 'h':units='s';limit*=3600;break;
    case 'd':units='s';limit*=3600*24;break;
    case 'w':units='s';limit*=3600*24*7;break;
    case 'm':units='s';limit*=3600*24*31;break;
    case 'y':units='s';limit*=3600*24*365;break;
    case 'K':units='k';break;
    case 'M':units='k';limit<<=10;break;
    case 'G':units='k';limit<<=20;break;
    default:
      rc=ERROR_BADFMT;
      goto bailout;
  }

  /* Make a list of previous versions of this file, sorted by date.
   */
  if (regcomp(&re,sAgedSpec,REG_EXTENDED)) {
    fprintf(stderr,__FILE__"(%d): Cannot compile RE \"%s\"\n",__LINE__-1,sAgedSpec);
    rc=ERROR_BADFMT;
    goto bailout;
  }
  list=ls_create(sTargetDir,&re,ls_match_RE,ls_sort_date);
  regfree(&re); /* We only needed this RE to find the files. */
  /*
  if (flags&DC_VERBOSE)
    for(i=0;i<LS_COUNT(list);++i)
      puts(LS_FILENAME(list,i));
  */

  /* Finally, remove as many previous versions of this file as necessary
   * in order to stay within our limit.
   */
  switch(units) {
    case 'f':
      /* Remove all but the limit newest previous versions.
       */
      n=LS_COUNT(list)-limit;
      for(i=0;i<n;++i) {
	if (flags&DC_VERBOSE)
	  printf("remove %s/%s\n",sTargetDir,LS_FILENAME(list,i));
	if ((flags&DC_FAKE)==0)
	  deletefromdir(sTargetDir,LS_FILENAME(list,i));
      }
      break;
    case 'k':
      /* Remove all but the most recent limit kilobytes of previous versions.
       */
      x=0;
      for(i=LS_COUNT(list)-1;i>=0 && (x+=(LS_BLOCKS(list,i)/2))<=limit;--i);
      for(;i>=0;--i) {
	if (flags&DC_VERBOSE)
	  printf("remove %s/%s\n",sTargetDir,LS_FILENAME(list,i));
	if ((flags&DC_FAKE)==0)
	  deletefromdir(sTargetDir,LS_FILENAME(list,i));
      }
      break;
    case 's':
      /* Remove all files older than limit seconds.
       */
      time((time_t*)&x);
      x-=limit;
      for(i=0;i<LS_COUNT(list);++i)
	if (LS_MTIME(list,i)<x) {
	  if (flags&DC_VERBOSE)
	    printf("remove %s/%s\n",sTargetDir,LS_FILENAME(list,i));
	  if ((flags&DC_FAKE)==0)
	    deletefromdir(sTargetDir,LS_FILENAME(list,i));
	}
      break;
  }

bailout:
  if (sTargetDir) free(sTargetDir);
  if (sSuffix) free(sSuffix);
  if (sPathBase) free(sPathBase);
  if (sAgedFile) free(sAgedFile);
  if (sSuffixRE) free(sSuffixRE);
  if (sAgedSpec) free(sAgedSpec);
  if (list) ls_destroy(&list);

  return rc;
} /* int remove_old_files(const char* path,const char* fmt,const char* olddir,
			  limit_t limit,int units,int flags) */

/******************************************************************************
 * NAME
 *  BaseName - return a copy of the last element in path.
 *  DirName - return a copy  of all but the last element in path.
 *
 * SYNOPSIS
 *  char *BaseName(const char* path);
 *  char *DirName(const char* path);
 *
 * DESCRIPTION
 *  These functions are just wrappers around the common basename() and
 *  dirname() functions. The wrappers' purpose is to protect their path
 *  arguments from mutilation. Otherwise, their functionality is identical
 *  to the more common functions that they wrap.
 *
 * RETURN VALUE
 *  These fucntions return a pointer to a malloc()ed string that contains
 *  either the base name or directory name component of the given path.
 *  It is the caller's responsibility to free this memory. If path is
 *  NULL or empty, a value of NULL is returned.
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

char *DirName(const char* path) {
  char *s=NULL;
  if (path && *path) {
    char *cp=strdup(path);
    s=strdup(dirname(cp));
    free(cp);
  }
  return s;
} /* static char *DirName(const char* path) */

/******************************************************************************
 * NAME
 *  copyfd - copy data from one file descriptor to another.
 *
 * SYNOPSIS
 *  static int copyfd(int from_fd,int to_fd);
 *
 * DESCRIPTION
 *  The copyfd() function copies all data from the current position of
 *  from_fd to the current position of to_fd.
 *
 * RETURN VALUE
 *  Upon successful completion, a value of 0 is returned. Otherwise, a value
 *  of -1 is returned and errno may be consulted for further information
 *  regarding where to tune in your area.
 */
int copyfd(int from_fd,int to_fd) {
  char buf[16384];
  int n;
  while((n=read(from_fd,buf,sizeof(buf)))>0)
    if (write(to_fd,buf,n))
      return -1;
  return n;
} /* static int copyfd(int from_fd,int to_fd) */

/******************************************************************************
 * NAME
 *  deletefromdir - Removes a file from a given directory.
 *
 * SYNOPSIS
 *  int deletefromdir(const char* dir,const char* fn);
 *
 * DESCRIPTIONS
 *  The deletefromdir() function accepts the name of a directory and the 
 *  name of a file. It removes the from from the directory.
 *
 * RETURN VALUE
 *  A value of zero is returned on success, or -1 on failure, in which case
 *  errno can be queried to find out what went wrong.
 */
int deletefromdir(const char* dir,const char* fn) {
  char *path;
  int n;

  if (!fn || !*fn) {
    errno=ENOENT;
    return -1;
  }
  if (!dir || !*dir)
    dir=".";
  n=strlen(dir)+strlen(fn)+2;
  path=malloc(n);
  snprintf(path,n,"%s/%s",dir,fn);
  n=unlink(path);
  free(path);

  return n;
} /* int deletefromdir(const char* dir,const char* fn) */

/******************************************************************************
 * NAME
 *  filesize - Return the number of bytes a given file contains.
 *  fileblocks - Return the number of blocks a given file contains.
 *
 * SYNOPSIS
 *  #include <sys/types.h>
 *  off_t filesize(const char* path);
 *
 * RETURN VALUE
 *  This function returns the number of bytes that path contains. It returns
 *  a value of -1 on error.
 *
 * BUGS
 *  The filesizek() function returns a value that is half of stat(s)'s
 *  512-byte block count for the given file. Since this division is performed
 *  with truncation rather than rounding, filesizek() tends more toward
 *  under-reporting the size of a file than toward exagerating it.
 */
off_t filesize(const char* path) {
  struct stat buf;
  return stat(path,&buf)?-1:buf.st_size;
} /* off_t filesize(const char* path) */

blkcnt_t filesizek(const char* path) {
  struct stat buf;
  return stat(path,&buf)?-1:buf.st_blocks>>1;
} /* blkcnt_t filesizek(const char* path) */

/******************************************************************************
 * NAME
 *  filemode - returns the integer value of the given file's permissions mode.
 *
 * SYNOPSIS
 *  int filemode(const char* path);
 *
 * RETURN VALUE
 *  This function returns the numeric permissions mode of the file named by
 *  path.
 */
int filemode(const char* path) {
  struct stat buf;
  return stat(path,&buf)?-1:buf.st_mode;
} /* int filemode(const char* path) */

/******************************************************************************
 * NAME
 *  filetime - return the creation, modification, or access time of a file.
 *
 * SYNOPSIS
 *  time_t filetime(const char* path,int which);
 *
 * DESCRIPTION
 *  The filetime() function returns either the creation, modification, or
 *  access time on a file, depending on the value of which, which is encoded
 *  as follows:
 *
 *    0 - Creation time is returned.
 *    1 - Modification time is returned.
 *    2 - Access  time is returned.
 *
 * RETURN VALUE
 *  The requested time, in seconds since the Epoch, is returned if all
 *  goes well. Otherwise, if the file does not exist or for some other
 *  reason cannot be statted, a value of -1 is returned.
 */
time_t filetime(const char* path,int which) {
  struct stat buf;
  if (stat(path,&buf)==0)
    return which==0?buf.st_ctime:which==1?buf.st_mtime:buf.st_atime;
  return -1;
} /* time_t filetime(const char* path,int which) */

/******************************************************************************
 * NAME
 *  is_directory - Determine whether a given path specifies a directory.
 *  is_regfie - Determine whether a given path specifies a regular file.
 *
 * SYNOPSIS
 *  int is_directory(const char* path);
 *  int is_regfile(const char* path);
 *
 * DESCRIPTION
 *  These functions use stat() to determine whether their respective string
 *  arguments identify a directory or a regular file. This means that
 *  symbolic links are followed and that the result is determined by what
 *  such a link points to rather than by the link itself.
 *
 * RETURN VALUE
 *  These functions return a non-zero integer value if their respective
 *  conditions are met (e.i. is_regfile(s) return a non-zero value if s
 *  is the name of a regular file). Otherwise, a value of 0 is returned.
 */
int is_directory(const char* path) {
  struct stat buf;
  return stat(path,&buf)==0 && S_ISDIR(buf.st_mode);
} /* int is_directory(const char* path) */

int is_regfile(const char* path) {
  struct stat buf;
  return stat(path,&buf)==0 && S_ISREG(buf.st_mode);
} /* int is_directory(const char* path) */

/******************************************************************************
 * NAME
 *  max_time_length - Given a format string suitable for expansion by
 *  strftime(3), determine the maximimum length of the expanded string, the
 *  size of a regular expression string matching strftime(3)'s output, or
 *  generate such a string expression.
 *
 * SYNOPSIS
 #  #define MTL_FILENAME  0x01
 #  #define MTL_SUFFIX    0x00
 #  #define MTL_REGEXP    0x02
 *  int max_time_length(char *fmt,int mode,char* sRE,int nRE);
 *
 * DESCRIPTION
 *  The max_time_length() function determines the maximum size string that
 *  strftime() will need in order to expand a given time format.
 *
 *  fmt points to the format string. See strftime(3) for details.
 *
 *  mode is a bit-encoded integer value that determines how max_time_length()
 *  behaves:
 *    MTL_FILENAME tells max_time_length() to disallow characters that are
 *		   not valid components of filenames.
 *    MTL_SUFFIX   tells max_time_length() to add up the maximum size of a
 *		   string that strftime(3) will need to output an arbitrary
 *		   time using the provided format.
 *    MTL_REGEXP   tells max_time_length() to add up the maximum size of a
 *		   string that holds a regular expression that will match
 *		   strftime(3)'s output for the provided format.
 *  When specifying a value for mode, exactly one of MTL_SUFFIX and MTL_REGEXP
 *  may be used.
 *
 *  sRE points to a buffer that is to receive a regular expression that will
 *  match strftime(3)'s output for the given format. If sRE is NULL, or if
 *  MTL_REGEXP is not specified as a component of mode's value, no such
 *  string will be composed or stored.
 *
 *  n is the number of bytes in the buffer that s points to.
 *
 * RETURN VALUE
 *  The max_time_length() function returns the maximum number of characters
 *  (not including the null terminator) that strftime() requires to expand
 *  a given format string. If the format string is found to be invalid in
 *  some way, a value of -1 is returned.
 */
int max_time_length(const char *fmt,int mode,char* sRE,int nRE) {
  struct tm tm;
  time_t t;
  char f[4]="%x",s[128];
  int i,j,l,m,n=0;

  /* Construct a valid tm struct. */
  time(&t);
  localtime_r(&t,&tm);

  /* Find strftime()'s maximum expansion of the format we've been given. */
  if (fmt)
    for(;*fmt;++fmt) {
      if (*fmt=='%')
	switch(f[1]=*++fmt) {
	  case 'a': /* abbreviated name of day of week */
	  case 'A': /* full name of day of week        */
	    if (mode&MTL_REGEXP) {
	      char *field="[a-z]{2,}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	    }
	    else
	      for(m=i=0;i<7;++i) {
		tm.tm_wday=i;
		l=strftime(s,sizeof(s),f,&tm);
		if (l>m)
		  m=l;
	      }
	    n+=m;
	    break;
	  case 'b': /* abbreviated name of month  */
	  case 'B': /* full name of month         */
	  case 'h': /* synonymous with "%b"       */
	    if (mode&MTL_REGEXP) {
	      char *field="[a-z]{2,}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	    }
	    else
	      for(m=i=0;i<12;++i) {
		tm.tm_mon=i;
		l=strftime(s,sizeof(s),f,&tm);
		if (l>m)
		  m=l;
	      }
	    n+=m;
	    break;
	  case 'c': /* preferred date and time representation for locale */
	    if (mode&MTL_REGEXP) {
	      char *field=".*"; /* This might be anything. */
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	    }
	    else
	      for(m=i=0;i<12;++i)
		for(j=0;j<7;++j) {
		  tm.tm_mon=i;
		  tm.tm_wday=j;
		  l=strftime(s,sizeof(s),f,&tm);
		  if (l>m)
		    m=l;
		}
	    n+=m;
	    break;
	  case 'r': /* usually synonymous with "%I:%H:%M %p" */
	    if (mode&MTL_REGEXP) {
	      char *field=".*"; /* This might be anything. */
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	    }
	    else {
	      m=strftime(s,sizeof(s),f,&tm);
	      tm.tm_hour=23-tm.tm_hour; /* Cross the meridian. */
	      l=strftime(s,sizeof(s),f,&tm);
	      if (l>m)
		m=l;
	    }
	    n+=m;
	    break;
	  case 's': /* decimal number of seconds since Epoch */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]+";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=strftime(s,sizeof(s),f,&tm);
	    break;
	  case 'x': /* preferred date format without time    */
	  case 'X': /* preferred time format without date    */
	  case 'z': /* time-zone as hour offset from GMT     */
	  case 'Z': /* time-zone, name, or abbreviation      */
	  case '+': /* date and time in date(1) format       */
	    if (mode&MTL_REGEXP) {
	      char *field=".*"; /* This might be anything. */
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=strftime(s,sizeof(s),f,&tm);
	    break;
	  case 'n': /* %n becomes a single new-line caracter */
	  case 't': /* %t becomes a single tab character     */
	  case '%': /* a litteral percent character          */
	    if (mode & MTL_FILENAME)
	      return -1;
	    if (mode&MTL_REGEXP) {
	      char field[2]="-";
	      switch(f[1]) {
		case 'n':*field='\n';break;
		case 't':*field='\t';break;
		case '%':*field='%';break;
	      }
	      m=1;
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      ++n;
	    break;
	  case 'u': /* numeric day of week (1-7), 1=Monday              */
	  case 'w': /* numeric day of week (0-6), 0=Sunday              */
	    if (mode&MTL_REGEXP) {
	      char *field="[0=9]";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      ++n;
	    break;
	  case 'p': /* either "AM" or "PM"                              */
	  case 'P': /* either "am" or "pm" (backward, but true)         */
	    if (mode&MTL_REGEXP) {
	      char *field="[AaPp][Mm]";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=2;
	    break;
	  case 'C': /* century (year/100) expressed as two digits       */
	  case 'd': /* day of month as a 2-digit decimal number         */
	  case 'g': /* 2-digit year, based on week number               */
	  case 'H': /* 2-digit hour, from "00" to "23"                  */
	  case 'I': /* 2-digit hour, from "01" to "12"                  */
	  case 'l': /* 2-digit hour, from " 1" to "12"                  */
	  case 'm': /* 2-digit month, from "01" to "12"                 */
	  case 'M': /* 2-digit minute, from "00" to "59"                */
	  case 'S': /* 2-digit second, from "00" to "61" (leap seconds) */
	  case 'U': /* 2-digit week number, from "00" to "53"           */
	  case 'V': /* 2-digit week number, from "01" to "53"           */
	  case 'W': /* 2-digit week number, from "00" to "53"           */
	  case 'y': /* 2-digit year without century, from "00" to "99"  */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]{2}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=2;
	    break;
	  case 'e': /* same as %d, but space replaces leading zero      */
	  case 'k': /* 2-digit hour, from " 0" to "23"                  */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9 ][0-9]";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=2;
	    break;
	  case 'j': /* 3-digit day of year, from "001" to "366"         */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]{3}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=3;
	    break;
	  case 'G': /* 4-digit year, based on week number               */
	  case 'Y': /* 4-digit year, from "1970" to "2038"              */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]{4}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=4;
	    break;
	  case 'R': /* synonymous with "%H:%M"                          */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]{2}:[0-9]{2}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=5;
	    break;
	  case 'D': /* synonymous with "%m/%d/%y"                       */
	    if (mode&MTL_FILENAME)
	      return -1;
	    if (mode&MTL_REGEXP) {
	      char *field="([0-9]{2}/){2}[0-9]{2}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=8;
	    break;
	  case 'T': /* synonymous with "%H:%M:%s"                       */
	    if (mode&MTL_REGEXP) {
	      char *field="([0-9]{2}:){2}[0-9]{2}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=8;
	    break;
	  case 'F': /* synonymous with "%Y-%m-%d"                       */
	    if (mode&MTL_REGEXP) {
	      char *field="[0-9]{4}(-[0-9]{2}){2}";
	      m=strlen(field);
	      if (sRE)
		if (n+m<nRE)
		  strcpy(sRE+n,field);
		else
		  return -1;
	      n+=m;
	    }
	    else
	      n+=10;
	    break;
	  case 'E': /* We don't support this extension.                 */
	  case 'O': /* Or this one.                                     */
	  default:  /* Silly user, what are you thingking!?             */
	    return -1;
	}
      else {
	if (mode & MTL_FILENAME &&
	    (*fmt<' ' || *fmt>'~' || strchr("<>|",*fmt)!=NULL))
	  return -1;
	if (mode&MTL_REGEXP) {
	  char field[]="^.[$()|*+?{\\";
	  m=0;
	  if (strchr(field,*fmt)) /* Must escape these RE tokens */
	    field[m++]='\\';
	  field[m++]=*fmt;
	  field[m]='\0';
	  if (sRE)
	    if (n+m<nRE)
	      strcpy(sRE+n,field);
	    else
	      return -1;
	  n+=m;
	}
	else
	  ++n;
      }
    }
  return n;
} /* int max_time_length(const char *fmt,int mode,char* sRE,int nRE) */
