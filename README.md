# Warning!
This code is currently in a transitional state between Python 2 and Python 3, _AND_ the installer's broken (and being rewritten). I'm porting it all to 3 as I have time. YOU HAVE BEEN WARNED!

# handy
These are home-grown commands and Python modules that make me more efficient (or at least happier).

Externals:
To update external projects, run "git submodule update --init --recursive".

Installation:

THE INSTALL SCRIPT IS STILL BROKEN. YOU HAVE TO INSTALL MANUALLY.

Run "./install" to install these the way I do or "./install -h" for other options.

SO DO IT THIS WAY ...

```shell
cd
mkdir my my/{bin,etc,include,lib} my/lib/python
```

That's how I organize my home directory's structure for "local" commands. You likely have your own system.

`cd ~/src/handy` ... or wherever you keep the handy code.

Here's where everything gets installed:

```shell
cd ~/src/handy
cp -p ad-userAccountControl alex ansi args ascii backup-volume base beyondpod certmon chronorename columnate csv cutcsv dump factors freq ind ip2host json json2csv keeplast ldif mark mazer mix names not now patch-cal pg ph pretty-json prime progress pwgen pygrep qr re reduce slice strftime strptime timeout title-case tread ts ~/my/bin
cd pylib
cp -p CSV.py OptionParserFormatters.py RE.py abbrev.py ansi.py conf.py daemon.py date_parser.py debug.py dirwalker.py english.py exiftool.py grep.py handy.py install.py loggy.py make.py parsing.py phonetics.py png.py prime.py semver.py stardate.py table.py tree.py versioning.py ~/my/lib/python
```

Add to PATH and PYTHONPATH as needed.

```shell
export PATH=~/my/bin;$PATH
export PYTHONPATH=~/my/lib/python;$PYTHONPATH
```
