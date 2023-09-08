.. tacl-extra documentation master file, created by
   sphinx-quickstart on Tue Dec  4 09:51:03 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to tacl-extra's documentation!
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   int-all
   jitc
   lifetime
   paternity
   sole-exception


tacl-extra provides scripts and libraries that make use of the `TACL`_
software.

Scripts provided are:

* **int-all**: Generates extended and reduced intersect results files
  for every pair of texts in a supplied corpus.
* **jitc**: Generates an HTML report showing the amount of overlap
  between a set of works, ignoring those parts that overlap with
  works in a second set of works.
* **lifetime**: Generates results data and a report showing the
  lifetime of n-grams that come into or fall out of use in a group of
  corpora.
* **paternity**: Generates a series of results files giving the
  n-grams in common between one corpus and each work in a second
  corpus, that are not present in a third corpus.
* **sole-exception**: Generates a series of reports giving data on
  works based on n-grams that exist only in a one of multiple
  benchmark corpora and unclassified works. Not to be confused with
  the sole-exceptions script below.
* **sole-exceptions**: Generates results files for each work in a
  corpus giving n-grams existing only in that work and a benchmark
  corpus. Not to be confused with the sole-exception script above.

The actual work of the scripts is done in library code that can be
imported and used by other code.


.. _TACL: https://github.com/ajenhl/tacl/
