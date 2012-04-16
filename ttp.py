# -*- coding: utf-8
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

# Text to phoneme engine: reads language rule, applies filters,
# does text-to-phonemes and prosody.

import sys, re, os, stat

import config
#from profiling import *
reload(sys)
sys.setdefaultencoding("utf-8")

import setencoding	

def expand_char_class(str, class_list):
    if str is None:
        return ""
    while 1:
        again = 0
        for targ, subs in class_list :
            str, n = targ.subn(subs, str)
            again = again + n
        if not again: break
    return str


def read_rules(filename):
    phonems = {}
    rules = {}
    filters = []
    char_class = []
    pitch_def = {}

    f = file(filename, "r")
    filetime = os.fstat(f.fileno())[stat.ST_MTIME]

    # remove coments, extra blanks, end of line, etc.
    cleanup = re.compile( r"\s+#.*|(?<!\\)#.*|\s*\n" )

    # the CLASS keyword
    CLASS = re.compile( r"^CLASS\s+(\S)\s+(\S+)$" )

    # PROSO_SPEED keyword
    PROSO_SPEED = re.compile(r'PROSO_SPEED\s+(\S+)\s+(-?\d+),\s+(-?\d+)')

    # PROSO_PITCH keyword
    PROSO_PITCH = re.compile(r'PROSO_PITCH\s+(\S+)\s+\[(\d+)\]\s+\{\s*'
                             +r'("\s*(?:\d+\s+\d+)?(?:\s+\d+\s+\d+)*\s*"'
                             +r'(?:,\s*"\s*(?:\d+\s+\d+)?(?:\s+\d+\s+\d+)*\s*"'
                             r')*)\s*\}')

    # the PHO keyword
    PHO = re.compile( r"^PHO\s+(\S+)\s+([CPV])\s+(\d+)$" )

    # a filter rule
    filter = re.compile( r"^\s*(\S+)\s+\-\>\s+\"(.*)\"$" )

    # a phonetic rule
    rule = re.compile( r"^\s*((?P<lc>\S+)\s+)?"
                       r"\[\[ (?P<targ>\S+) \]\]\s+"
                       r"((?P<rc>\S+)\s+)?"
                       r"\-\>\s*(?P<pho>.*)$" )

    # Special char _ means space for convenience in filter and rule
    # patterns, unless preceeded with \.
    underline = re.compile(r'(?<!\\)_')
    def expand_space(str):
        return underline.sub(' ', str)

    # Our rule syntax allows (), but for efficiency we want the
    # non-grouping version of ().
    lparen = re.compile(r'(?<!\\)\((?!\?)')
    def expand_lparen(str):
        return lparen.sub('(?:', str)

    for ln,line in enumerate(f):
        line = line.decode('utf8')
        line = cleanup.sub("", line)
        if not line: continue
        try:
            m = rule.match(line)
            if m:
                lc, targ, rc, pho = m.group("lc", "targ", "rc", "pho")
                lc = expand_char_class(lc, char_class)
                lc = expand_space(lc)
                lc = expand_lparen(lc)
                targ = expand_space(targ)
                rc = expand_char_class(rc, char_class)
                rc = expand_space(rc)
                rc = expand_lparen(rc)
                left = re.compile(lc + "$")
                n = len(targ)
                right = re.compile(re.escape(targ)+rc)
                pho = pho.split()
                rules.setdefault(targ[0], []) \
                                          .append( (left, right, pho,n,
                                                    ln,line))
                continue

            m = PROSO_SPEED.match(line)
            if m:
                pho, s1, s2 = m.groups()
                s1,s2 = int(s1), int(s2)
                pitch_def[pho] = ((s1,s2),)
                continue

            m = PROSO_PITCH.match(line)
            if m:
                pho,i,pitches = m.groups()
                i = int(i)
                pitches = [s.replace('"', '').strip() \
                           for s in pitches.split(',')]
                pl = list(pitch_def[pho])
                if not len(pl) == i:
                    raise ValueError
                pl.append(tuple(pitches))
                pitch_def[pho] = tuple(pl)
                continue

            m = filter.match(line)
            if m:
                targ, subs = m.groups()
                targ = expand_char_class(targ, char_class)
                targ = expand_space(targ)
                targ = re.compile(targ)
                filters.append( (targ, subs) )
                continue

            m = PHO.match(line)
            if m:
                phonems[m.group(1)] = (m.group(2), int(m.group(3)))
                continue

            m = CLASS.match(line)
            if m:
                targ, subs = m.group(1,2)
                targ = re.compile(targ)
                char_class.append( (targ, subs) )
                continue
        except re.error, x:
            sys.stderr.write('%s (%d): regexp error: %s\n%s\n' \
                             % (filename, ln+1, str(x), line))
            sys.stderr.flush()
            sys.exit(1)
        except (ValueError, KeyError):
            pass
        sys.stderr.write('%s (%d): syntax error:\n%s\n' \
                         % (filename, ln+1, line))
        sys.stderr.flush()
        sys.exit(1)
    f.close()
    return rules, filters, phonems, pitch_def, filetime


