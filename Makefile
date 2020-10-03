
# vim:fileencoding=utf-8:fdm=marker:ft=make
.PHONY: all install uninstall clean check tags format test
.SUFFIXES:

MOD:= beammech
SRCS:= ${MOD}.py

# Python settings.
PY:= python3
PKGPATH!=${PY} -c "import site; print(site.getsitepackages()[0])"
USRPATH!=${PY} -c "import site; print(site.getusersitepackages())"
# Program settings
CHECK:= env PYTHONWARNINGS=ignore::FutureWarning pylama -i E501,W605
TAGS:= uctags -R -V
FMT:= yapf -i
TEST:= pytest -v

# Default target.
all::
	@echo 'you can use the following commands:'
	@echo '* test: run the built-in tests.'
	@echo '* install: install system-wide.'
	@echo '* uninstall: remove system install.'
	@echo '* install-user: install for current user.'
	@echo '* uninstall-user: remove install for current user.'
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


install-user::
	${PY} -B setup.py install --user
	rm -rf build dist *.egg-info

uninstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to uninstall the software!"; \
		exit 1; \
	fi
	rm -f ${PKGPATH}/${MOD}.py ${PKGPATH}/${MOD}.egg* ${PKGPATH}/${MOD}*.egg-info

uninstall-user::
	rm -f ${USRPATH}/${MOD}.py ${USRPATH}/${MOD}.egg* ${USRPATH}/${MOD}*.egg-info

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
	${TEST} tests
