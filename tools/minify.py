#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
minify.py
~~~~~~~~~

This tool removes as much whitespace from an NGINX config file as possible
without breaking it or causing NGINX to act differently.

For example, this NGINX config file:

.. code:: nginx

    events {
    }
    
    http {
        server {
            listen 8080;
            location ~ ^/foo/$ {
                return 200 'bar';
            }
        }
    }

Would be minified to this:

.. code:: nginx

    events{}http{server{listen 8080;location ~ '^/foo/$'{return 200 bar;}}}

"""

import os
import sys

# make amplify libs available
script_location = os.path.abspath(os.path.expanduser(__file__))
agent_repo_path = os.path.dirname(os.path.dirname(script_location))
sys.path.append(agent_repo_path)

from amplify.agent.objects.nginx.config.amplify_parser.lex import lex_file

__author__ = 'Arie van Luttikhuizen'
__copyright__ = 'Copyright (C) Nginx, Inc. All rights reserved.'
__maintainer__ = 'Arie van Luttikhuizen'
__email__ = 'arie@nginx.com'

DELIMITERS = ('{', '}', ';')


def parse_args():
    from argparse import ArgumentParser

    # create parser and parse arguments
    parser = ArgumentParser(description='Minifies an NGINX config file')
    parser.add_argument('filename', help='NGINX config file to minify')
    parser.add_argument('-o', '--out', metavar='file', default=None,
                        help='file to write to (default is stdout)')
    args = parser.parse_args()

    # prepare filename argument
    args.filename = os.path.expanduser(args.filename)
    args.filename = os.path.abspath(args.filename)
    if not os.path.isfile(args.filename):
        parser.error('filename: No such file or directory')

    return args


def _escape(string):
    prev, char = '', ''
    for char in string:
        if prev == '\\' or prev + char == '${':
            prev += char
            yield prev
            continue
        if prev == '$':
            yield prev
        if char not in ('\\', '$'):
            yield char
        prev = char
    if char in ('\\', '$'):
        yield char


def needs_quotes(string):
    if string == '':
        return True
    elif string in DELIMITERS:
        return False

    # lexer should throw an error when variable expansion syntax
    # is messed up, but just wrap it in quotes for now I guess
    chars = _escape(string)

    # arguments can't start with variable expansion syntax
    char = next(chars)
    if char.isspace() or char in ('{', ';', '"', "'", '${'):
        return True

    expanding = False
    for char in chars:
        if char.isspace() or char in ('{', ';', '"', "'"):
            return True
        elif char == ('${' if expanding else '}'):
            return True
        elif char == ('}' if expanding else '${'):
            expanding = not expanding

    return char in ('\\', '$') or expanding


def minify(filename, outfile=None):
    output = sys.stdout if outfile is None else open(outfile, 'w')
    try:
        prev, token = '', ''
        for token, __ in lex_file(filename):
            token = str(token.encode('utf-8'))

            if needs_quotes(token):
                token = repr(token.decode('string_escape'))

            if prev and not (prev in DELIMITERS or token in DELIMITERS):
                token = ' ' + token

            output.write(token)
            output.flush()

            prev = token
    finally:
        if outfile is None:
            print
        else:
            output.close()


def main():
    args = parse_args()
    minify(args.filename, args.out)


if __name__ == '__main__':
    main()
