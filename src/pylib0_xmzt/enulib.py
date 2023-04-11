#newer than denumlib
#
#
# create function calls type() to create new type, hence the need for the type name
#
# Usage:
#     Foo = Enu.create('Foo', 'a', 'b', 'c', val=1, inc=1)
#     x = Foo.b
#     x => 2
#     x.des() => 'b'

#------------------------------------------------------------------------------------------------------------------------
# Enu
#------------------------------------------------------------------------------------------------------------------------

class EnuItem:
    def __init__(self, iden, val):
        self.iden = iden
        self.val = val

    def __repr__(self):
        return f'{self.__class__.__name__}({self.iden!r}, 0x{self.val:x})'

class Enu(int):
    def __new__(cls, val):
        return int.__new__(cls, val)

    def __add__(self, other): return self.__class__(int(self) + other)
    def __sub__(self, other): return self.__class__(int(self) - other) 
    def __and__(self, other): return self.__class__(int(self) & other) 
    def __xor__(self, other): return self.__class__(int(self) ^ other) 
    def __or__(self, other) : return self.__class__(int(self) | other) 

    def __radd__(self, other): return self.__class__(other + int(self))
    def __rsub__(self, other): return self.__class__(other - int(self)) 
    def __rand__(self, other): return self.__class__(other & int(self)) 
    def __rxor__(self, other): return self.__class__(other ^ int(self)) 
    def __ror__(self, other) : return self.__class__(other | int(self)) 

    def __repr__(self):
        return f'<{self.__class__.__name__}>{self.des()}'

    def __str__(self):
        return self.des()

    @classmethod
    def addItem(cls, item):
        cls.ItemV.append(item)
        setattr(cls, item.iden, cls(item.val))
        cls.ItemByVal[item.val] = item
        return cls
        
    @classmethod
    def addV(cls, argV, val=0, inc=1):
        for arg in argV:
            cls.addItem(EnuItem(arg, val))
            val += inc
        return cls

    @classmethod
    def create(cls, typName):
        return type(typName, (cls,), { 'ItemV': [], 'ItemByVal': {} })

    def des(self):
        return f'0x{self:x}' if None is (x := self.ItemByVal.get(self)) else x.iden

    @classmethod
    def dump(cls, logr, pre):
        with logr(f'{pre}{cls.__name__}'):
            with logr(f'ItemV'):
                for item in cls.ItemV:
                    logr(f'{item!r}')
            with logr(f'ItemByVal'):
                for val,item in cls.ItemByVal.items():
                    logr(f'0x{val:x}: {item!r}')
        
#------------------------------------------------------------------------------------------------------------------------
# EnuBitmap
#------------------------------------------------------------------------------------------------------------------------
    
class EnuBitmapItem:
    def __init__(self, iden, val, mask):
        self.iden = iden
        self.val = val
        self.mask = mask

    def __repr__(self):
        return f'{self.__class__.__name__}({self.iden!r}, 0x{self.val:x}, 0x{self.mask:x})'

class EnuBitmap(Enu):
    @classmethod
    def add(cls, iden, val, mask, **kwargs):
        item = EnuBitmapItem(iden, val, mask)
        for k,v in kwargs.items():
            setattr(item, k, v)
        cls.addItem(item)
        return cls
        
    @classmethod
    def addItem(cls, item):
        super().addItem(item)
        cls.MaskSet[item.mask] = None
        return cls
        
    @classmethod
    def addV(cls, argV, val=0, inc=1):
        for arg in argV:
            cls.addItem(EnuBitmapItem(arg, 1<<val, 1<<val))
            val += inc
        return cls
        
    @classmethod
    def create(cls, typName):
        typ = type(typName, (cls,), { 'ItemV': [], 'ItemByVal': {}, 'MaskSet': {} })
        typ._0 = typ(0)
        return typ

    @classmethod
    def dump(cls, logr, pre):
        super().dump(logr, pre)
        with logr:
            logr(f'MaskSet {" ".join([f"{x:x}" for x in cls.MaskSet])}')
    
    def des(self, sep='|'):
        dst = []
        x = int(self)
        for mask in self.MaskSet:
            if None is not (item := self.ItemByVal.get(mask & x)):
                dst.append(item.iden)
                x ^= item.val
        if not dst or x:
            dst.append(f'0x{x:x}')
        return sep.join(dst)
