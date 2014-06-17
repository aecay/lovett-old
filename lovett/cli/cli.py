#!/usr/bin/env python

import sys
import logging
import click

# from .. import __version__

from lovett.corpus_xml import (parse_file, _validate_psdx)
from lxml import etree

logging.basicConfig(format="%(message)s", level=logging.INFO)

@click.group()
@click.option("--debug", "-d", is_flag=True)
def cli(debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)

@cli.command()
@click.argument("filename", type=click.Path(exists=True))
def validate(filename):
    logging.info("validating file %s" % filename)
    corpus = parse_file(filename)
    result, msg = _validate_psdx(corpus)
    if result:
        logging.info("valid")
    else:
        logging.info("invalid")
        logging.info("error is: " + str(msg))
        sys.exit(1)

@cli.command()
@click.argument("infile", type=click.Path(exists=True))
@click.argument("outfile", nargs=-1, type=click.Path())
def format(infile, outfile):
    if len(outfile) > 1:
        raise Exception("Please specify one input and one output file.")
    elif len(outfile) == 1:
        outfile = outfile[0]
    else:
        outfile = None
    s = etree.tostring(etree.parse(infile), pretty_print=True, encoding="utf-8")
    if outfile is not None:
        with open(outfile, "wb") as f:
            f.write(s)
    else:
        sys.stdout.write(s.decode("utf-8"))
