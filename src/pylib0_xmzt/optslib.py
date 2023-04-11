import inspect
import os
import re
import sys
import traceback

def noop(*args, **kwds): pass

#------------------------------------------------------------------------------------------------------------------------
# Argr
#--------------------------------------------------------------------------------------------------------------------

class ArgInvalidException(Exception):
    def __init__(self, argr): super().__init__(f'[{argr.argI + argr.argIOff}] {argr.argV[argr.argI]!r}')
    
class ArgNormalUnexpectedException(ArgInvalidException): pass
class ArgCallableParametersException(ArgInvalidException): pass
class ArgCallableExpectedException(ArgInvalidException): pass
class ArgValueTypeUnexpectedException(ArgInvalidException): pass

class ArgrOp:
    def __init__(self, fun, paramN):
        self.fun = fun
        self.paramN = paramN

class Argr:
    def __init__(self, op=None):
        self.op = self.opFromCallable(self.opArgInvalid if None is op else op)
        self.opD = {}
        self.kvD = {}

    def uninitAdd(self, uninit):
        self.uninitV.append(uninit)
            
    def argVGo(self, argV, argIOff):
        self.argV = argV
        self.argIOff = argIOff
        self.opV = []
        self.argI = 0
        for arg in argV:
            self.arg1Go(arg)
            self.argI += 1
        self.opGo()
        return self
            
    def argVGoUninit(self, argV, argIOff):
        self.uninitV = []
        try:
            return self.argVGo(argV, argIOff)
        except:
            traceback.print_exception(*sys.exc_info())
        finally:
            for uninit in reversed(self.uninitV):
                uninit()
            
    ArgRe = re.compile(r'-(\S+?)(?:=(.*))?', re.S)
            
    def arg1Go(self, arg):
        if None is not (m := self.ArgRe.fullmatch(arg)):
            # special arg. exec any accumulated op
            self.opGo()
                
            # determine type of arg
            k,v = m.group(1),m.group(2)
            if None is v:
                # op 
                self.op = self.opD.get(k)
                if None is self.op:
                    self.op = self.opD[k] = self.opImplicit(k)
            else:
                # kv
                kv = self.kvD.get(k)
                if None is kv:
                    kv = self.kvD[k] = self.kvImplicit(k)
                kv(v)
        else:
            # normal arg
            if len(self.opV) == self.op.paramN:
                self.opGo()
            self.opV.append(arg)

    def opGo(self):
        self.op.fun(*self.opV)
        self.opV = []
        
    def opImplicit(self, key):
        obj,attr,val = self.keyLookup(key)
        if not callable(val):
            raise ArgCallableExpectedException(self)
        return self.opFromCallable(val)

    def opFromCallable(self, fun):
        nVar = False
        n = 0
        for param in inspect.signature(fun).parameters.values():
            if (inspect.Parameter.POSITIONAL_ONLY == param.kind
                or inspect.Parameter.POSITIONAL_OR_KEYWORD == param.kind):
                n += 1
            elif inspect.Parameter.VAR_POSITIONAL == param.kind:
                nVar = True
            else:
                raise ArgCallableParametersException(self)
        return ArgrOp(fun, None if nVar else n)

    def opArgInvalid(self, *args):
        if args:
            raise ArgUnexpectedException(self)

    def keyTranslate(self, key):
        return f'self.{key}'.rsplit('.', 1)
        
    def keyLookup(self, key):
        obj,attr = self.keyTranslate(key)
        try:
            obj = eval(obj)
            return obj, attr, getattr(obj, attr)
        except AttributeError:
            pass
        raise ArgInvalidException(self)

    def kvImplicit(self, key):
        obj,attr,val = self.keyLookup(key)
        if None is not (argrKv := getattr(val, 'argrKv', None)):
            return argrKv(obj, attr)
        elif isinstance(val, str):
            return lambda x: setattr(obj, attr, x)
        elif isinstance(val, float):
            return lambda x: setattr(obj, attr, float(x))
        elif isinstance(val, int):
            return lambda x: setattr(obj, attr, int(x))
        else:
            raise ArgValueTypeUnexpectedException(self)

    def kvLog(self, key, val, fun):
        code = compile(f'self.{key} = fun if int(x) else noop', '<string>', 'exec')
        kv = self.kvD[key] = lambda x: exec(code, globals(), {'self':self, 'fun':fun, 'x':x})
        kv(val)
    
    #def kvSet(self, key, val, kv):
    #    self.kvD[key] = kv
    #    kv(val)
    #    return kv
        
#------------------------------------------------------------------------------------------------------------------------
# PathArg PathSubArg

class PathArg:
    def __init__(self, path):
        self.path = path

    def argrKv(self, obj, attr):
        return self.__init__

    def join(self, *paths):
        return os.path.join(self.path, *paths)

class PathSubArg(PathArg):
    def __init__(self, up, path):
        self.up = up
        self.path = path

    def set(self, path):
        self.path = path

    def argrKv(self, obj, attr):
        return self.set
        
    def join(self, *paths):
        return self.up.join(self.path, *paths)

#------------------------------------------------------------------------------------------------------------------------
# Main2
#--------------------------------------------------------------------------------------------------------------------

