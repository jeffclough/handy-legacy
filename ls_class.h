#include <regex.h>
#include <sys/types.h>
#include <sys/stat.h>

typedef struct {
  struct stat st;
  char filename[1];
} lsent_t;

typedef struct {
  char *dir;	  /* names the directory to be scanned */
  lsent_t **pent; /* points to an array of ls_ent      */
  int ent_count;  /* # of elements allocated for pent  */
  char *path;	  /* used to construct full path names */
  char *filename; /* used to construct full path names */
  void *data;	  /* points to caller's arbitrary data */
} ls_t;

/* The macros below provide only convenience for the coder and a little
 * protection for the data inside the ls_t and lsent_t structures. No
 * bounds checking or pointer validation is performed.
 *
 * l must be a pointer to ls_t.
 * i is an integer in the range [0..LS_COUNT(l)-1].
 * e must be a pointer to lsent_t.
 */

/* Get the number of lsent_t entries in ls_t l. */
#define LS_COUNT(l) (((const ls_t*)l)->ent_count)

/* Get a pointer to the ith lsent_t of ls_t l. */
#define LSENT(l,i) ((const lsent_t*)((l)->pent[i]))

/* Get the value of a given field of lsent_t e. */
#define LSENT_FILENAME(e) ((const char*)(((const lsent_t*)e)->filename))
#define LSENT_STAT(e)	  (*((const struct stat*)(&((e)->st))))
#define LSENT_MODE(e)	  (LSENT_STAT(e).st_mode)
#define LSENT_INO(e)	  (LSENT_STAT(e).st_ino)
#define LSENT_DEV(e)	  (LSENT_STAT(e).st_dev)
#define LSENT_RDEV(e)	  (LSENT_STAT(e).st_rdev)
#define LSENT_NLINK(e)	  (LSENT_STAT(e).st_nlink)
#define LSENT_UID(e)	  (LSENT_STAT(e).st_uid)
#define LSENT_GID(e)	  (LSENT_STAT(e).st_gid)
#define LSENT_SIZE(e)	  (LSENT_STAT(e).st_size)
#define LSENT_ATIME(e)	  (LSENT_STAT(e).st_atime)
#define LSENT_MTIME(e)	  (LSENT_STAT(e).st_mtime)
#define LSENT_CTIME(e)	  (LSENT_STAT(e).st_ctime)
#define LSENT_BLKSIZE(e)  (LSENT_STAT(e).st_blksize)
#define LSENT_BLOCKS(e)	  (LSENT_STAT(e).st_blocks)

/* Get the value of a given field of the ith lsent_t of ls_t l. */
#define LS_FILENAME(l,i)  LSENT_FILENAME(LSENT((l),(i)))
#define LS_MODE(l,i)	  LSENT_MODE(LSENT((l),(i)))
#define LS_INO(l,i)	  LSENT_INO(LSENT((l),(i)))
#define LS_DEV(l,i)	  LSENT_DEV(LSENT((l),(i)))
#define LS_RDEV(l,i)	  LSENT_RDEV(LSENT((l),(i)))
#define LS_NLINK(l,i)	  LSENT_NLINK(LSENT((l),(i)))
#define LS_UID(l,i)	  LSENT_UID(LSENT((l),(i)))
#define LS_GID(l,i)	  LSENT_GID(LSENT((l),(i)))
#define LS_SIZE(l,i)	  LSENT_SIZE(LSENT((l),(i)))
#define LS_ATIME(l,i)	  LSENT_ATIME(LSENT((l),(i)))
#define LS_MTIME(l,i)	  LSENT_MTIME(LSENT((l),(i)))
#define LS_CTIME(l,i)	  LSENT_CTIME(LSENT((l),(i)))
#define LS_BLKSIZE(l,i)	  LSENT_BLKSIZE(LSENT((l),(i)))
#define LS_BLOCKS(l,i)	  LSENT_BLOCKS(LSENT((l),(i)))

/* Wrapper macros for evaluating file modes. */
#define LSENT_ISREG(e)	  S_ISREG(LSENT_MODE(e))
#define LSENT_ISDIR(e)	  S_ISDIR(LSENT_MODE(e))
#define LSENT_CHR(e)	  S_CHR(LSENT_MODE(e))
#define LSENT_ISBLK(e)	  S_ISBLK(LSENT_MODE(e))
#define LSENT_ISFIFO(e)	  S_ISFIFO(LSENT_MODE(e))
#define LSENT_ISLNK(e)	  S_ISLNK(LSENT_MODE(e))
#define LSENT_ISSOCK(e)	  S_ISSOCK(LSENT_MODE(e))

#define LS_ISREG(l,i)	  S_ISREG(LS_MODE((l),(i)))
#define LS_ISDIR(l,i)	  S_ISDIR(LS_MODE((l),(i)))
#define LS_CHR(l,i)	  S_CHR(LS_MODE((l),(i)))
#define LS_ISBLK(l,i)	  S_ISBLK(LS_MODE((l),(i)))
#define LS_ISFIFO(l,i)	  S_ISFIFO(LS_MODE((l),(i)))
#define LS_ISLNK(l,i)	  S_ISLNK(LS_MODE((l),(i)))
#define LS_ISSOCK(l,i)	  S_ISSOCK(LS_MODE((l),(i)))

void ls_destroy(ls_t **list);
const char* ls_path(const ls_t* list,const lsent_t* ent);
ls_t* ls_create(const char* dir,void* data,
		int (*select)(const lsent_t*,void*),
		int (*compar)(const lsent_t**,const lsent_t**));
void ls_reorder(ls_t *list,int (*compar)(const lsent_t**,const lsent_t**));

int ls_match_RE(const lsent_t* ent,void* data);
int ls_match_not_RE(const lsent_t* ent,void* data);
int ls_sort_alpha(const lsent_t** a,const lsent_t** b);
int ls_sort_date(const lsent_t** a,const lsent_t** b);
int ls_sort_size(const lsent_t** a,const lsent_t** b);
