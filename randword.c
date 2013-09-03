#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

char *USAGE="usage: randword <min> <max> [<maxwords>]\n"
            "where <min> is the minimum number of sylables you want\n"
            "and <max> is the maximum number of sylables you want in\n"
            "the names that will be randomly generated. If <maxwords>\n"
            "is given, that many words will be generated. By default,\n"
            "100 words will be generated.\n\n";

#define MAXSYL 100 /* maximum number of sylables allowed */

#define random(n) (rand()%(n))

int sconcount;
char *scon[]={"b","c","d","f","g","h","j","k","l","m",
              "n","p","q","r","s","t","v","x","z"};

int concount;
char *con[]={"b",  /* This is an array of possible consonants and */
             "bb", /* consonant pairs.                            */
             "bh",
             "bj",
             "bl",
             "br",
             "bw",
             "c",
             "cc",
             "ch",
             "cj",
             "ck",
             "cl",
             "cr",
             "ct",
             "cw",
             "d",
             "dd",
             "dh",
             "dj",
             "dl",
             "dr",
             "dw",
             "f",
             "fc",
             "ff",
             "fh",
             "fj",
             "fl",
             "fr",
             "fw",
             "g",
             "gg",
             "gh",
             "gj",
             "gl",
             "gr",
             "gw",
             "h",
             "hg",
             "hh",
             "hj",
             "hl",
             "hr",
             "hw",
             "j",
             "jh",
             "jj",
             "jl",
             "jr",
             "jw",
             "k",
             "kh",
             "kj",
             "kk",
             "kl",
             "kr",
             "kw",
             "l",
             "lh",
             "ll",
             "m",
             "mh",
             "ml",
             "mm",
             "mn",
             "mr",
             "ms",
             "mt",
             "mw",
             "n",
             "nh",
             "nl",
             "nn",
             "nr",
             "ns",
             "nt",
             "nw",
             "p",
             "ph",
             "pl",
             "pp",
             "pr",
             "pw",
             "q",
             "qu",
             "r",
             "rh",
             "rr",
             "s",
             "sc",
             "sd",
             "sf",
             "sg",
             "sh",
             "sj",
             "sk",
             "sl",
             "sm",
             "sn",
             "sp",
             "sq",
             "squ",
             "sr",
             "ss",
             "st",
             "sv",
             "sw",
             "t",
             "tl",
             "tr",
             "tw",
             "v",
             "vl",
             "vr",
             "vw",
             "w",
             "wh",
             "wr",
             "ww",
             "x",
             "xh",
             "xw",
             "xx",
             "z",
             "zh",
             "zl",
             "zm",
             "zn",
             "zr",
             "zw",
             "zz",
             ""}; /* a null string must terminate this array */

int vowcount;
char *vow[]={"a",  /* This is an array of vowels and vowel combinations. */
             "aa",
             "ae",
             "ai",
             "ao",
             "au",
             "ay",
             "e",
             "ea",
             "ee",
             "ei",
             "eo",
             "eu",
             "ey",
             "i",
             "ia",
             "ie",
             "io",
             "iu",
             "iy",
             "o",
             "oa",
             "oe",
             "oi",
             "ou",
             "oy",
             "u",
             "ua",
             "ue",
             "ui",
             "uo",
             "uu",
             "uy",
             "y",
             "ya",
             "ye",
             "yi",
             "yo",
             "yu",
             "yy",
             ""}; /* a null string must terminate this array */

char *randsylable(void);
char *randword(int min,int max);

int main(int argc,char **argv) {
  int min,max;   /* Range of sylibles. */
  long maxwords; /* Number of words to generate. */
  /*
    Read and validate the command line.
  */
  if (argc<3) {
    printf("%s",USAGE);
    return 1;
   }
  argv++;
  min=atoi(*argv++);
  max=atoi(*argv++);
  if (min<1 || max<1 || min>max || max>100) {
    printf("Don't use rediculous values for <min> and <max>\n\n");
    puts(USAGE);
    return 1;
   }
  if (*argv)
    maxwords=atol(*argv);
  else
    maxwords=100;
  if (maxwords<0) {
    printf("Don't use rediculous values for <maxwords>\n\n");
    puts(USAGE);
    return 1;
   }
  /*
    Ramdomize the random number generator.
  */
  srand(time(0));
  /*
    Determine the sizes of the scon, con, and vow arrays.
  */
  sconcount=sizeof(scon)/sizeof(*scon);
  concount=sizeof(con)/sizeof(*con);
  vowcount=sizeof(vow)/sizeof(*vow);
  /*
    Generate random words.
  */
  while(maxwords--) 
    puts(randword(min,max));
  return 0;
} /* end of int main(argc,argv) */

char *randword(int min,int max) {
 static char word[1024];
 int i,n;
 n=random(max-min+1)+min;
 strcpy(word,scon[random(sconcount)]);
 while(n--) {
   strcat(word,vow[random(vowcount)]);
   if (n)
     strcat(word,con[random(concount)]);
   else
     strcat(word,scon[random(sconcount)]);
 }
 return word;
} /* end of char *randword(min,max) */

