#include "ls_class.h"
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/******************************************************************************
 * NAME
 *  _select_all - provides a default select() function for ls_crete().
 *
 * RETURN VALUE
 *  This function always returns 1, ensuring that each directory entry 
 *  that ls_create() finds is regarded as selected.
 */
static int _select_all(const lsent_t* ent,void* data) {
  return 1;
} /* int _select_all(const lsent_t* ent,void* data) */

/******************************************************************************
 * NAME
 *  ls_match_RE - makes ls_create() find only filenames matching an RE.
 *  ls_match_not_RE - makes ls_create() find only filenames not matching an RE.
 *
 * DESCRIPTION
 *  These functions are provided as samples of proper select arguments to
 *  ls_create(). They might also be useful to you in and of themselves.
 *
 *  Both of these functions expect their data argument to point to a regex_t,
 *  so be sure to prepare one (by calling regcomp(3)) and passing a pointer
 *  to your regex_t as the data argument to ls_create().
 *
 * EXAMPLE
 *  Scan the current directory for files matching the RE "\.c$" (which is
 *  identical the shell wildcard pattern "*.c") and write their names to
 *  standard output in alphabetical order.
 *
 *  int main(void) {
 *    ls_t *list;
 *    regex_t re;
 *
 *    regcomp(&re,"\.c$",REG_EXTENDED);
 *    list=ls_create(NULL,&re,ls_match_RE,ls_sort_alpha);
 *    for(i=0;i<LS_COUNT(list);++i)
 *	puts(LS_FILENAME(list,i));
 *    ls_destroy(&list);
 *    regfree(&re);
 *
 *    return 0;
 *  }
 */
int ls_match_RE(const lsent_t* ent,void* data) {
  regex_t *preg=(regex_t*)data;
  return !regexec(preg,LSENT_FILENAME(ent),0,NULL,0);
}

int ls_match_not_RE(const lsent_t* ent,void* data) {
  regex_t *preg=(regex_t*)data;
  return regexec(preg,LSENT_FILENAME(ent),0,NULL,0);
}

/******************************************************************************
 * NAME
 *  ls_sort_alpha - makes qsort() sort lsent_t* array by filename.
 *  ls_sort_date - makes qsort() sort lsent_t* array by file date.
 *  ls_sort_size - makes qsort() sort lsent_t* array by file size.
 *
 * DESCRIPTION
 *  These functions are provided as samples of proper compar arguments to
 *  ls_create(). They might also be useful to you in and of themselves.
 *
 * REMEMBER!
 *  These functions take lsent_t** arguments, so remember to dereference
 *  the arguments before using them with the LSENT... macros.
 */
int ls_sort_alpha(const lsent_t** a,const lsent_t** b) {
  return strcmp(LSENT_FILENAME(*a),LSENT_FILENAME(*b));
}

int ls_sort_date(const lsent_t** a,const lsent_t** b) {
  return LSENT_MTIME(*a)-LSENT_MTIME(*b);
}

int ls_sort_size(const lsent_t** a,const lsent_t** b) {
  return LSENT_SIZE(*a)-LSENT_SIZE(*b);
}

/******************************************************************************
 * NAME
 *  ls_destroy - free all memory used by a given stuct ls.
 *
 * SYNOPSIS
 *  #include "ls_class.h"
 *  void ls_destroy(ls_t **list);
 *
 * DESCRIPTION
 *  The ls_destroy() function frees all memory that is managed by the given
 *  ls_t. This memory was allocated by ls_create().
 *
 *  Notice that a pointer to a pointer to a stuct ls is required. This is so
 *  that ls_destroy() can set the pointer to the ls_t to NULL after its
 *  memory has been freed, thus making it a little more difficult for the
 *  caller to use this pointer to reference memory that has been freed.
 *
 *  Calling ls_destroy() on a pointer to a (ls_t*) that has not been
 *  initialized by ls_create() will crash your program. Calling ls_destroy()
 *  on a pointer to NULL pointer, however, is allowed and ignored.
 *
 * EXAMPLE
 *  #include "ls_class.h"
 *
 *  int main(void) {
 *    ls_t *list;
 *    int i;
 *    list=ls_create(NULL,NULL,NULL);
 *    for(i=0;i<list->ent_count;++i) {
 *      .
 *      .                  {Process list of directory entries.      }
 *      .
 *    }
 *    ls_destroy(&list);   {Pass in pointer to pointer to ls_t.}
 *    ls_destroy(&list);   {This is superfluous, but permitted.     }
 *    return 0;
 *  }
 *
 */
void ls_destroy(ls_t **list) {
  if (list && *list) {
    if ((*list)->dir)
      free((*list)->dir);
    if ((*list)->path)
      free((*list)->path);
    if ((*list)->pent) {
      int i;
      for(i=0;i<(*list)->ent_count;++i)
	if ((*list)->pent[i])
	  free((*list)->pent[i]);
      free((*list)->pent);
    }
    free(*list);
    *list=NULL;
  }
} /* void ls_destroy(ls_t **list) */

