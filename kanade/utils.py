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