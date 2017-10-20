#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""grash -- a KISS static site generator built upon pandoc and jinja2

Takes a directory with jinja2 templates as <srcpath> (defaults to ./templates)
and renders the HTML pages to the <outpath> (defaults to ./build).

Usage:
  grash build [--src=<srcpath> --out=<outpath> --static=<a,b,c>]
  grash watch [--src=<srcpath> --out=<outpath> --static=<a,b,c>]
  grash (-h | --help)
  grash --version

Options:
  --version        Show version.
  -h --help        Show this screen.
  --static=<a,b,c> Accepts a comma-separated list of static directories
  --out=<outpath>  Render the HTML pages to the <outpath> directory.
  --src=<srcpath>  Render jinja2 templates from <srcpath> directory.

"""
import os
import sys

import grash
from grash.config import Settings

from docopt import docopt


def render(args):
    """
    Render a site.

    Args:

        args (:obj:`dict`):

            A map from command-line options to their values.
            For example:

            {
                '--help': False,
                '--static': None,
                '--version': False,
                '--out': None,
                '--src': None,
                'build': True,
                'watch': False
            }
    """
    settings = Settings()

    if args['--src'] is None:
        srcpath = settings.templatePath
    elif os.path.isabs(args['--src']):
        srcpath = args['--src']
    else:
        srcpath = os.path.join(os.getcwd(), args['--src'])

    if not os.path.isdir(srcpath):
        print("The template directory '{}' is invalid."
              .format(srcpath))
        sys.exit(1)

    if args['--out'] is not None:
        outpath = args['--out']
    else:
        outpath = settings.buildDir

    if not os.path.isdir(outpath):
        print("The output directory '{}' is invalid."
              .format(outpath))
        sys.exit(1)

    staticdirs = args['--static']
    staticpaths = None

    if staticdirs:
        staticpaths = staticdirs.split(",")
        for path in staticpaths:
            path = os.path.join(srcpath, path)
            if not os.path.isdir(path):
                print("The static files directory '{}' is invalid."
                      .format(path))
                sys.exit(1)

    site = grash.make(
        templatePath=srcpath,
        buildDir=outpath,
        staticDirs=staticpaths
    )

    reloader = args['watch']

    site.render(reloader=reloader)


def main():
    render(docopt(__doc__, version='grash 0.0.1'))


if __name__ == '__main__':
    main()