/******************************************************************************
 * NAME
 *  ls_create - create a list of either all or a subset of the entries in a
 *  given directory.
 *
 * SYNOPSIS
 *  #include "ls_class.h"
 *  ls_t* ls_create(const char* dir,void* data,
 *		   int (*select)(const lsent_t*,void*),
 *		   int (*compar)(const lsent_t**,const lsent_t**));
 *
 * DESCRIPTION
 *  The ls_create() creates a ls_t on the heap and fills it with a list
 *  of directory entries from the given directory.
 *
 *  dir is the name of the directory to be scanned for entries. The "." and
 *  ".." directories, if they exist, are never included in this list. If dir
 *  is NULL or an empty string, the current direcoty (".") is used.
 *
 *  data is a pointer that will be passed to the select function that
 *  ls_create() calls on each file during the scan. ls_create() takes no
 *  action based on what data points to and does not modify it. It simply
 *  passes it to the select() function and nothing more. One common use for
 *  this is to pass a pointer to regex_t as this argument in order to let
 *  select() match filenames against a regular expression.
 *
 *  select is a pointer to a function accepting a pointer to a lsent_t
 *  and a void* to the callers data and returning a non-zero value if the
 *  ls_ent should be included is the list of scanned directory entries.
 *  Otherwise, it returns zero. If select is NULL, all directory entries
 *  will be selected. See the EXAMPLE section below for some sample select
 *  functions.
 *
 *  compar is a pointer to a function accepting two pointers (say a and b)
 *  to pointers to lsent_t and retrning an integer value to indicate which
 *  entry should appear before the other in a sorted list:
 *
 *    return	if
 *      <0	a<b
 *       0     a==b
 *      >0	a>b
 *
 *  There is a sample compar function in the EXAMPLE section below.
 *
 * RETURN VALUE
 *  The ls_crete() function returns a pointer to the ls_t that it
 *  creates. If none could be created, maybe because the specified directory
 *  doesn't exist or can't be read, a value of NULL is returned.
 *
 * EXAMPLE
 *  Scan the current directory for files matching the RE "\.c$" (which is
 *  identical the shell wildcard pattern "*.c") and write their names to
 *  standard output in alphabetical order.
 *
 *  Note in particular that while match_RE() takes an lsent_t* argument,
 *  sort_alpha() takes two lsent_t** arguments. be sure that you dereference
 *  these lsent_t** values before passing them to any of the LSENT_...
 *  macros.
 * 
 *  int match_RE(const lsent_t* ent,void* data) {
 *    regex_t *preg=(regex_t*)data;
 *    return !regexec(preg,LSENT_FILENAME(ent),0,NULL,0);
 *  }
 *
 *  int sort_alpha(const lsent_t** a,const lsent_t** b) {
 *    return strcmp(LSENT_FILENAME(*a),LSENT_FILENAME(*b));
 *  }
 *
 *  int main(void) {
 *    ls_t *list;
 *    regex_t re;
 * 
 *    regcomp(&re,"\.c$",REG_EXTENDED);
 *    list=ls_create(NULL,&re,match_RE,sort_alpha);
 *    for(i=0;i<LS_COUNT(list);++i)
 *      puts(LS_FILENAME(list,i));
 *    ls_destroy(&list);
 *    regfree(&re);
 * 
 *    return 0;
 *  }
 */
ls_t* ls_create(const char* dir,void* data,
    int (*select)(const lsent_t*,void*),
    int (*compar)(const lsent_t**,const lsent_t**)) {
  ls_t *list=NULL;
  struct stat stat_buf;
  DIR *dstream;
  struct dirent *dptr;
  int i,n;

  /* Allocate and initialize a ls_t.
   */
  list=(ls_t*)malloc(sizeof(ls_t));
  list->dir=NULL;
  list->pent=NULL;
  list->ent_count=0;

  /* If our dir parameter looks good, remember its value and allocate
   * and initialize our path and filename varaibles.
   */
  if (!dir || !*dir)
    dir=".";
  if (!stat(dir,&stat_buf) && S_ISDIR(stat_buf.st_mode)) {
    list->dir=strdup(dir);
    list->path=malloc(strlen(list->dir)+MAXNAMLEN+2);
    strcpy(list->path,list->dir);
    list->filename=list->path+strlen(list->path);
    list->filename[0]='/';
    list->filename++;
  }
  else
    goto bailout;

  /* In order to simplify subsequent logic, provide a default select
   * function if none was given by the caller.
   */
  if (!select)
    select=_select_all;

  /* Perform an initial scan just to count the directoy entiries.
   */
  if ((dstream=opendir(list->dir))!=NULL) {
    lsent_t *ent;
    ent=malloc(sizeof(lsent_t)+MAXNAMLEN);
    while((dptr=readdir(dstream))!=NULL)
      if (strcmp(dptr->d_name,".") && strcmp(dptr->d_name,"..")) {
	strcpy(list->filename,dptr->d_name);
	strcpy(ent->filename,dptr->d_name);
	if (!stat(list->path,&(ent->st)) && select(ent,data))
	  list->ent_count++;
      }
    /* Now allocate memory for the array and perform our second scan,
     * storing one ls_ent struct for every selected file.
     */
    list->pent=(lsent_t **)calloc(list->ent_count,sizeof(void*));
    rewinddir(dstream);
    i=0;
    while(i<list->ent_count && (dptr=readdir(dstream))!=NULL)
      if (strcmp(dptr->d_name,".") && strcmp(dptr->d_name,"..")) {
	strcpy(list->filename,dptr->d_name);
	strcpy(ent->filename,dptr->d_name);
	if (!stat(list->path,&(ent->st)) && select(ent,data)) {
	  n=sizeof(lsent_t)+strlen(ent->filename);
	  list->pent[i]=(lsent_t*)malloc(n);
	  memcpy(list->pent[i],ent,n);
	  ++i;
	}
      }
    list->ent_count=i; /* In case there are fewer entries on 2nd scan. */
    closedir(dstream);
  }
  else
    goto bailout;

  /* Finally, sort the results if we have a function for doing that.
   */
  if (compar)
    qsort(list->pent,list->ent_count,sizeof(void*),
	(int(*)(const void *, const void *))compar);
  goto nobailout;

  /* I'll make you a deal: When ANSI provides a formal destructor-like
   * mechanism for this archaic language, I'll stop using goto statements.
   */
bailout:
  if (list) ls_destroy(&list);

nobailout:
  return list;
} /* ls_t* ls_create(const char* dir,void* data,
		  int (*select)(const lsent_t*),
		  int (*compar)(const lsent_t**,const lsent_t**)) */

