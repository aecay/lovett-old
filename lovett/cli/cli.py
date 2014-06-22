#!/usr/bin/env python

import sys
import logging
import click

# from .. import __version__

from lovett.corpus import (parse_file, _validate_psdx)
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
@click.argument("infile", nargs=1, type=click.File("r"))
@click.argument("outfile", nargs=1, type=click.File("w"))
def format(infile, outfile):
    s = etree.tostring(etree.parse(infile), pretty_print=True, encoding="utf-8")
    outfile.write(s.decode("utf-8"))

# TODO: factor out common file handling code
@cli.command()
# "from" clashes with a python keyword, so assign a different name
@click.option("--from", "-f", "frm", type=click.Choice(["psdx", "deep"]))
@click.option("--to", "-t", type=click.Choice(["psdx", "deep"]))
@click.argument("infile", nargs=1, type=click.File("r"))
@click.argument("outfile", nargs=1, type=click.File("w"))
def convert(frm, to, infile, outfile):
    if frm == "psdx":
        corpus = parse_file(infile)
    else:
        raise NotImplemented("convert from: %s" % frm)
    if to == "deep":
        outfile.write("\n\n".join(map(lambda x: x.to_deep(), corpus.trees())))
    else:
        raise NotImplemented("convert to: %s" % to)
