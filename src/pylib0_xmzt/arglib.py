import re

#--------------------------------------------------------------------------------------------------------------
# argument processing and main loop

ArgRe = re.compile(r'-([^=]*)(?:=(.*))?', re.S)

def keyObjAttr(obj, k):
    segV = k.split('.')
    attr = segV.pop()
    for seg in segV:
        obj = getattr(obj, seg)
    return (obj, attr)

def valObj(v):
    try:
        return int(v)
    except:
        pass
    try:
        return float(v)
    except:
        pass
    return v

def opGo(op, opArgV):
    if None is not (ret := op(*opArgV)):
        print(f'[result] {ret!r}')

def argVGo(obj, argV, argI):
    op = None
    for argI in range(argI,len(argV)):
        if (m := ArgRe.fullmatch(arg := argV[argI])):
            # new -key or -key=val expr. execute accumulated op first
            if None is not op:
                opGo(op, opArgV)
                op = None
            # parse key
            kObj,kAttr = keyObjAttr(obj, m.group(1))
            if None is (v := m.group(2)):
                # -key format, keep parsing args until next -key
                op = getattr(kObj, kAttr)
                opArgV = []
            else:
                # -key=val format. parse val first.
                setattr(kObj, kAttr, valObj(v))
        elif None is not op:
            opArgV.append(valObj(arg))
        else:
            raise Exception(f'arg unexpected nonspecial: [{argI}] {arg!r}')
    if None is not op:
        opGo(op, opArgV)
