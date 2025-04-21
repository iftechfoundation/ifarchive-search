import argparse
import os, os.path

def run(appinstance):
    """The entry point when search.wsgi is invoked on the command line.
    """
    popt = argparse.ArgumentParser(prog='search.wsgi')
    subopt = popt.add_subparsers(dest='cmd', title='commands')

    popt_search = subopt.add_parser('search', help='perform a search')
    popt_search.set_defaults(cmdfunc=cmd_search)
    popt_search.add_argument('query')
    popt_search.add_argument('-p', '--page', type=int, default=1)

    args = popt.parse_args()

    if not args.cmd:
        popt.print_help()
        return

    args.cmdfunc(args, appinstance)

def cmd_search(args, app):
    """Perform a search and display the result(s).
    """
    try:
        query = app.queryparser.parse(args.query)
    except Exception as ex:
        print('query parse failed (%s)' % (ex,))
        return
    
    with app.getsearcher() as searcher:
        results = searcher.search(query)
        
        corrected = searcher.correct_query(query, args.query)
        if corrected.query != query:
            print('Did you mean: "%s"' % (corrected.string,))
        
        if not len(results):
            print('No results')
            return

        print('%d results in %.04f sec:' % (len(results), results.runtime,))
        print()
        
        for res in results:
            fields = res.fields()
            if 'date' in fields:
                val = '(%s: %s)' % (fields['type'], fields.get('date'),)
            else:
                val = '(%s)' % (fields['type'],)
            print('* %s  %s' % (fields['path'], val,))
            if 'shortdesc' in fields:
                print(fields['shortdesc'])
            print()
    
    
