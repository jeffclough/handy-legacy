/******************************************************************************

Abstract: This is a program for the purpose of discovering from the default
name server the canonical name corresponding to a given IP adress. It will
also, and this is its strong point iterate through a range of IP addresses,
reporting the IP address and name of each machine in that range which is
known to the default name server.

TODO:
1. Add more precise subnet specification syntax. As on version 2.0, names
assumes that subnet masks of 8, 16, or 24 high-order bits are the only ones
of interest. This could be replaced with the syntax net/mask syntax (for
example, ). This would allow more versatile specification of subnets to be
scanned for known hosts.

HISTORY:

1.0, Unknown, Unknown
This code appears to have originated somewhere within operations. I've sent
Dewey email requesting more information on this so that I can make
appropriate attribution to the aboriginator.

2.0, 2003-10-03, Jeff Clough <jeff.clough@oit.gatech.edu>
The jump in version number is less due to changes in functionality and to 
my having virtually rewritten and restructured the code for the purposes of
readability and ease of future maintainance. The most significant things I
did were to resturcture the recursive printout() function, and to rewrite
the command line parsing logic to more easily allow for the addition of new
command line syntax. I also added a -v comman line option to display the
version of the names command.

******************************************************************************/

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>
#include <stdio.h>

char *version="Names v2.0";
char *progname=NULL;

/******************************************************************************
 * Send our usage message to stderr and return the value passed in to rc.
 */
int usage(int rc) {
  fprintf(stderr,
    "Usage: %s [-nv] ipaddr ...\n"
    "\n"
    "This program is used to discover from the default name server the cannonical\n"
    "name corresponding to a given IP address, or to a range of addresses if a\n"
    "partial IP address is given.\n"
    "\n"
    "  ipaddr  complete or partial IP address\n"
    "\n"
    "      -n  Adds IP addresses with no known hostname to list.\n"
    "      -v  Write the version of this program to standard output.,\n",
    progname);
  return rc;
} /* int usage(int rc) */

/******************************************************************************
 * printout() is called recursively until it as 4 valid octets of the IP
 * number. When it has 4 octets, it does the reverse lookup and prints the
 * resulting FQDN. It will loop through all valid values (0-255) for any
 * unspecified octets.
 */
int printout(char* ip,int numoct,int print_null_entries) {
  char stringtemp[16];
  int loop;

  if (numoct<4) {
    for(loop=0;loop<=255;loop++) {
      sprintf(stringtemp,"%s.%d",ip,loop);
      printout(stringtemp,numoct+1,print_null_entries);
    }
  }
  else {
#ifdef DEBUG
    printf("%-16s\n ",ip);
#else
    struct sockaddr_in sin;
    struct hostent *host;

    sin.sin_addr.s_addr=inet_addr(ip);
    host=gethostbyaddr((char*)&(sin.sin_addr),sizeof(sin.sin_addr),AF_INET);
    if (host!=NULL)
      printf("%-16s  \t%s\n", ip,host->h_name);
    else
      if (print_null_entries==1)
	printf("%-16s  \t\t<NO ENTRY>\n", ip);
#endif
  }
  return 0;
} /* int printout(char* ip,int numoct,int print_null_entries) */

/******************************************************************************
 * Main
 */
main(int argc,char** argv) {
  int i,print_null_entries=0;

  /*
   * Handle the command line.
   */
  progname=*argv;
  if (argc<2)
    return usage(1);
  for(i=1;i<argc;++i) {
    if (*argv[i]=='-') { /* This argument contains options. */
      int j;
      for(j=1;argv[i][j];++j)
	switch(argv[i][j]) {
	  case 'n':
	    print_null_entries=1;
	    break;
	  case 'v':
	    puts(version);
	    break;
	  default:
	    fprintf(stderr,"%s: Invalid option: -%c\n",argv[0],argv[i][j]);
	    return usage(1);
	}
    }
    else { /* This *should* be an IP or network specification. */
      int a,b,c,d,n;
      char ip[32];
      a=b=c=d=0;
      n=sscanf(argv[i],"%i.%i.%i.%i",&a,&b,&c,&d);
      if (a<0 || a>255 || b<0 || b>255 || c<0 || c>255 || d<0 || d>255) {
	fprintf(stderr,"%s: Invalid IP: %s\n\n",argv[i]);
	return usage(1);
      }
      switch(n) {
	case 0:
	  return usage(1);
	case 1:
	  sprintf(ip,"%d",a);
	  break;
	case 2:
	  sprintf(ip,"%d.%d",a,b);
	  break;
	case 3:
	  sprintf(ip,"%d.%d.%d",a,b,c);
	  break;
	case 4:
	  sprintf(ip,"%d.%d.%d.%d",a,b,c,d);
	  break;
      }
      printout(ip,n,print_null_entries);
    }
  }
  return 0;
}