/******************************************************************************
 * NAME
 *
 * SYNOPSIS
 *
 * DESCRIPTION
 *
 * RETURN VALUE
 *
 */
const char* ls_path(const ls_t* list,const lsent_t* ent) {
  if (list && ent) {
    strncpy(list->filename,ent->filename,MAXNAMLEN+1);
    return list->path;
  }
  return NULL;
} /* const char* ls_path(const ls_t* list,const lsent_t* ent) */

/******************************************************************************
 * NAME
 *
 * SYNOPSIS
 *
 * DESCRIPTION
 *
 * RETURN VALUE
 *
 */
void ls_reorder(ls_t* list,int (*compar)(const lsent_t**,const lsent_t**)) {
  if (list && list->ent_count>1)
    qsort(list->pent,list->ent_count,sizeof(void*),
	  (int (*)(const void*,const void*))compar);
} /* void ls_reorder(ls_t* list,
		     int (*compar)(const lsent_t**,const lsent_t**)) */

#ifdef TEST

#include <string.h>

int usage(int rc) {
  puts("Usage: ls_class {[option ...] filespec} ...\n"
      "where option is an of\n"
      "	 -a sorts output alphabetically\n"
      "	 -d sorts output by date\n"
      "	 -s sorts output by size\n"
      "	 -v inverts regular expression matching\n"
      "\n"
      "filespec is a POSIX regular expression that is matched against\n"
      "filenames in the current directory.\n");
  return rc;
}

int main(int argc,char **argv) {
  /* Leave files unsorted by default. */
  int (*sortfunc)(const lsent_t**,const lsent_t**)=NULL;

  /* Match files by regular expression by default. */
  int (*selfunc)(const lsent_t*,void*)=ls_match_RE;

  if (argc<2)
    return usage(1);
  while(*++argv)
    if (**argv=='-') {
      char *cp;
      for(cp=(*argv)+1;*cp;++cp)
	switch(*cp) {
	  case 'a':
	    sortfunc=ls_sort_alpha;
	    break;
	  case 'd':
	    sortfunc=ls_sort_date;
	    break;
	  case 's':
	    sortfunc=ls_sort_size;
	    break;
	  case 'v':
	    selfunc=selfunc==ls_match_RE?ls_match_not_RE:ls_match_RE;
	    break;
	  default:
	    printf("Bad sort spec: %s\n",*argv);
	    return usage(1);
	}
    }
    else {
      ls_t *list;
      regex_t re;
      int i;
      printf("Matching against \"%s\"\n",*argv);
      if ((i=regcomp(&re,*argv,REG_EXTENDED))!=0) {
	char s[1024];
	regerror(i,&re,s,sizeof(s));
	printf("RE Error: %s\n",s);
	return usage(1);
      }
      if ((list=ls_create(NULL,&re,selfunc,sortfunc))==NULL) {
	perror("ls_create()");
	return 2;
      }
      for(i=0;i<LS_COUNT(list);++i) {
	char s[1024];
	strftime(s,sizeof(s),"%Y-%m-%d %H:%M:%S",
	    localtime(&LS_MTIME(list,i)));
	printf("%10lli  %s  %s\n",
	    LS_SIZE(list,i),s,LS_FILENAME(list,i));
      }
      putchar('\n');
      ls_destroy(&list);
      regfree(&re);
    }
} /* int main(int argc,char **argv) */

#endif
