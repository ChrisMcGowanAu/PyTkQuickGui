import sys
import logging as log

#########################################################
# This is a set of 'c' like interfaces that are more intuitive for me
#########################################################

def index(buf: str, search: str) -> int:
    # returns -1 if ch not found
    idx = buf.find(search)
    return idx


def printf(fmt: str, *args):
    sys.stdout.write(fmt % args)


def fprintf(fp, fmt: str, *args):
    fp.write(fmt % args)


def sprintf(buf,fmt, *args) -> str:
    tmpStr: str = buf
    tmpStr.format(fmt % args)
    # tmpStr.write(fmt % args)
    log.info("sprintf: ->%s<- fmt ->%s<-",tmpStr,fmt)
    return tmpStr


def fopen(fileName,mode):
    f: any
    # Possibly, if mode has a 'b' in it, then drop the encoding
    try:
        if mode.find("b") >= 0:
            f = open(fileName, mode, encoding="binary")
            # f = open(fileName, mode)
        else:
            f = open(fileName, mode, encoding="utf8")

    except FileNotFoundError as e:
        log.warning("File not found %s exception %s", fileName, str(e))
        f = open(fileName, "x", encoding="utf8")
    return f


def fclose(fp):
    fp.close()
