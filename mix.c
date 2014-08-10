/******************************************************************************
 * Reading from standard input and writing to standard output, scramble the
 * interior of each word found along the way.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main(void) {
  char *cp,buf[16384]; /* These hold and manage a line of text. */
  int i,j; /* These point to the start and end+1 of a word. */
  int len,l,m,n; /* These help us to scramble a word's interior. */

  /*
   * Seed C's standard pseudo-random number generator with the current time.
   */
  srand(time(NULL));

  /*
   * Iterate through each line of standard input.
   */
  while(fgets(buf,sizeof(buf),stdin)) {
    if ((cp=strchr(buf,'\n'))!=NULL)
      *cp='\0';
    /*
     * Scramble the interior of each word in this line, but be careful to
     * maintain formatting.
     */
    for(i=0;buf[i];i=j) {
      char ch;
      /* Find the beginning of the next word. */
      while((ch=buf[i])!='\0' && (ch<'a' || ch>'z') && (ch<'A' || ch>'Z'))
	++i;
      /* Find the end of this word. */
      for(j=i;((ch=buf[j])>='a' && ch<='z') || (ch>='A' && ch<='Z');++j);
      /* If this word is at least 4 characters in length, scramble it. */
      if ((len=n=j-i-2)>=2)
	while(--n) {
	  l=(rand()%len)+i+1;
	  m=(rand()%len)+i+1;
	  ch=buf[l];
	  buf[l]=buf[m];
	  buf[m]=ch;
	}
    }
    puts(buf);
  }
} /* int main(void) */
