import datetime
import re

### create vs rebuild

# https://whoosh.readthedocs.io/en/latest/intro.html

from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, NUMERIC, STORED
from whoosh.analysis import StemmingAnalyzer, CharsetFilter
from whoosh.support.charset import accent_map

import ifarchivexml
(root, dirs, files) = ifarchivexml.parse('Master-Index.xml')

# Analyzer that does case-folding, stopwords, stemming, and accent-folding
analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)

SHORTDESC = 300

schema = Schema(
    type=STORED,
    description=TEXT(analyzer=analyzer),
    shortdesc=STORED,
    name=ID,
    path=ID(stored=True),
    dir=KEYWORD,
    date=DATETIME(stored=True),
    size=NUMERIC,
    tuid=KEYWORD,
    )

pat_markdownlink = re.compile('\\[([^\\]]*)\\]\\([^)]*\\)')

def builddesc(obj, all=True):
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

index = create_in('searchindex', schema)
### or don't, if we want to reindex from scratch without interrupting existing readers. (mergetype=writing.CLEAR)

writer = index.writer()

itemcount = 0
dirdescmap = {}

for dir in dirs.values():
    if dir.name == 'if-archive':
        # skip the root
        continue
    
    dirstr = None
    dls = dir.name.split('/')
    if dls and dls[0] == 'if-archive':
        del dls[0]
    if dls:
        dirstr = ' '.join(dls)

    _, _, name = dir.name.rpartition('/')
    alldesc = builddesc(dir)

    shortdesc = builddesc(dir, all=False)
    if shortdesc:
        shortdesc = shortdesc.strip()
    if shortdesc:
        dirdescmap[dir.name] = shortdesc
        
    tuids = None
    if dir.metadata and 'tuid' in dir.metadata:
        tuids = ' '.join(dir.metadata['tuid'])
        
    writer.add_document(
        path = dir.name,
        name = name,
        dir = dirstr,
        type = 'dir',
        description = alldesc,
        shortdesc = shortdesc,
        tuid = tuids,
    )
    itemcount += 1
    
for file in files.values():
    if file.symlink:
        continue
    date = None
    if file.rawdate is not None:
        date = datetime.datetime.fromtimestamp(file.rawdate)

    dirstr = None
    dls = file.directory.split('/')
    if dls and dls[0] == 'if-archive':
        del dls[0]
    if dls:
        dirstr = ' '.join(dls)

    alldesc = builddesc(file)
    
    shortdesc = builddesc(file, all=False)
    if shortdesc:
        shortdesc = shortdesc.strip()
    if shortdesc:
        if len(shortdesc) > SHORTDESC:
            shortdesc = shortdesc[ 0 : SHORTDESC ] + '...'
    if not shortdesc:
        shortdesc = dirdescmap.get(file.directory, None)
        
    tuids = None
    if file.metadata and 'tuid' in file.metadata:
        tuids = ' '.join(file.metadata['tuid'])

    writer.add_document(
        path = file.path,
        name = file.name,
        dir = dirstr,
        type = 'file',
        description = alldesc,
        shortdesc = shortdesc,
        date = date,
        size = file.size,
        tuid = tuids,
    )
    itemcount += 1

writer.commit()

print('Indexed %d items' % (itemcount,))
