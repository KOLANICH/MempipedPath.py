MempipedPath.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
===============
[![GitLab Build Status](https://gitlab.com/KOLANICH/MempipedPath.py/badges/master/pipeline.svg)](https://gitlab.com/KOLANICH/MempipedPath.py/pipelines/master/latest)
![GitLab Coverage](https://gitlab.com/KOLANICH/MempipedPath.py/badges/master/coverage.svg)
[![Coveralls Coverage](https://img.shields.io/coveralls/KOLANICH/MempipedPath.py.svg)](https://coveralls.io/r/KOLANICH/MempipedPath.py)
[![Libraries.io Status](https://img.shields.io/librariesio/github/KOLANICH/MempipedPath.py.svg)](https://libraries.io/github/KOLANICH/MempipedPath.py)

Just a helper library allowing you to interact with CLI tools and libs requiring files to be on disk rather in standard pipes.

Requirements
------------
* [`Python >=3.4`](https://www.python.org/downloads/). [`Python 2` is dead, stop raping its corpse.](https://python3statement.org/) Use `2to3` with manual postprocessing to migrate incompatible code to `3`. It shouldn't take so much time. For unit-testing you need Python 3.6+ or PyPy3 because their `dict` is ordered and deterministic.
