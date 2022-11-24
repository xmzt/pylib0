import re
import traceback
import sys

def noop(*args, **kwds): pass

#------------------------------------------------------------------------------------------------------------------------
# Logc collection of logging functions

class Logc:
    def argrKv(self, k, v):
        v0 = getattr(self, k)
        if not int(v):
            setattr(self, k, noop)
        elif v0 is noop:
            delattr(self, k)

#------------------------------------------------------------------------------------------------------------------------
# Logr5

class Logr5:
    LineRe = re.compile(r'^.*?$', re.M)

    def __init__(self, ind):
        self.ind = ind

    def birth(self, pre, show):
        return Logr5Child(self, pre, show)
        
    def __enter__(self):
        self.ind += 4
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ind -= 4
        
    def traceback(self, exc, value, tb):
        for line in traceback.format_exception(exc, value, tb):
            self(line.rstrip())
        return self

    def tracebackOob(self, exc, value, tb):
        for line in traceback.format_exception(exc, value, tb):
            self.oob(line.rstrip())
        return self

    def __call__(self, *args):
        self.out(*args)
        return self

    def call(self, op, *args, **kwargs):
        self.out(f'{op.__module__}.{op.__qualname__}'
                 f' {" ".join([f"{v!r}" for v in args])}'
                 f' {" ".join([f"{k}={v!r}" for k,v in kwargs.items()])}')
        op(*args, **kwargs)
        return self
    
    def ml(self, txt):
        offW = len(str(len(txt)))
        for i,m in enumerate(self.LineRe.finditer(txt)):
            self.out(f'{i:03d}[{m.start():0{offW}d}]: {m.group()}')
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
                self.out(''.join(lineH))
                self.out(''.join(lineC))
                lineH = []
                lineC = []
            lineH.append(f'{txt[i]:02x}')
            lineC.append(f'{chr(txt[i])} ' if 0x20 <= txt[i] and txt[i] < 0x7F else '--')
        if lineH:
            self.out(''.join(lineH))
            self.out(''.join(lineC))
        return self
            
    def inMl(self, txt):
        self.ind += 4
        try:
            return self.ml(txt)
        finally:
            self.ind -= 4
        
    def inMlHex(self, txt):
        self.ind += 4
        try:
            return self.mlHex(txt)
        finally:
            self.ind -= 4

    def inLines(self, *lines):
        self.ind += 4
        try:
            for line in lines:
                self(line)
            return self
        finally:
            self.ind -= 4

    def p0(self, pre, *args):
        return self.__call__(pre, *args) if 0 == self.ind else self.__call__(*args)

class Logr5Child(Logr5):
    def __init__(self, parent, pre, show):
        self.parent = parent
        self.pre = pre
        self.show = show

    def birth(self, pre, show):
        return Logr5Child(self.parent, pre, show)

    def __enter__(self):
        self.parent.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.parent.__exit__(exc_type, exc_val, exc_tb)

    def out(self, *args):
        if self.show:
            self.parent.out(self.pre, *args)

    def oob(self, *args):
        self.parent.oob(*args)

class Logr5File(Logr5):
    def __init__(self, file0=sys.stdout, ind=0):
        super().__init__(ind)
        self.file0 = file0

    def out(self, *args):
        print(' '*self.ind, *args, sep='', file=self.file0)

    def oob(self, *args):
        print(*args, sep='', file=self.file0)

class Logr5File2(Logr5):
    def __init__(self, file1=None, file0=sys.stdout, ind=0):
        super().__init__(ind)
        self.file0 = file0
        self.file1 = file1

    def out(self, *args):
        print(' '*self.ind, *args, sep='', file=self.file0)
        print(' '*self.ind, *args, sep='', file=self.file1)

    def oob(self, *args):
        print(*args, sep='', file=self.file0)
        print(*args, sep='', file=self.file1)
