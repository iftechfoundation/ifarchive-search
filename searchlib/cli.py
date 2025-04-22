import argparse
import os, os.path

def run(appinstance):
    """The entry point when search.wsgi is invoked on the command line.
    """
    popt = argparse.ArgumentParser(prog='search.wsgi')
    subopt = popt.add_subparsers(dest='cmd', title='commands')

    popt_build = subopt.add_parser('build', help='build the search index')
    popt_build.set_defaults(cmdfunc=cmd_build)
    popt_build.add_argument('--create', action='store_true')
    
    popt_search = subopt.add_parser('search', help='perform a search')
    popt_search.set_defaults(cmdfunc=cmd_search)
    popt_search.add_argument('query')
    popt_search.add_argument('-l', '--limit', type=int, default=0)
    popt_search.add_argument('-p', '--page', type=int, default=1)

    args = popt.parse_args()

    if not args.cmd:
        popt.print_help()
        return

    args.cmdfunc(args, appinstance)

def cmd_build(args, app):
    """Build or rebuild the search index.
    This reads Master-Index.xml and rebuilds the search index. It
    cleans out and replaces all the existing entries.
    
    Use --create if you are creating a completely new search index.
    You probably only need to do this if the schema changes. Restart
    httpd after using this option.
    """
    import ifarchivexml
    from whoosh.index import create_in, open_dir
    from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, NUMERIC, STORED
    import whoosh.writing
    from whoosh.analysis import StemmingAnalyzer, CharsetFilter
    from whoosh.support.charset import accent_map
    
    (root, dirs, files) = ifarchivexml.parse(app.masterindexpath)

    if args.create:
        print('Creating index from scratch...')
        analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)
    
        # STORED fields are returned as part of the result object; they are not
        #   indexed (not searchable).
        # stored=True fields are returned as part of the result object, but they
        #   *are* searchable.
        # KEYWORD fields are searchable lists.
        # The "description" field gets fancy full-text searchability, including
        #   stemming, accent-folding, etc.
        
        schema = Schema(
            type=STORED,           # "file" or "dir"
            description=TEXT(analyzer=analyzer),   # the primary search text
            shortdesc=STORED,      # snippet of the description; displayed not indexed
            name=ID,               # bare filename
            path=ID(stored=True),  # full path
            dir=KEYWORD(commas=True),  # directory segments, comma-separated list
            date=DATETIME(stored=True),
            size=NUMERIC,          # in bytes
            tuid=KEYWORD,          # tuids, space-separated list
        )
        index = create_in(app.searchindexdir, schema)
    else:
        print('Rebuilding index...')
        index = open_dir(app.searchindexdir)

    SHORTDESC = 300
    writer = index.writer()
    writer.commit(mergetype=whoosh.writing.CLEAR)
    
def cmd_search(args, app):
    """Perform a search and display the result(s).
    """
    try:
        query = app.queryparser.parse(args.query)
    except Exception as ex:
        print('query parse failed (%s)' % (ex,))
        return
    
    with app.getsearcher() as searcher:
        pagelen = args.limit or app.pagelen
        results = searcher.search_page(query, args.page, pagelen=pagelen)
        resultcount = len(results)

        pagecount = ((resultcount+pagelen-1) // pagelen)
        showmin = (args.page-1) * pagelen + 1
        showmax = min(showmin+pagelen-1, resultcount)

        corrected = searcher.correct_query(query, args.query)
        if corrected.query != query:
            print('Did you mean: "%s"' % (corrected.string,))
        
        if not len(results):
            print('No results')
            return

        if resultcount > pagelen:
            val = 'page %d (%d-%d) of ' % (args.page, showmin, showmax,)
        else:
            val = ''
        print('Showing %s%d results in %.04f sec:' % (val, len(results), results.results.runtime,))
        print()
        
        for res in results:
            fields = res.fields()
            if 'date' in fields:
                val = '(%s: %s)' % (fields['type'], fields.get('date'),)
            else:
                val = '(%s)' % (fields['type'],)
            print('* %s  %s' % (fields['path'], val,))
            if 'shortdesc' in fields:
                print(fields['shortdesc'].replace('\n', ' '))
            print()
    
    
