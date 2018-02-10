/*
THE MATERIALS AND INFORMATION CONTAINED HEREIN ARE UNPUBLISHED, CONFIDENTIAL,
PROPRIETARY, AND REGARDED BY GEORGIA TECH RESEARCH CORPORATION (GTRC) AS ITS
TRADE SECRET MATERIAL, AND ARE ONLY CONDITIONALLY ISSUED.  NEITHER RECEIPT NOR
POSSESSION THEREOF CONFERS OR TRANSFERS ANY RIGHT IN, OR LICENSE TO USE, THE
SUBJECT MATTER THEREOF, OR ANY DESIGN, TECHNIQUE, OR TECHNICAL INFORMATION
SHOWN THEREIN, NOR ANY RIGHT TO REPRODUCE THESE PROGRAMS, DOCUMENTATION, OR
ANY PART THEREOF EXCEPT IN ACCORDANCE WITH THE TERMS OF THE EXISTING LICENSE
AGREEMENT WITH GTRC.
*/

/*
	Written by Ray Spalding, Information Technology Internal Services,
	Georgia Institute of Technology, University System of Georgia.
*/

#include	<ctype.h>
#include	<sys/types.h>
#include	<sys/socket.h>
#include	<netinet/in.h>
#include	<netdb.h>
#include	<signal.h>
#include	<stdio.h>
#include	<stdlib.h>
#include	<string.h>
#include	<unistd.h>

#define	PH_HOST			"ph.gatech.edu"
#define	PH_SERVICE		"csnet-ns"
#define	PH_PROTO		"tcp"
#define	PH_PORT			105

#define	PHENV_HOST		"PHHOST"
#define	PHENV_PORT		"PHPORT"

#ifndef	SIGTYPE
#define	SIGTYPE	void
#endif	/* SIGTYPE */

#define	NAMELEN	40

typedef struct Field {
	struct Field* next;
	char* name;
	char* value;
} Field;

static int errflag;
static char* prog;
static char* fflag;
static char* hflag;
static char* pflag;
static int dashflag;
static int vflag;
static Field* ffield;
static Field* lfield;

static char* escchar[2] = {
	"abnrt\\",
	"\a\b\n\r\t\\"
};

static void
nomem()
{
	fprintf(stderr,"%s: Out of memory.\n",prog);
	exit(1);
}

static SIGTYPE
onsig(sig)
	int sig;
{
	fprintf(stderr,"%s: Signal %d.\n",prog,sig);
	exit(1);
}

static void
ph_usage()
{
	fprintf(stderr,"usage: %s [-v...] [-h host] [-p port] [-f format] [--] [command]\n",prog);
	exit(1);
}

static int
parg(buf,len,argc,argv)
	char* buf;
	int len;
	int argc;
	char** argv;
{
	char* cp;
	char* dp;
	int c;

	dp = buf;
	while (--argc > 0) {
		cp = *++argv;
		if (!dashflag && *cp == '-') {
			c = *++cp;
			switch (c) {
			case '-':		/* no more options */
				++dashflag;
				break;
			case 'v':		/* verbose level */
				do {
					++vflag;
					c = *++cp;
				} while (c == 'v');
				if (c) ph_usage();
				break;
			case 'h':		/* host */
				if (!*++cp) {
					if (--argc <= 0) ph_usage();
					cp = *++argv;
				}
				if (hflag) ph_usage();
				hflag = cp;
				break;
			case 'p':		/* port */
				if (!*++cp) {
					if (--argc <= 0) ph_usage();
					cp = *++argv;
				}
				if (pflag) ph_usage();
				pflag = cp;
				break;
			case 'f':		/* output format */
				if (!*++cp) {
					if (--argc <= 0) ph_usage();
					cp = *++argv;
				}
				if (fflag) ph_usage();
				fflag = cp;
				break;
			default:
				ph_usage();
			}
		} else {
			while (*cp && dp < buf + len - 2) {
				*dp++ = *cp++;
			}
			*dp++ = ' ';
		}
	}
	if (dp > buf) {
		dp[-1] = 0;
		return 1;
	}
	return 0;
}

static void
setfield(pp)
	char* pp;
{
	char name[NAMELEN];
	char* dp;
	Field* fp;

	while (isspace(*pp)) ++pp;
	dp = name;
	for (; *pp && *pp != ':'; ++pp) {
		if (dp < name + sizeof name - 1) *dp++ = *pp;
	}
	*dp = 0;
	if (*pp) ++pp;
	while (isspace(*pp)) ++pp;
	fp = (Field*)malloc(sizeof(Field));
	if (!fp) nomem();
	memset((char*)fp,0,sizeof(Field));
	fp->name = malloc(strlen(name) + 1);
	if (!fp->name) nomem();
	strcpy(fp->name,name);
	fp->value = malloc(strlen(pp) + 1);
	if (!fp->value) nomem();
	strcpy(fp->value,pp);
	if (!ffield) ffield = fp;
	if (lfield) lfield->next = fp;
	lfield = fp;
}

static void
freefieldlist()
{
	Field* fp;
	Field* np;

	for (fp = ffield; fp; fp = np) {
		np = fp->next;
		free(fp->name);
		free(fp->value);
		free((char*)fp);
	}
	ffield = 0;
}

