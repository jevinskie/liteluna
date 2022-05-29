from amaranth.hdl.ast import Signal
from amaranth.hdl.rec import Record


def get_signals(obj, recurse=False):
    signals = set()
    for attr_name in dir(obj):
        if attr_name[:2] == "__" and attr_name[-2:] == "__":
            continue
        attr = getattr(obj, attr_name)
        if isinstance(attr, Signal):
            signals.add(attr)
        elif isinstance(attr, Record):
            for robj in attr.flatten():
                if isinstance(robj, Signal):
                    signals.add(robj)
        elif recurse and isinstance(attr, Module):
            signals |= get_signals(attr, recurse=True)

    return signals
