# The search widget for the IF Archive

- Copyright 2025 by the Interactive Fiction Technology Foundation
- Distributed under the MIT license
- Created by Andrew Plotkin <erkyrath@eblong.com>

This is the web plugin that provides IF Archive search.

The service is built on Python, server-side WSGI, and the [Whoosh][] query library. At present there is no Javascript at all.

[Whoosh]: https://whoosh.readthedocs.io/en/latest/quickstart.html

## The basic deal

The search index is built directly from the [`Master-Index.xml`][masterindex] file, which is generated on the Archive by the [ifmap][] tool. `Master-Index.xml` contains all the text descriptions of the files, as well as the rest of the metadata. So there is no need to scan the HTML files on disk.

[masterindex]: https://ifarchive.org/indexes/Master-Index.xml
[ifmap]: https://github.com/iftechfoundation/ifarchive-ifmap-py

We include a few metadata fields (`size`, `date`, `tuid`) in the searchable index. Note that this is not all of them. (You can't search on `md5` for example.)

## Contents

- `search.wsgi`: A Python script that handles the main web interface. This lives in /var/ifarchive/wsgi-bin.
- `searchlib`: App-specific support for `admin.wsgi`. Lives in /var/ifarchive/wsgi-bin.
- `templates`: HTML templates for the search page. Lives in /var/ifarchive/lib/searchtpl.
- `sample.config`: Config file. Lives in /var/ifarchive/lib/ifarch.config. Note that the version in this repository is an incomplete sample. The real ifarch.config has settings for other tools (upload, ifmap, admintool).

This also relies on:

- `tinyapp`: A general web-app framework for WSGI apps. This is part of the [admintool][] repo.
- `css/ifarchive.css`: Archive stylesheet, which includes the search page styles. Part of the [ifarchive-static][] repo.

[admintool]: https://github.com/iftechfoundation/ifarchive-admintool
[ifarchive-static]: https://github.com/iftechfoundation/ifarchive-static

## Command-line use

    python3 /var/ifarchive/wsgi-bin/search.wsgi

This will display a list of command-line commands. These include:

    search.wsgi build [ --create ]

Rebuild the search index from `Master-Index.xml`. The search app should detect the update and provide the updated search info immediately.

The `--create` option wipes the search index completely (if present) and recreates it from scratch. You should only need to do this once. After using this option, restart httpd.

    search.wsgi search [ --page PAGE ] [ --limit LIMIT ] QUERY

Perform a search on the command line. Normally returns a maximum of 10 results per page; you can increase this with `--limit`. If there are more results, use `--page 2` and so on.

## Testing

It is possible to test the admin interface on a local Apache server. See the [TESTING.md][] file in the [admintool][] repo. (Except this repo is not yet set up for Docker.)

[TESTING.md]: https://github.com/iftechfoundation/ifarchive-admintool/blob/main/TESTING.md
