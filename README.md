# text-fabric

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1008899.svg)](https://doi.org/10.5281/zenodo.592193)
![text-fabric](/docs/images/tf.png)


Text-Fabric is several things:

* a *browser* for ancient text corpora
* a Python3 package for processing ancient corpora

A corpus of ancient texts and linguistic annotations represents a large body of knowledge.
Text-Fabric makes that knowledge accessible to non-programmers by means of 
built-in a search interface that runs in your browser.

From there the step to program your own analytics is not so big anymore.
Because you can call the Text-Fabric API from your Python programs, and
it works really well in Jupyter notebooks.
 
# Install

Text Fabric is a Python(3) package on the Python Package Index, so you can install it easily with `pip` from
the command line. Here are the precise
[installation instructions](https://dans-labs.github.io/text-fabric/).

# Use

Provided you have the data repositories for the Hebrew Bible (bhsa) or the Proto-Cuneiform Uruk corpus (cunei)
in place (see below),
you can open a terminal (command prompt), and just say

```sh
text-fabric bhsa
```

or 

```sh
text-fabric cunei
```

After loading the data your browser will open and load the search interface.
There you'll find links to further help.

<p>
<img src="/docs/images/bhsa-app.png"/>
</p>

<p>
<img src="/docs/images/cunei-app.png"/>
</p>

# Documentation

There is extensive documentation.
If you start using the Text-Fabric API in your programs, you'll need it.

Jump off to the [docs](https://dans-labs.github.io/text-fabric/)

# Data

In order to work with Text-Fabric, you need a dataset to operate on,
such as the
[Biblia Hebraica Stuttgartensia Amstelodamensis](https://github/etcbc/bhsa)
or the
[Proto-Cuneiform tablets from Uruk IV/III](https://github/nino-cunei/uruk)


<a target="_blank" href="https://archive.softwareheritage.org/browse/origin/https://github.com/Dans-labs/text-fabric/directory/"><img src="/docs/images/swh-logo-archive.png" width="100" align="left"/></a>

**This repository is being archived continuously by the 
[Software Heritage Archive](https://archive.softwareheritage.org).
If you want to cite snippets of the code of this repository, the Software Archive
offers an easy and elegant way to do so.
As an example, here I quote the 
[*stitching* algorithm](https://archive.softwareheritage.org/swh:1:cnt:6169c074089ddc8a0e048cb67e1fec57857ef54d;lines=3224-3270/),
by means of which Text-Fabric Search collects the solutions of a
[search template](https://dans-labs.github.io/text-fabric/Api/General/#searching).
The quote refers directly to specific lines of code, deeply buried in
a Python file within a particular version of Text-Fabric.**
