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
    
pat_markdownlink = re.compile('\\[([^\\]]*)\\]\\([^)]*\\)')
def buildmddesc(obj, all=True):
    """Pull out the description from an IFDir or IFFile object, as
    loaded from Master-Index.xml.

    (This is used when building the search index.)

    The description is Markdown, but it will be searched or displayed
    as-is. (Except that we discard Markdown links -- those are not
    interesting for either searching or displaying.)

    We include all parentdescs, because they may have useful search terms,
    especially if the local description is empty.

    If all is False, we only return *one* description: the local one or
    the first parentdesc found.
    """
    alldesc = []
    if obj.description:
        alldesc.append(obj.description)
    for desc in obj.parentdescs.values():
        if alldesc and not all:
            break
        if desc:
            alldesc.append(desc)
        
    if not alldesc:
        return None

    alldesc = [ pat_markdownlink.sub('\\1', val) for val in alldesc ]
    
    return '\n'.join(alldesc)

