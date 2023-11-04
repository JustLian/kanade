def readable_dict(d: dict) -> list:
    r = []
    for k, v in d.items():
        if isinstance(v, dict):
            r.append('\n[{}]'.format(k))
            r.extend(readable_dict(v))
            r.append('\n')
        
        elif isinstance(v, list):
            r.append('{}: '.format(k) + ', '.join(list))
        
        else:
            r.append('{}: {}'.format(k, v))
    return r


def to_rgb(hx: str) -> tuple[int, int, int]:
    if hx.startswith('#'):
        hx = hx[1:]
    return tuple(int(hx[i:i+2], 16) for i in (0, 2, 4))
