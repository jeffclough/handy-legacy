#!/usr/bin/env python3

"""
This module is for decoding Smart Health Card (SHC) data, commonly used
for Covid-19 attestation.

See https://spec.smarthealth.cards for details.
https://www.ietf.org/rfc/rfc7517.txt is also helpful.

SHC data is cryptographically signed, but this module makes no attempt
to verify the signature.
"""

import base64,json,re,zlib

def decode(s):
  """Decode an SHC string, with or without the leading "shc:/" prefix,
  returning whatever comes out (typically JSON-formatted data)."""

  # Verify we've been handed a string value, and remove any "shc:/" prefix.
  if not isinstance(s,str):
    raise ValueError(f"shc.decode() requires a string argument (not {type(s)}).")
  if s[:5].lower()=='shc:/':
    s=s[5:]

  # Translate this from digit-pairs to character values.to base64 text,
  # yielding dot-separated string values, each of which must be base64-decoded.
  parts=(''.join([chr(int(s[i:i+2])+45) for i in range(0,len(s),2)])).split('.')
  parts=[p+'='*(4-len(p)%4) for p in parts] # To make these valid b64 values.
  parts=[base64.urlsafe_b64decode(p) for p in parts]

  # Get the configuration, data, and signature from this SHC data.
  conf,data,sig=parts
  conf=type('',(),json.loads(conf))

  # Interpret our "data" value according to what we find in conf.
  if conf.zip=='DEF':
    data=json.loads(zlib.decompress(parts[1],wbits=-15))
  else:
    raise ValueError(f"Unrecognized format in SHC data. Found {conf!r}.")

  return data
