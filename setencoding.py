# -*- coding: utf8
# This file is part of Cicero TTS.
#   Cicero TTS: A Small, Fast and Free Text-To-Speech Engine.
#   Copyright (C) 2003-2008 Nicolas Pitre  <nico@cam.org>
#   Copyright (C) 2003-2008 Stéphane Doyon <s.doyon@videotron.ca>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2.
#   See the accompanying COPYING file for more details.
#
#   This program comes with ABSOLUTELY NO WARRANTY.
#
# Pseudo-automated charset conversion for std{in,out,err} and program
# args, so we can work with unicode internally.

import codecs, locale, sys

# Inspired from http://kofoto.rosdahl.net/trac/wiki/UnicodeInPython

def get_file_encoding(f):
    if hasattr(f, "encoding") and f.encoding:
        e = f.encoding
    else:
        e = locale.getpreferredencoding()
    if e == 'ANSI_X3.4-1968': # fancy name for ascii
        # We're sure to have accents and ascii is sure not to work, let's
        # just guess UTF-8. (An alternative might be to use the 'replace'
        # error handler...)
        e = 'UTF-8'
    return e

# Wrap std{in,out,err} with versions that auto decode/encode.
# 0 means guess charset, None means don't install a wrapper.
# Some caveats: make the file unbuffered / nonblocking BEFORE. And the
# wrapper won't do some stuff like isatty() for instance...
def stdfilesEncoding(sin=0, sout=0, serr=0):
    if sin is 0:
        sin = get_file_encoding(sys.stdin)
    if sin is not None:
        sys.stdin = codecs.getreader(sin)(sys.stdin)
    if sout is 0:
        sout = get_file_encoding(sys.stdout)
    if sout is not None:
        sys.stdout = codecs.getwriter(sout)(sys.stdout)
    if serr is 0:
        serr = get_file_encoding(sys.stderr)
    if serr is not None:
        sys.stderr = codecs.getwriter(serr)(sys.stderr)

# Decode program arguments
def decodeArgs():
    sys.argv = [a.decode(sys.getfilesystemencoding()) for a in sys.argv]
