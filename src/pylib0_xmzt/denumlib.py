class DenumItem(int):
    #todo? __slots__ = [ 'iden', 'val', 'mask' ]

    def __new__(cls, iden, val, mask):
        self = int.__new__(cls, val)
        self.iden = iden
        self.val = val
        self.mask = mask
        return self

    def __repr__(self):
        return f'DenumItem({self.iden!r}, 0x{self.val:x}, 0x{self.mask:x})'

class Denum:
    @classmethod
    def init(cls):
        cls.ItemV = []
        cls.ItemByVal = {}
        return cls

    @classmethod
    def byVal(cls, val):
        return cls.ItemByVal.get(val)
    
    @classmethod
    def add(cls, iden, val, mask, **kwargs):
        item = DenumItem(iden, val, mask)
        for k,v in kwargs.items():
            setattr(item, k, v)
        cls.ItemV.append(item)
        setattr(cls, item.iden, item)
        cls.ItemByVal[item.val] = item
        return item
    
    @staticmethod
    def order(x):
        i = 1
        while x := x >> 1:
            i += 1
        return i

    @classmethod
    def maskFromIdenPre(cls, idenPre):
        mask = 0
        for item in cls.ItemV:
            if item.iden.startswith(idenPre):
                mask |= item.mask
        return mask

    @classmethod
    def maskFromIdenPreAssign(cls, idenPre):
        mask = 0
        updateV = []
        for item in cls.ItemV:
            if item.iden.startswith(idenPre):
                mask |= item.mask
                updateV.append(item)
        for item in updateV:
            item.mask = mask
        return mask

    @classmethod
    def firstIdenPre(cls, idenPre):
        for item in cls.ItemV:
            if item.iden.startswith(idenPre):
                return item

    @classmethod
    def des(cls, x, sep='|'):
        dst = []
        for item in cls.ItemV:
            if item.mask & x == item.val:
                dst.append(item.iden)
                x ^= item.val
        if x:
            dst.append(f'0x{x:x}')
        return sep.join(dst)

    @classmethod
    def codeCInit(cls, cTyp, cIden):
        cls.CTyp = cTyp
        cls.CIden = cIden
    
    @classmethod
    def codeCDefines(cls):
        return ''.join([f'#define {cls.CIden}_{item.iden} {cls.valFmt(item.val)}\n' for item in cls.ItemV])

    @classmethod
    def codeCDesProto(cls):
        return f'const char * {cls.CIden}Des({cls.CTyp} x);'
    
    @classmethod
    def codeCDes(cls):
        cases = '\n'.join([f'    case {cls.CIden}_{item.iden}: return "{item.iden}";' for item in cls.ItemV if item.mask])
        return f'''const char * {cls.CIden}Des({cls.CTyp} x) {{
    switch(x) {{
        {cases}
        default: return NULL;
    }}
}}
'''
    
    @classmethod
    def valFmt(cls, x):
        return str(x)
