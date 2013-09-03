#include <stdio.h>

int main(void) {
  char s[32767];
  unsigned long n=0;
  while(fgets(s,sizeof(s),stdin)) {
    printf("%4ld %s",++n,s);
    fflush(stdin);
  }
  return 0;
} /* int main(void) */