class Main2ArgInvalidException(Exception): pass
class Main2ArgTargetFunctionHasKeywordException(Exception): pass
class Main2ArgTargetTypeUnexpectedException(Exception): pass
class Main2ArgTargetNotCallableException(Exception): pass

class Main2:
    def __init__(self, argMap):
        self.argMap = argMap
        
    ArgRe = re.compile(r'-([A-Za-z0-9_.]+)(?:=(.*))?', re.S)

    def argFinGo(self): pass

    def argVGoFin(self, argV, argIOff):
        try:
            self.argVGo(argV, argIOff)
        except:
            traceback.print_exception(*sys.exc_info())
        self.argFinGo()

    def argVGo(self, argV, argIOff):
        self.argV = argV
        self.argIOff = argIOff
        self.argOp0 = None
        # self.argOpV
        # self.argOpVLimit
        self.argI = 0
        for arg in argV:
            if None is not (m := self.ArgRe.fullmatch(arg)):
                # special arg. exec any accumulated op
                if None is not self.argOp0:
                    self.argOpGo()
                    self.argOp0 = None

                # follow . references in key (left of =, or entire arg if no =)
                v0 = self.argMap
                for attr in k.split('.'):
                    obj = v0
                    if None is (v0 := getattr(obj, attr, None)):
                        raise Main2ArgInvalidException(self.argIOff + self.argI, arg)

                # at this point obj[attr] = v0
                if None is not v:
                    self.argKvGo(obj, attr, v, v0)
                elif callable(v0):
                    self.argOp0Go(v0)
                else:
                    raise Main2ArgTargetNotCallableException(self.argIOff + self.argI, arg)
            else:
                # normal arg
                if None is not self.argOp0:
                    if self.argOpVLimit != len(self.argOpV):
                        self.argOpV.append(arg)
                    else:
                        self.argOpGo()
                        self.argOp0 = None
                        self.argNormalGo(arg)
                else:
                    self.argNormalGo(arg)
            self.argI += 1
        if None is not self.argOp0:
            self.argOpGo()

    def argKvGo(self, obj, attr, v, v0):
        if None is not (f := getattr(v0, 'argKvSet', None)):
            return f(v)
        elif isinstance(v0, str):
            return setattr(obj, attr, v)
        elif isinstance(v0, int):
            return setattr(obj, attr, int(v))
        else:
            raise Main2ArgTargetTypeUnexpectedException(self.argIOff + self.argI, self.argV[self.argI])

    def argNormalGo(self, arg):
        raise Main2ArgInvalidException(self.argIOff + self.argI, self.argV[self.argI])

    def argOpGo(self):
        return self.argOp0(*self.argOpV)

    def argOp0Go(self, fun):
        nVar = False
        n = 0
        for param in inspect.signature(fun).parameters.values():
            if (inspect.Parameter.POSITIONAL_ONLY == param.kind
                or inspect.Parameter.POSITIONAL_OR_KEYWORD == param.kind):
                n += 1
            elif inspect.Parameter.VAR_POSITIONAL == param.kind:
                nVar = True
            else:
                raise Main2ArgTargetFunctionHasKeywordException(self.argIOff + self.argI, self.argV[self.argI])
        self.argOp0 = fun
        self.argOpI = self.argI
        self.argOpV = []
        self.argOpVLimit = None if nVar else n

    def dbgLog(self, logF, val):
        opt = DbgLogOpt(self, logF, val)
        setattr(self, 'dbg' + logF.__name__[3:], opt)

#------------------------------------------------------------------------------------------------------------------------
# DbgLogOpt
#--------------------------------------------------------------------------------------------------------------------

class DbgLogOpt:
    def __init__(self, main, logF, val):
        self.main = main
        self.logF = logF
        self.argKvSet(val)
        
    def argKvSet(self, val):
        if noop is getattr(self.main, self.logF.__name__):
            delattr(self.main, self.logF.__name__)
        if not (val := int(val)):
            setattr(self.main, self.logF.__name__, noop)
    
#------------------------------------------------------------------------------------------------------------------------
# PathOpt
#--------------------------------------------------------------------------------------------------------------------

class PathOpt:
    def __init__(self, path):
        self.path = path

    def argKvSet(self, path):
        self.path = path
        
    def get(self, *paths):
        return os.path.join(self.path, *paths)

    def sub(self, *paths):
        return PathSubOpt(self, paths)

class RelPathOpt(PathOpt):
    def __init__(self, path):
        super().__init__(path)
        self.relPre = os.path.realpath(path) + '/'
        
    def argKvSet(self, path):
        super().argKvSet(path)
        self.relPre = os.path.realpath(path) + '/'
        
    def relFrom(self, path):
        path = os.path.realpath(path)
        if path.startswith(self.relPre):
            return path[len(self.relPre):]
        return None

class PathSubOpt:
    def __init__(self, up, paths):
        self.up = up
        self.paths = paths

    def argKvSet(self, path):
        self.paths = [ path ]
    
    def get(self, *paths):
        return self.up.get(*self.paths, *paths)

    def sub(self, *paths):
        return PathSubOpt(self.up, self.paths + paths)
