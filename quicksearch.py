import sys

querytext = sys.argv[1]

from whoosh.index import open_dir

index = open_dir('searchindex')

from whoosh.qparser import QueryParser
from whoosh.qparser.dateparse import DateParserPlugin

def dosearch(querytext):
    # The search object caches stuff, but can only be used in one thread at a time
    # can be expired if the index updates
    # just refresh it
    with index.searcher() as searcher:
        qparser = QueryParser('description', index.schema)
        qparser.add_plugin(DateParserPlugin(free=True))
        try:
            query = qparser.parse(querytext)
        except:
            print('query parse failed')
            return
        results = searcher.search(query)
        if not len(results):
            print('no results')
        else:
            print(len(results), 'results:')
        for res in results:
            fields = res.fields()
            if 'date' in fields:
                val = '(%s: %s)' % (fields['type'], fields.get('date'),)
            else:
                val = '(%s)' % (fields['type'],)
            print(fields['path'], val)
        corrected = searcher.correct_query(query, querytext)
        if corrected.query != query:
            print("Did you mean:", corrected.string)

dosearch(querytext)