static void
editformat()
{
	char* vp;
	char* dp;
	Field* fp;
	char name[NAMELEN];
	int c;
	int rc;

	rc = 0;
	for (vp = fflag; *vp; ) {
		switch (*vp) {
		case '%':
			dp = name;
			while ((c = *++vp) && (isalnum(c) || c == '_')) {
				if (dp < name + sizeof name - 1) *dp++ = c;
			}
			*dp = 0;
			for (fp = ffield; fp; fp = fp->next) {
				if (strcmp(fp->name,name) == 0) {
					dp = fp->value;
					while (*dp) {
						rc = putchar(*dp++);
						if (rc == EOF) break;
					}
				}
			}
			break;
		case '\\':
			c = *++vp;
			if (c == 0) {
				break;
			} else if (isdigit(c)) {
				c = strtol(vp,&vp,8);
				rc = putchar(c);
			} else if (c == 'x') {
				c = strtol(vp + 1,&vp,16);
				rc = putchar(c);
			} else {
				dp = strchr(escchar[0],c);
				if (dp) {
					rc = putchar(escchar[1][dp - escchar[0]]);
					++vp;
				} else {
					rc = putchar('\\');
				}
			}
			break;
		default:
			rc = putchar(*vp++);
			break;
		}
		if (rc == EOF) break;
	}
	if (rc == EOF) {
		perror("stdout");
		exit(1);
	}
	if (rc && rc != '\n') putchar('\n');
}

static void
displayformat()
{
	char* vp;

	if (!fflag) return;
	for (vp = fflag; *vp; ++vp) {
		fprintf(stderr,"  %c",isgraph(*vp) ? *vp : ' ');
	}
	fprintf(stderr,"\n");
	for (vp = fflag; *vp; ++vp) {
		fprintf(stderr," %02x",*vp);
	}
	fprintf(stderr,"\n");
}

int
main(argc,argv)
	int argc;
	char** argv;
{
	int sock;
	FILE* sockfp;
	struct sockaddr_in server;
	struct hostent* hp;
	struct servent* sp;
	char cmd[1024];
	char buf[1024];
	char* cp;
	char* pp;
	int rc;
	int ec;
	int datf;
	int entry;
	int cq;
	int len;
	unsigned short port;

	prog = *argv;
	if ((cp = strrchr(prog,'/'))) prog = cp + 1;
	errflag = 0;
	cq = parg(cmd,sizeof cmd - 3,argc,argv);
	if (vflag > 2) displayformat();
	signal(SIGPIPE,onsig);

	/* Determine host */
	if (!hflag) {
		hflag = getenv(PHENV_HOST);
		if (!hflag) hflag = PH_HOST;
	}

	/* Determine port */
	if (!pflag) {
		pflag = getenv(PHENV_PORT);
	}
	if (pflag) {
		port = strtol(pflag,&cp,10);
		if (*cp) ph_usage();
	} else {
		sp = getservbyname(PH_SERVICE,PH_PROTO);
		if (sp) {
			port = ntohs(sp->s_port);
		} else {
			port = PH_PORT;
		}
	}

	/* Create socket */
	sock = socket(AF_INET,SOCK_STREAM,0);
	if (sock < 0) {
		(void)sprintf(buf,"%s: Opening communication socket",prog);
		perror(buf);
		exit(1);
	}

	/* Connect socket using name */
	memset((char*)&server,0,sizeof server);
	server.sin_family = AF_INET;
	hp = gethostbyname(hflag);
	if (hp == 0) {
		fprintf(stderr,"%s: Host '%s' not found.\n",prog,hflag);
		exit(1);
	}
	memcpy((char*)&server.sin_addr,(char*)hp->h_addr,(unsigned)hp->h_length);
	server.sin_port = htons(port);
	if (vflag) {
		fprintf(stderr,"Connecting to '%s' port '%u'... ",hflag,port);
		fflush(stderr);
	}
	if (connect(sock,(struct sockaddr*)&server,sizeof server) < 0) {
		if (vflag) putc('\n',stderr);
		(void)sprintf(buf,"%s: connecting to '%s' port '%u'",prog,hflag,port);
		perror(buf);
		exit(1);
	}
	if (vflag) putc('\n',stderr);
	sockfp = fdopen(sock,"r+");
	if (!sockfp) {
		(void)sprintf(buf,"%s: fdopen",prog);
		perror(buf);
		exit(1);
	}
	for (;;) {
		if (!cq) {
			printf("> ");
			fflush(stdout);
			if (!fgets(cmd,sizeof cmd - 3,stdin)) break;
			if ((cp = strchr(cmd,'\n'))) *cp = 0;
		}
		len = strlen(cmd);
		strcpy(cmd + len,"\r\n");
		write(sock,cmd,len + 2);
		entry = 0;
		for (;;) {
			if (!fgets(buf,sizeof buf,sockfp)) break;
			rc = atoi(buf);
			if ((cp = strchr(buf,'\r'))) *cp = 0;
			if ((cp = strchr(buf,'\n'))) *cp = 0;
			if (vflag > 1) fprintf(stderr,"%s\n",buf);
			datf = (rc == -200) ? 1 : 0;
			if (rc >= 500 || rc <= -500) ++errflag;
			pp = buf;
			ec = 0;
			if ((cp = strchr(pp,':'))) {
				pp = cp + 1;
				if (datf) {
					ec = atoi(pp);
					if ((cp = strchr(pp,':'))) pp = cp + 1;
				}
			}
			if (ec != entry) {
				if (fflag) {
					if (entry) {
						editformat();
						freefieldlist();
					}
				} else { 
					printf("-----------------------------\n");
				}
				entry = ec;

			}
			if (fflag) {
				if (datf) setfield(pp);
			} else {
				if (vflag || rc != 200) printf("%s\n",pp);
			}
			if (rc >= 0) break;
		}
		if (cq) break;
		if (strncmp(buf,"200:Bye",7) == 0) break;
	}
	close(sock);
	if (errflag) {
		exit(1);
	}
	exit(0);
}
