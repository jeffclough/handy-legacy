# ts (Time Stamp)

```
Usage: ts [OPTIONS] filename ...

This command renames the given file(s) to include the date and time of each
respective file. It renames filename to filename.YYYYMMDD_HHMMSS. If -c
(--copy) is given, the file is copied rather than renamed. If no argument is
given, the current (or offset) time is simply written to standard output.

Options:
  -h, --help            show this help message and exit
  --age                 Report the age of the file in seconds. No copying or
                        renaming is performed.
  -t TIME, --time=TIME  Choose which time to use for the timestamp. The
                        choices are 'created', 'accessed', or 'modified'.
                        (default: modified)
  --format=FORMAT       Specify a new format for a time-stamped filename.
                        (default: %(filename)s.%(time)s)
  --time-format=TIME_FORMAT
                        Specify the format for expressing a file's timestamp.
                        (default: %Y%m%d_%H%M%S)
  -n, --dry-run         Don't actually rename any files. Only output the new
                        name of each file as it would be renamed.
  --offset=OFFSET       Formatted as '[+|-]H:M' or '[+|-]S', where H is hours,
                        M is minutes, and S is seconds, apply the given offset
                        to the time.
  -c, --copy            Copy the file rather than renaming it.
  -s, --show-me         Only output the timestamped filename of the given
                        file(s). No file is actually renamed or copied. The
                        current time is used for any file that does not exist.
  -q, --quiet           Perform all renaming or copying silently. This option
                        does not silence the --age or the -s (--show-me)
                        option.
  --utc                 Express all times as UTC (no time zone at all).
```


