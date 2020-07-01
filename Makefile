# file: Makefile
# vim:fileencoding=utf-8:fdm=marker:ft=make
#
# Copyright © 2019 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2012-04-15T20:42:31+02:00
# Last modified: 2020-07-01T22:42:41+0200

.PHONY: all install uninstall clean check tags format test
.SUFFIXES: .ps .pdf .py

MOD= beammech
SRCS:= ${MOD}.py

# Python settings.
PY= python3
PKGPATH!=${PY} -c "import site; print(site.getsitepackages()[0])"
# Program settings
CHECK= env PYTHONWARNINGS=ignore::FutureWarning pylama -i E501,W605
TAGS= exctags -R --verbose
FMT= yapf-3.7 -i
TEST= pytest-3.7 -v

# Default target.
all::
	@echo 'you can use the following commands:'
	@echo '* test: run the built-in tests.'
	@echo '* install'
	@echo '* uninstall'
	@echo '* dist: create a distribution file.'
	@echo '* clean: remove all generated files.'
	@echo '* check: run pylama on all python files.'
	@echo '* tags: run exctags.'
	@echo '* format: format the source with yapf.'

install::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the software!"; \
		exit 1; \
	fi
# Let Python do the install work.
	${PY} -B setup.py install
	rm -rf build dist *.egg-info

uninstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to uninstall the software!"; \
		exit 1; \
	fi
	rm -f ${PKGPATH}/${MOD}.py ${PKGPATH}/${MOD}.egg*

# Create distribution file. Use zip format to make deployment easier on windoze.
dist:
	${PY} -B setup.py sdist --format=zip
	rm -f MANIFEST

clean::
	rm -rf dist build backup-*.tar.gz MANIFEST *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

# The targets below are mostly for the maintainer.
check:: .IGNORE
	${CHECK} ${MOD}.py tests/*.py

tags::
	${TAGS}

format::
	${FMT} ${MOD}.py tests/*.py

test::
	${TEST} --doctest-modules
