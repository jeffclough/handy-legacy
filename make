#!/usr/bin/env python
import make

make.COPTS=(
  # Suppress complaints about missing braces in if...else statements.
  '-Wno-dangling-else',
  # Crank up the verbosity to show linker invocation.
  #'-v',
)

CPROGS=( # Compile these targets from C source files.
  'datecycle',
  'dump',
  'freq',
  'mix',
  'numlines',
  'ph',
  'portname',
  'randword',
  'secdel',
  'timeshift',
)

SCRIPTS=( # These targets are simply copied during installation.
  'chronorename',
  'columnate',
  'cutcsv',
  'decode64',
  'encode64',
  'factors',
  'gensig/gensig',
  'ip2host',
  'mark',
  'names',
  'now',
  'pa',
  'pygrep',
  'strftime',
  'ts',
)

DATA=( # Copy these data files to opt.prefix/etc.
  'gensig/quotes',
  'gensig/*.sig',
)

PYTHON_LIB_DIR=make.expand_all('~/my/lib/python')

# DEBUGGING:
prefix=make.expand_all('~/tmp/inst')

make.CExecutable('datecycle','datecycle.c',objs='ls_class.o')
make.CExecutable('dump','dump.c',opts='-lm')
make.CObjectFile('ls_class.o','ls_class.c','ls_class.h')
make.CObjectFile('ls_class_test','ls_class.c','ls_class.h',opts='-DTEST')
make.CExecutable('freq','freq.c',opts='-lm')
make.CExecutable('mix','mix.c')
make.CExecutable('numlines','numlines.c')
make.CExecutable('ph','ph.c')
make.CExecutable('portname','portname.c')
make.CExecutable('randword','randword.c')
make.CExecutable('secdel','secdel.c')
make.CExecutable('timeshift','timeshift.c')
make.DependentTarget('cutcsv','xlrd')
make.EasyInstall('xlrd',PYTHON_LIB_DIR)

# We need one installer for each target directory.
make.Installer('install',make.path(prefix,'bin'),CPROGS,SCRIPTS)
make.Installer('install',make.path(prefix,'etc'),DATA)
make.Installer(
  'install',
  make.path(prefix,'lib','python'),
  make.path('pylib','*'),
)

for target in make.args:
  if target=='clean':
    make.clean()
  else:
    make.make(target)

