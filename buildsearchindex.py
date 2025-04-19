import datetime
import re

### stemming
### store in sqlite?

from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, STORED

import ifarchivexml
(root, dirs, files) = ifarchivexml.parse('Master-Index.xml')

schema = Schema(
    type=STORED,
    description=TEXT,
    name=ID,
    path=ID(stored=True),
    date=DATETIME(stored=True),
    size=NUMERIC,
    )

index = create_in('indexdir', schema)
### or don't, if we want to reindex from scratch without interrupting existing readers. (mergetype=writing.CLEAR)

pat_markdownlink = re.compile('\\[([^\\]]*)\\]\\([^)]*\\)')

def builddesc(obj):
    alldesc = []
    if dir.description:
        alldesc.append(dir.description)
    for desc in dir.parentdescs.values():
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
        
    writer.add_document(
        path = dir.name,
        name = name,
        type = 'dir',
        description = alldesc,
    )
    itemcount += 1
    
for file in files.values():
    if file.symlink:
        continue
    date = None
    if file.rawdate is not None:
        date = datetime.datetime.fromtimestamp(file.rawdate)

    alldesc = builddesc(dir)

    writer.add_document(
        path = file.path,
        name = file.name,
        type = 'file',
        description = alldesc,
        date = date,
        size = file.size,
    )
    itemcount += 1

writer.commit()

print('Indexed %d items' % (itemcount,))
