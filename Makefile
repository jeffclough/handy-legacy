#
# Use this make file for compiling any or all of the programs listed below.
# Note that "make install" will build the executables if necessary.
#

PROGS=datecycle dump freq mix numlines portname randword secdel \
      timeshift
      
SCRIPTS=gensig/gensig mark names

DATA=gensig/quotes gensig/*.sig


SYSTYPE=`uname`
ifeq ("$(SYSTYPE)","Linux")
STATIC=-static -static-libgcc
else
STATIC=
endif

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

all: $(PROGS)

install: $(PROGS)
	@for p in $(PROGS); do echo mv $$p ~/my/bin; mv $$p ~/my/bin; done
	@for p in $(SCRIPTS); do echo cp -p $$p ~/my/bin; cp -p $$p ~/my/bin; done
	@for p in $(DATA); do echo cp -p $$p ~/my/etc; cp -p $$p ~/my/etc; done

clean:
	rm -f $(PROGS)
	rm -f ls_class.o
	
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

datecycle: datecycle.c ls_class.o
	cc datecycle.c ls_class.o -o datecycle
	touch -r datecycle.c datecycle

dump: dump.c
	cc dump.c -lm -o dump
	touch -r dump.c dump

freq: freq.c
	cc freq.c -lm -o freq
	touch -r freq.c freq

ls_class.o: ls_class.c ls_class.h
	cc -c ls_class.c
	touch -r ls_class.c ls_class.o

ls_class_test: ls_class.c ls_class.h
	cc -g -DTEST -o ls_class_test ls_class.c
	touch -r ls_classtest.c ls_class_test

mix: mix.c
	cc mix.c -o mix
	touch -r mix.c mix

#names: names.c
#	cc names.c -lsocket -lnsl -o names
#	touch -r names.c names

numlines: numlines.c
	cc numlines.c -o numlines
	touch -r numlines.c numlines

portname: portname.c
	cc portname.c -o portname
	touch -r portname.c portname

randword: randword.c
	cc randword.c -o randword
	touch -r randword.c randword

secdel: secdel.c
	gcc secdel.c -o secdel $(STATIC)
	touch -r secdel.c secdel

timeshift: timeshift.c
	cc timeshift.c -o timeshift
	touch -r timeshift.c timeshift
