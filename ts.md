# ts (Time Stamp)

```
Usage: ts [OPTIONS] filename ...

This command renames or coppies, and optionally compresses, the given
file(s) to include the date and time of each respective file. This is
very handy for rotating log files or saving a copy of a script before
modifying it. File permissions and times are preserved, even when
copying and/or compressing.

Options:
  -h, --help            show this help message and exit
  --age=UNITS           Report the age of the file in the given UNITS.
                        No copying or renaming is performed. If no
                        filename is given on the command line, simply
                        output the current (or offset) time in the
                        given UNITS to standard output. UNITS is one
                        of 'seconds', 'minutes', 'hours', 'days', or
                        'weeks' (or s, m, h, d, or w, or anywhere in
                        between).
  -c, --copy            Copy the file rather than rename it.
  --filename            Only output the timestamped filename of the
                        given file(s). No file is actually renamed or
                        copied. The current time is used for any file
                        that does not exist.
  --format=FORMAT       Specify a new format for a time-stamped
                        filename. (default: %(filename)s.%(time)s)
  -n, --dry-run         Don't actually rename any files. Only output
                        the new name of each file as it would be
                        renamed.
  --offset=OFFSET       Formatted as '[+|-]H:M' or '[+|-]S', where H
                        is hours, M is minutes, and S is seconds,
                        apply the given offset to the time.
  -q, --quiet           Perform all renaming or copying silently. This
                        option does not silence the --age or the
                        --filename options.
  -t TIME, --time=TIME  Choose which time to use for the timestamp.
                        The choices are 'created', 'accessed', or
                        'modified'. (default: modified)
  --time-format=TIME_FORMAT
                        Specify the format for expressing a file's
                        timestamp. (default: %Y%m%d_%H%M%S)
  --utc                 Express all times as UTC (no time zone at
                        all).
  -z                    The file is compressed with gzip after
                        renaming or copying.
```
