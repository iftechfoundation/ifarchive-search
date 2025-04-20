import datetime
import re

### create vs rebuild
### store in sqlite?
### tuid

# https://whoosh.readthedocs.io/en/latest/intro.html

from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, NUMERIC, STORED
from whoosh.analysis import StemmingAnalyzer, CharsetFilter
from whoosh.support.charset import accent_map

import ifarchivexml
(root, dirs, files) = ifarchivexml.parse('Master-Index.xml')

# Analyzer that does case-folding, stopwords, stemming, and accent-folding
analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)

schema = Schema(
    type=STORED,
    description=TEXT(analyzer=analyzer),
    name=ID,
    path=ID(stored=True),
    date=DATETIME(stored=True),
    size=NUMERIC,
    tuid=KEYWORD,
    )

index = create_in('indexdir', schema)
### or don't, if we want to reindex from scratch without interrupting existing readers. (mergetype=writing.CLEAR)

pat_markdownlink = re.compile('\\[([^\\]]*)\\]\\([^)]*\\)')

def builddesc(obj):
    alldesc = []
    if obj.description:
        alldesc.append(obj.description)
    for desc in obj.parentdescs.values():
        if desc:
            alldesc.append(desc)
        
    if not alldesc:
        return None

    alldesc = [ pat_markdownlink.sub('\\1', val) for val in alldesc ]
    
    return '\n'.join(alldesc)

itemcount = 0

writer = index.writer()

for dir in dirs.values():
    _, _, name = dir.name.rpartition('/')
    alldesc = builddesc(dir)
        
    tuids = None
    if dir.metadata and 'tuid' in dir.metadata:
        tuids = ' '.join(dir.metadata['tuid'])
        
    writer.add_document(
        path = dir.name,
        name = name,
        type = 'dir',
        description = alldesc,
        tuid = tuids,
    )
    itemcount += 1
    
for file in files.values():
    if file.symlink:
        continue
    date = None
    if file.rawdate is not None:
        date = datetime.datetime.fromtimestamp(file.rawdate)

    alldesc = builddesc(file)
    
    tuids = None
    if file.metadata and 'tuid' in file.metadata:
        tuids = ' '.join(file.metadata['tuid'])

    writer.add_document(
        path = file.path,
        name = file.name,
        type = 'file',
        description = alldesc,
        date = date,
        size = file.size,
        tuid = tuids,
    )
    itemcount += 1

writer.commit()

print('Indexed %d items' % (itemcount,))
