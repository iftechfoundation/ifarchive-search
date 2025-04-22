import xml.sax
import xml.sax.handler

"""ifarchivexml:

This module parses the Master-Index.xml file that is available at
<http://www.ifarchive.org/indexes/Master-Index.xml>.

You can use this module like this:
  import ifarchivexml
  (root, dirs, files) = ifarchivexml.parse('Master-Index.xml')

root is an IFDir object representing the root directory ('if-archive').
dirs is a dictionary mapping directory names ('if-archive/games', for
example) to IFDir objects. files is a dictionary mapping file pathname
('if-archive/games/playgame.FAQ', for example) to IFFile objects. 

You can display the contents of either an IFDir or IFFile object with
the obj.dump() method.

Dec 2019: Updated to Python 3; added sha512 and metadata fields.
Apr 2025: Added parentdesc field; support metadata field for directories;
  removed xdir field.
"""

CONTEXT_NONE = 0
CONTEXT_DIR = 1
CONTEXT_FILE = 2
CONTEXT_DIRLINK = 3
CONTEXT_FILELINK = 4
CONTEXT_METADATA = 5
CONTEXT_METAITEM = 5

class IFDir:
    description = None
    metadata = None
    def __init__(self):
        self.subdirs = []
        self.files = []
        self.parentdescs = {}
    def __repr__(self):
        return '<IFDir \'' + self.name + '\'>'
    def dump(self):
        print('name:   ', self.name)
        print('parent: ', self.parent, ('('+str(self.parentobj)+')'))
        print('subdircount:', self.subdircount)
        print('filecount:  ', self.filecount)
        if (self.metadata is not None):
            print('metadata:')
            for (key, valls) in self.metadata.items():
                print(' ', key+':', ', '.join(valls))
        if (self.description is not None):
            print('description:')
            print(self.description)
        for key in self.parentdescs:
            print('parentdesc (from %s)' % (key,))
            print(self.parentdescs[key])
        print('subdirs:')
        for subdir in self.subdirs:
            print(' ', str(subdir))
        print('files:')
        for file in self.files:
            print(' ', str(file))

class IFFile:
    size = None
    date = None
    md5 = None
    sha512 = None
    rawdate = None
    symlink = None
    metadata = None
    description = None
    def __init__(self):
        self.parentdescs = {}
    def __repr__(self):
        return '<IFFile \'' + self.path + '\'>'
    def dump(self):
        print('path:   ', self.path)
        print('name:   ', self.name)
        print('directory: ', self.directory, ('('+str(self.directoryobj)+')'))
        if (self.symlink == 'dir'):
            print('symlink to dir:')
            print('  name: ', self.symlinkname)
        if (self.symlink == 'file'):
            print('symlink to file:')
            print('  path: ', self.symlinkpath)
        print('size:   ', self.size)
        print('date:   ', self.date)
        print('rawdate:', self.rawdate)
        print('md5:    ', self.md5)
        print('sha512: ', self.sha512)
        print('orderindex:', self.orderindex)
        if (self.metadata is not None):
            print('metadata:')
            for (key, valls) in self.metadata.items():
                print(' ', key+':', ', '.join(valls))
        if (self.description is not None):
            print('description:')
            print(self.description)
        for key in self.parentdescs:
            print('parentdesc (from %s)' % (key,))
            print(self.parentdescs[key])

