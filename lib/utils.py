#!/usr/bin/python3
# -*- coding=utf-8 -*-
import sys
from wrapper import log

# converts the string to reference
def parse(ref):
    strs = ref.split(":")
    if len(strs) != 2:
        log("ref {} error".format(ref))
        return "", ""
    return strs[0], strs[1]

# Docker style progress bar
def progress_bar(ublob, nb_traits):
    sys.stdout.write("\r" + ublob[7:19] + ": Downloading [")
    for i in range(0, nb_traits):
        if i == nb_traits - 1:
            sys.stdout.write(">")
        else:
            sys.stdout.write("=")
    for i in range(0, 49 - nb_traits):
        sys.stdout.write(" ")
    sys.stdout.write("]")
    sys.stdout.flush()