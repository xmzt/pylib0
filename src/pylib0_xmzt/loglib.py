import collections
import re
import traceback
import sys

#todo def noop(*args, **kwds): pass

#------------------------------------------------------------------------------------------------------------------------
# LogNoop

class LogNoop:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def __call__(self, *args): return self
    
logNoop = LogNoop()
    
#------------------------------------------------------------------------------------------------------------------------
# Logc collection of logging functions

LogcMethodRe = re.compile(r'__([^_]+)$', re.S)

def LogcMeta(name, bases, namespace, **kwds):
    funDset = {}
    funRootDset = {}
    nfunDset = {}
    for ns in [namespace] + [base.__dict__ for base in bases]:
        for k in ns:
            if (m := LogcMethodRe.search(k)):
                funDset[k] = None
                funRootDset[k[:m.start()]] = None
            else:
                nfunDset[k] = None
    for k in funRootDset:
        if (k0 := f'{k}__0') not in funDset:
            namespace[k0] = funDset[k0] = logNoop
        if k not in funDset:
            namespace[k] = namespace[k0]
    namespace['FunRootDset'] = funRootDset
    namespace['NfunDset'] = nfunDset
    return type(name, bases, namespace, **kwds)

class Logc:
    def kvSet(self, **kwds):
        for k,v in kwds.items():
            if k in self.NfunDset:
                setattr(self, k, v)
            elif k in self.FunRootDset:
                setattr(self, k, getattr(self, f'{k}__{v}'))
            else:
                for k0 in self.FunRootDset:
                    if k0.startswith(k):
                        setattr(self, k0, getattr(self, f'{k0}__{v}'))
        return self

    def logrFromPath(self, path):
        self.logr = Logr5File(open(path, 'w'))
        return self

    def logrSet(self, logr):
        self.logr = logr
        return self

#------------------------------------------------------------------------------------------------------------------------
# Logr5

class Logr5:
    LineRe = re.compile(r'^.*?$', re.M)

    def __init__(self, ind0):
        self.ind = self.ind0 = ind0

    def indDec(self):
        self.ind -= 4

    def indInc(self):
        self.ind += 4

    def indSet(self, ind):
        self.ind = self.ind0 + ind

    def birth(self): 
        return Logr5Child(self, self.ind)
        
    def __enter__(self):
        self.indInc()
        return self
        
    def __exit__(self, *args):
        self.indDec()
        
    def traceback(self, exc, value, tb):
        for line in traceback.format_exception(exc, value, tb):
            self(line.rstrip())
        return self

    def tracebackOob(self, exc, value, tb):
        for line in traceback.format_exception(exc, value, tb):
            self.oob(line.rstrip())
        return self

    def __call__(self, *args):
        self.out(self.ind, *args)
        return self

    def call(self, op, *args, **kwargs):
        self.out(self.ind, f'{op.__module__}.{op.__qualname__}'
                 f' {" ".join([f"{v!r}" for v in args])}'
                 f' {" ".join([f"{k}={v!r}" for k,v in kwargs.items()])}')
        op(*args, **kwargs)
        return self
    
    def ml(self, txt):
        for m in self.LineRe.finditer(txt):
            self.out(self.ind, m.group())
        return self
    
    def mlPos(self, txt):
        offW = len(str(len(txt)))
        for i,m in enumerate(self.LineRe.finditer(txt)):
            self.out(self.ind, f'{i:03d}[{m.start():0{offW}d}]: {m.group()}')
        return self
    
    def mlHex(self, txt):
        iE = len(txt)
        lineH = []
        lineC = []
        for i in range(0, len(txt)):
            if i & 0x3:
                pass
            elif i & 0xF:
                lineH.append(' ')
                lineC.append(' ')
            elif i:
                self.out(self.ind, ''.join(lineH))
                self.out(self.ind, ''.join(lineC))
                lineH = []
                lineC = []
            lineH.append(f'{txt[i]:02x}')
            lineC.append(f'{chr(txt[i])} ' if 0x20 <= txt[i] and txt[i] < 0x7F else '--')
        if lineH:
            self.out(self.ind, ''.join(lineH))
            self.out(self.ind, ''.join(lineC))
        return self
            
    def inMl(self, txt):
        self.indInc()
        try:
            return self.ml(txt)
        finally:
            self.indDec()
        
    def inMlPos(self, txt):
        self.indInc()
        try:
            return self.mlPos(txt)
        finally:
            self.indDec()

    def inMlHex(self, txt):
        self.indInc()
        try:
            return self.mlHex(txt)
        finally:
            self.indDec()

    def inLineV(self, lineV):
        self.indInc()
        try:
            for line in lineV:
                self(line)
            return self
        finally:
            self.indDec()
            
    def inLines(self, *lines):
        return self.inLineV(lines)
            
    def p0(self, pre, *args):
        return self.__call__(pre, *args) if 0 == self.ind else self.__call__(*args)

#------------------------------------------------------------------------------------------------------------------------
# Logr5Child

class Logr5Child(Logr5):
    def __init__(self, parent, ind0):
        self.parent = parent
        self.ind = self.ind0 = ind0

    def birth(self):
        return Logr5Child(self.parent, self.ind)

    def out(self, ind, *args):
        return self.parent.out(self.ind, *args)
    
    def oob(self, *args):
        self.parent.oob(*args)

    def pos(self):
        return self.parent.pos()
        
#------------------------------------------------------------------------------------------------------------------------
# Logr5File

class Logr5File(Logr5):
    def __init__(self, file0=sys.stdout, ind=0):
        super().__init__(ind)
        self.file0 = file0
        self.posI = 0

    def birthFile2(self, file1): 
        return Logr5File2(file1, self.file0, self.ind)

    def out(self, ind, *args):
        print(' '*ind, *args, sep='', file=self.file0)
        self.posI += 1

    def oob(self, *args):
        print(*args, sep='', file=self.file0)
        self.posI += 1

    def pos(self):
        return self.posI
        
class Logr5File2(Logr5):
    def __init__(self, file1=None, file0=sys.stdout, ind=0):
        super().__init__(ind)
        self.file0 = file0
        self.file1 = file1
        self.posI = 0

    def out(self, ind, *args):
        print(' '*ind, *args, sep='', file=self.file0)
        print(' '*ind, *args, sep='', file=self.file1)
        self.posI += 1

    def oob(self, *args):
        print(*args, sep='', file=self.file0)
        print(*args, sep='', file=self.file1)
        self.posI += 1

    def pos(self):
        return self.posI
