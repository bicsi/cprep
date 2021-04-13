def pad(s: str, n: int = 25):
    in_c = False
    char_pos = []
    for i, c in enumerate(s):
        # print(repr(c))
        if c == '\x1b':
            in_c = True
        if not in_c:
            char_pos.append(i)
        if c == 'm':
            in_c = False 
        
    if len(char_pos) > n:
        while len(char_pos) > n - 3:
            s = s[:char_pos[-1]] + s[(char_pos[-1] + 1):]
            char_pos.pop(-1)
        return s + '...'
    return s + ' ' * (n - len(char_pos))

