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

dump: dump.c
	cc dump.c -lm -o dump

freq: freq.c
	cc freq.c -lm -o freq

ls_class.o: ls_class.c ls_class.h
	cc -c ls_class.c

ls_class_test: ls_class.c ls_class.h
	cc -g -DTEST -o ls_class_test ls_class.c

mix: mix.c

#names: names.c
#	cc names.c -lsocket -lnsl -o names

numlines: numlines.c

portname: portname.c

randword: randword.c

secdel: secdel.c
	gcc secdel.c -o secdel $(STATIC)

timeshift: timeshift.c
