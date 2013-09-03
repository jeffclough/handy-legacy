#include <stdio.h>
#include <string.h>
#include <netdb.h>

char *progname=NULL;

void findservice(int port) {
  struct servent *sep;
  char **cpp;
  int hbo,found=0;
  setservent(1);
  while((sep=getservent())!=NULL) {
    hbo=ntohs(sep->s_port);
    if (hbo==port) {
      printf("%d/%s\t%s",hbo,sep->s_proto,sep->s_name);
      for(cpp=sep->s_aliases;*cpp;++cpp)
	printf(" %s",*cpp);
      putchar('\n');
      found=1;
    }
  }
  endservent();
  if (!found)
    fprintf(stderr,"%s: port %d has no name on this system.\n",progname,port);
} /* void findservice(int port) */

int main(int argc,char **argv) {
  progname=*argv;
  while(*++argv) {
    int port;
    if (sscanf(*argv,"%i",&port)!=1) {
      fprintf(stderr,"%s: %s is not a valid port number.\n",progname,*argv);
      return 1;
    }
    findservice(port);
  }
} /* int main(int argc,char **argv) */
