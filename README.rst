tacl-extra
==========

tacl-extra provides scripts and libraries that make use of the `TACL`_
software.

Scripts provided are:

* int-all: Generates extended and reduced intersect results files for
  every pair of texts in a supplied corpus.
* lifetime: Generates results data and a report showing the lifetime
  of n-grams that come into or fall out of use in a group of corpora.
* paternity: Generates a series of results files giving the n-grams in
  common between one corpus and each work in a second corpus, that are
  not present in a third corpus.

The actual work of the scripts is done in library code that can be
imported and used by other code.


.. _TACL: https://github.com/ajenhl/tacl/
