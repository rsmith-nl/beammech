# file: Makefile
# vim:fileencoding=utf-8:ft=make
#
# NOTE: This Makefile is only intended for developers.
#       It is only meant for UNIX-like operating systems.
#       Most of the commands require extra software.
.POSIX:
.SUFFIXES:
.PHONY: help install install-user uninstall uninstall-user wheel clean tags format test 

MOD:= beammech

# Python program name. Either “python” or “python3”, depending on the system.
PY:= python3
# Determinded by calling python.
PKGPATH!=${PY} -c "import site; print(site.getsitepackages()[0])"
USRPATH!=${PY} -c "import site; print(site.getusersitepackages())"
# Helper program settings
CHECK:= env PYTHONWARNINGS=ignore::FutureWarning pylama -i E501,W605

# Default target.
help::
	@echo "Command  Meaning"
	@echo "-------  -------"
	@sed -n -e '/##/s/:.*\#\#/\t/p' -e '/@sed/d' Makefile

install:: ## install system-wide.
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the software!"; \
		exit 1; \
	fi
# Let Python do the install work.
	${PY} -m pip install dist/*.whl

install-user:: ## install for current user.
	${PY} -m pip install --user dist/*.whl

uninstall:: ## remove system-wide install.
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to uninstall the software!"; \
		exit 1; \
	fi
	${PY} -m pip uninstall ${MOD}

uninstall-user:: ## remove install for current user.
	${PY} -m pip uninstall ${MOD}

wheel:  ## create distribution file in wheel format.
	${PY} -m build -n -w

clean:: ## remove all generated files.
	rm -rf dist build backup-*.tar.gz
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

# The targets below are mostly for the maintainer.
check:: .IGNORE  ## check all python files. (requires pylama)
	${CHECK} src/${MOD} tests/*.py

format:: ## format the source files.
	black src/${MOD} tests/*.py

test:: ## run the test suite. (requires py.test)
	env PYTHONPATH=src/ ${PY} -m pytest
