import argparse
import os, os.path

def run(appinstance):
    popt = argparse.ArgumentParser(prog='search.wsgi')
    subopt = popt.add_subparsers(dest='cmd', title='commands')
    
    args = popt.parse_args()

    if not args.cmd:
        popt.print_help()
        return

    args.cmdfunc(args, appinstance)