def filter_text(text, filters, inxposes):
    text = text.lower()
    def repl(m, preSpaces):
        s,e = m.start(), m.end()
        n1 = m.group().count(' ')
        if callable(subs):
            r = subs(m)
        else:
            r = m.expand(subs)
        n2 = r.count(' ')
        assert len(inxposes) >= preSpaces+n1
        if n1:
            v = inxposes[preSpaces]
        elif preSpaces:
            v = inxposes[preSpaces-1]
        else:
            v = 0
        inxposes[preSpaces:preSpaces+n1] = [v]*n2
        return r, n2
    for targ, subs in filters:
        #text = re.sub(targ, repl, text)
        prestr = ''
        preSpaces = 0
        while text:
            m = re.search(targ, text)
            if not m:
                prestr += text
                break
            pre = text[:m.start()]
            prestr += pre
            preSpaces += pre.count(' ')
            r, nSpaces = repl(m, preSpaces)
            text = text[m.end():]
            prestr += r
            preSpaces += nSpaces
        text = prestr
        #print '%s -> %s' % (targ.pattern, subs)
        #print text
    assert len(inxposes) == text.count(' ') +1
    return text, inxposes


class PhonetizeError(Exception):
    pass

def phonetize(text, rules, showrules=0):
    done = ""
    res = []
    while text:
        try:
            for left, right, pho,n, ln, rule_line in rules[text[0]]:
                lm = left.search(done)
                if not lm: continue
                match = right.match(text)
                if not match: continue
                if showrules:
                    sys.stderr.write('%d: { %s } -- [ %s | %s | %s ]\n' \
                                   % (ln+1, rule_line,
                                      lm.group(), text[:n], match.group()[n:]))
                    if lm.group(): sys.stderr.write('%s<-' % lm.group())
                    sys.stderr.write('%s' % text[:n])
                    if match.group()[n:]: sys.stderr.write( '-<%s' % match.group()[n:])
                # keep last 20 chars of "done" context. 20 is arbitrary.
                done = (done + text[:n])[-20:]
                text = text[n:]
                res.extend(pho)
                #print (' = %s' % ''.join(pho))
                break
            else:
                # FIXME: provide necessary debugging info, and a config
                # option to die (so we notice) or continue (for
                # non-developers).
                raise PhonetizeError('No rule matched')
                done = done + text[0]
                text = text[1:]
        except KeyError:
            # FIXME: provide necessary debugging info
            sys.stderr.write('Char unmatched <%s> %d\n' % (text[0], ord(text[0])))
            done = done + text[0]
            text = text[1:]
    return res

rules, filters, phonems, pitch_def, filetime = read_rules(config.rulefile)

def checkReloadRules():
    try:
        newtime = os.stat(config.rulefile)[stat.ST_MTIME]
    except OSError:
        return
    global rules, filters, phonems, pitch_def, filetime
    if newtime >filetime:
        try:
            r,f,ph,pi,ft = read_rules(config.rulefile)
        except:
            filetime = newtime # don't retry until it changes again.
            return
        else:
            rules, filters, phonems, pitch_def, filetime = r,f,ph,pi,ft

spaces = re.compile(r'\s+')
def init_inxposes(str):
    # Original input length
    inputLen = len(str)
    # Note index position in original input where stretches of spaces end.
    inxposes = []
    def repl(m):
        inxposes.append(m.end())
        # keep a flag ("\t") to indicate the presence of multiple spaces
        return " \t"[:len(m.group())]
    str = spaces.sub(repl, str)
    # Last index is a bit special: marks end of text.
    inxposes.append(inputLen)
    return str, inxposes

def word2filtered(str):
    str, inxposes = init_inxposes(str)
    str, inxposes = filter_text(str, filters, inxposes)
    return str

def word2phons(str, showrules=0):
    checkReloadRules()
    str, inxposes = init_inxposes(str)
    str, inxposes = filter_text(str, filters, inxposes)
    phono = phonetize(str, rules, showrules)
    return ''.join(phono)
