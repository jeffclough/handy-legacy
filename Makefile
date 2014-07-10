#
# Use this make file for compiling any or all of the programs listed below.
# Note that "make install" will build the executables if necessary.
#

PROGS=datecycle dump freq mix numlines ph portname randword secdel \
	timeshift
      
SCRIPTS=chronorename columnate cutcsv decode64 encode64 factors gensig/gensig \
	ip2host mark names pa pygrep strftime ts

DATA=gensig/quotes gensig/*.sig

PYTHON_PKGS=xlrd

CC=cc
GCC=gcc
SYSTYPE=$(shell uname)
ifeq "$(SYSTYPE)" "Linux"
  NETLIBS=
  #STATIC=-static -static-libgcc
  STATIC=
else
  ifeq "$(SYSTYPE)" "SunOS"
    GCC=$(CC)
    NETLIBS=-lsocket -lnsl
    STATIC=
  else
    NETLIBS=
    STATIC=
  endif
endif

#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

all: $(PROGS)

python_pkgs:
	@for p in $(PYTHON_PKGS); do \
	echo $$p; \
	test -d pkgs/$$p || \
	easy_install --build-directory pkgs --editable $$p; \
	cd pkgs/$$p && \
	python setup.py build && \
	rsync -uav build/lib/$$p $(HOME)/my/lib/python && \
	cd ../..; \
	done

install: $(PROGS) python_pkgs
	@for p in $(PROGS); do echo cp -p $$p $(HOME)/my/bin; cp -p $$p $(HOME)/my/bin; done
	@for p in $(SCRIPTS); do echo cp -p $$p $(HOME)/my/bin; cp -p $$p $(HOME)/my/bin; done
	@for p in $(DATA); do echo cp -p $$p $(HOME)/my/etc; cp -p $$p $(HOME)/my/etc; done
	@for p in pylib/*; do echo cp -p $$p $(HOME)/my/lib/python; cp -p $$p $(HOME)/my/lib/python; done

clean:
	rm -f $(PROGS)
	rm -f *.o
	
#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#

datecycle: datecycle.c ls_class.o
	$(CC) datecycle.c ls_class.o -o datecycle && \
	touch -r datecycle.c datecycle

dump: dump.c
	$(CC) dump.c -lm -o dump && \
	touch -r dump.c dump

freq: freq.c
	$(CC) freq.c -lm -o freq && \
	touch -r freq.c freq

ls_class.o: ls_class.c ls_class.h
	$(CC) -c ls_class.c && \
	touch -r ls_class.c ls_class.o

ls_class_test: ls_class.c ls_class.h
	$(CC) -g -DTEST -o ls_class_test ls_class.c && \
	touch -r ls_classtest.c ls_class_test

mix: mix.c
	$(CC) mix.c -o mix && \
	touch -r mix.c mix

#names: names.c
#	$(CC) names.c -lsocket -lnsl -o names
#	touch -r names.c names

numlines: numlines.c
	$(CC) numlines.c -o numlines && \
	touch -r numlines.c numlines

ph: ph.c
	$(CC) ph.c $(NETLIBS) -o ph && \
	touch -r ph.c ph

portname: portname.c
	$(CC) portname.c $(NETLIBS) -o portname && \
	touch -r portname.c portname

randword: randword.c
	$(CC) randword.c -o randword && \
	touch -r randword.c randword

secdel: secdel.c
	$(GCC) secdel.c -o secdel $(STATIC) && \
	touch -r secdel.c secdel

timeshift: timeshift.c
	$(CC) timeshift.c -o timeshift && \
	touch -r timeshift.c timeshift
