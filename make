#!/usr/bin/env python
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Generic Boiler-plate code for using the make module.

# Prefer the python modules in our pylib directory.
import sys
sys.path.insert(1,'pylib')

# Import make (which will handle the command line).
import make

# Provide a default installation prefix directory.
if make.opt.prefix==None:
  make.opt.prefix='~/my'
make.opt.prefix=make.expand_all(make.opt.prefix)

# End of Boiler-plate code.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

make.COPTS=[]
if make.OS_NAME=='Darwin':
  # Suppress complaints about missing braces in if...else statements.
  make.COPTS.append('-Wno-dangling-else')

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
  'csv',
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
  'pwgen',
  'pygrep',
  'slice',
  'strftime',
  'ts',
)

DATA=( # Copy these data files to make.opt.prefix/etc.
  'gensig/quotes',
  'gensig/*.sig',
)

# Both home-grown and modules and PyPi packages are installed here.
PYTHON_LIB_DIR=make.expand_all('$HOME/my/lib/python')

# Define some targets of different types and their dependencies.
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
make.EasyInstall('xlrd',PYTHON_LIB_DIR,minver='2.6')

# We need one installer for each target directory.
make.Installer('install',make.path(make.opt.prefix,'bin'),CPROGS,SCRIPTS)
make.Installer('install',make.path(make.opt.prefix,'etc'),DATA)
make.Installer(
  'install',
  make.path(make.opt.prefix,'lib','python'),
  make.path('pylib','*'),
)

for target in make.args:
  if target=='clean':
    make.clean()
  else:
    make.make(target)

