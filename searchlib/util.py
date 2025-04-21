import re

filehash_pattern = re.compile('([^a-zA-Z0-9_.,;:()@/-])')
filehash_escaper = lambda match: '=%02X=' % (ord(match.group(1)),)
def filehash(val):
    """Escape a filename in a way that can appear in a DOM id or URL
    fragment (dir#filename). This also works on full pathnames.
    (Nothing in the system needs to reverse this mapping, but it
    should be unique.)
    This is a bit arbitrary. Almost any non-whitespace character is legal
    in those domains; you just have to HTML-escape or URL-escape it.
    However, we want to pass dir#file URLs around with a minimum of fuss,
    so it's worth encoding Unicode and the fussier punctuation.
    (This is copied from ifmap.py, and must be consistent with it.)
    """
    return filehash_pattern.sub(filehash_escaper, val)
    