class IFAParser(xml.sax.handler.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)
        self.grabbeddata = ''
        self.curdir = None
        self.curfile = None
        self.curitem = None
        self.curmetaowner = None
        self.directories = {}
        self.files = {}
        self.orderindex = 0
        self.context = CONTEXT_NONE
        self.elements = {
            'ifarchive': (self.ignore_start, self.ifarchive_end),
            'directory': (self.directory_start, self.directory_end),
            'file': (self.file_start, self.file_end),
            'metadata': (self.metadata_start, self.metadata_end),
            'item': (self.item_start, self.item_end),
            'key': (self.grabdata_start, self.key_end),
            'value': (self.grabdata_start, self.value_end),
            'name': (self.grabdata_start, self.name_end),
            'filecount': (self.grabdata_start, self.filecount_end),
            'subdircount': (self.grabdata_start, self.subdircount_end),
            'parent': (self.grabdata_start, self.parent_end),
            'path': (self.grabdata_start, self.path_end),
            'size': (self.grabdata_start, self.size_end),
            'date': (self.grabdata_start, self.date_end),
            'rawdate': (self.grabdata_start, self.rawdate_end),
            'md5': (self.grabdata_start, self.md5_end),
            'sha512': (self.grabdata_start, self.sha512_end),
            'description': (self.grabdata_start, self.description_end),
            'parentdesc': (self.parentdesc_start, self.parentdesc_end),
            'symlink': (self.symlink_start, self.symlink_end),
        }
        
    def characters(self, data):
        self.grabbeddata = (self.grabbeddata + data)

    def startElement(self, name, attrs):
        if (name not in self.elements):
            return
        (startfunc, endfunc) = self.elements.get(name)
        startfunc(attrs)

    def endElement(self, name):
        if (name not in self.elements):
            return
        (startfunc, endfunc) = self.elements.get(name)
        endfunc()

    def ignore_start(self, dict):
        pass
    def ignore_end(self):
        pass

    def grabdata_start(self, dict):
        self.grabbeddata = ''
    def grabdata(self):
        dat = self.grabbeddata
        self.grabbeddata = ''
        return dat

    def directory_start(self, dict):
        if (self.context == CONTEXT_NONE):
            self.curdir = IFDir()
            self.context = CONTEXT_DIR
        elif (self.context == CONTEXT_FILE):
            self.grabdata_start(None)

    def directory_end(self):
        if (self.context == CONTEXT_DIR):
            name = self.curdir.name
            self.directories[name] = self.curdir
            self.curdir = None
            self.context = CONTEXT_NONE
        elif (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.directory = data

    def file_start(self, dict):
        if (self.context == CONTEXT_NONE):
            self.curfile = IFFile()
            self.context = CONTEXT_FILE

    def file_end(self):
        if (self.context == CONTEXT_FILE):
            path = self.curfile.path
            self.curfile.orderindex = self.orderindex
            self.orderindex = self.orderindex+1
            self.files[path] = self.curfile
            self.curfile = None
            self.context = CONTEXT_NONE

    def metadata_start(self, dict):
        if (self.context == CONTEXT_FILE):
            self.curmetaowner = self.curfile
            self.curfile.metadata = {}
            self.context = CONTEXT_METADATA
        elif (self.context == CONTEXT_DIR):
            self.curmetaowner = self.curdir
            self.curdir.metadata = {}
            self.context = CONTEXT_METADATA

    def metadata_end(self):
        if (self.context == CONTEXT_METADATA):
            if self.curmetaowner is self.curfile:
                self.context = CONTEXT_FILE
            elif self.curmetaowner is self.curdir:
                self.context = CONTEXT_DIR
            else:
                raise Exception()
        self.curmetaowner = None

    def item_start(self, dict):
        if (self.context == CONTEXT_METADATA):
            self.curitem = [None]
            self.context = CONTEXT_METAITEM

    def item_end(self):
        if (self.context == CONTEXT_METAITEM):
            if self.curitem[0] and len(self.curitem) > 1:
                self.curmetaowner.metadata[self.curitem[0]] = self.curitem[1:]
            self.curitem = None
            self.context = CONTEXT_METADATA

    def key_end(self):
        if (self.context == CONTEXT_METAITEM):
            val = self.grabdata()
            if (self.curitem is not None):
                self.curitem[0] = val
                
    def value_end(self):
        if (self.context == CONTEXT_METAITEM):
            val = self.grabdata()
            if (self.curitem is not None):
                self.curitem.append(val)
                
    def symlink_start(self, dict):
        if (self.context == CONTEXT_FILE):
            if (dict['type'] == 'dir'):
                self.context = CONTEXT_DIRLINK
                self.curfile.symlink = 'dir'
            else:
                self.context = CONTEXT_FILELINK
                self.curfile.symlink = 'file'

    def symlink_end(self):
        if (self.context == CONTEXT_DIRLINK):
            self.context = CONTEXT_FILE
        elif (self.context == CONTEXT_FILELINK):
            self.context = CONTEXT_FILE

    def name_end(self):
        if (self.context == CONTEXT_DIR):
            name = self.grabdata()
            if (self.curdir is not None):
                self.curdir.name = name
        elif (self.context == CONTEXT_FILE):
            name = self.grabdata()
            if (self.curfile is not None):
                self.curfile.name = name
        elif (self.context == CONTEXT_DIRLINK):
            name = self.grabdata()
            if (self.curfile is not None):
                self.curfile.symlinkname = name

    def parent_end(self):
        if (self.context == CONTEXT_DIR):
            data = self.grabdata()
            if (self.curdir is not None):
                self.curdir.parent = data

    def subdircount_end(self):
        if (self.context == CONTEXT_DIR):
            data = self.grabdata()
            if (self.curdir is not None):
                self.curdir.subdircount = int(data)

    def filecount_end(self):
        if (self.context == CONTEXT_DIR):
            data = self.grabdata()
            if (self.curdir is not None):
                self.curdir.filecount = int(data)

    def path_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.path = data
        elif (self.context == CONTEXT_FILELINK):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.symlinkpath = data

    def size_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.size = int(data)

    def date_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.date = data

    def rawdate_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.rawdate = int(data)

    def md5_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.md5 = data

    def sha512_end(self):
        if (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.sha512 = data

    def parentdesc_start(self, dict):
        if (self.context == CONTEXT_DIR or self.context == CONTEXT_FILE):
            self.grabbeddata = ''
            self.curitem = dict['dir']
        
    def parentdesc_end(self):
        if (self.context == CONTEXT_DIR):
            data = self.grabdata()
            if (self.curdir is not None):
                self.curdir.parentdescs[self.curitem] = data
            self.curitem = None
        elif (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.parentdescs[self.curitem] = data
            self.curitem = None
                
    def description_end(self):
        if (self.context == CONTEXT_DIR):
            data = self.grabdata()
            if (self.curdir is not None):
                self.curdir.description = data
        elif (self.context == CONTEXT_FILE):
            data = self.grabdata()
            if (self.curfile is not None):
                self.curfile.description = data

    def ifarchive_end(self):
        for dir in self.directories.values():
            parent = dir.parent
            if (parent == ''):
                dir.parentobj = None
            else:
                dir.parentobj = self.directories[parent]
                dir.parentobj.subdirs.append(dir)
        for file in self.files.values():
            parent = file.directory
            file.directoryobj = self.directories[parent]
            file.directoryobj.files.append(file)

def parse(filename):
    parser = IFAParser()

    fl = open(filename, 'r')
    xml.sax.parse(fl, parser)
    fl.close()

    rootdir = parser.directories['if-archive']
    result = (rootdir, parser.directories, parser.files)
    return result
