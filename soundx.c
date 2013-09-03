#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PH_TONGUE   1
#define PH_LIP      2
#define PH_GLOTTAL  4
#define PH_VIOCE    8

static char phoneme[256];

/*
 * Initialize our string->phoneme map data.
 */
static void init() {
 phoneme['b']='b';
 phoneme['c']='b';
 phoneme['d']='b';
 phoneme['f']='b';
 phoneme['g']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
 phoneme['b']='b';
} /* static void init() */

/******************************************************************************

  NAME
  soundx_value - Compute the SoundX value of the given string.

  SYNOPSIS
  int soundx_value(char* s,char* val,int valsize);

  DESCRIPTION
  This function creates an array of phonetic indices from string s and puts
  them into array val, which contains valsize characters.

******************************************************************************/
int soundx_value(char* s,char* val,int valsize) {
} /* int soundx_value(char* s,char* val,int valsize) */
