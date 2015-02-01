.PHONY: all install tests dist clean backup deinstall check
.SUFFIXES: .ps .pdf .py

MOD = beammech
SRCS = ${MOD}.py

all::
	@echo 'you can use the following commands:'
	@echo '* tests'
	@echo '* install'
	@echo '* deinstall'
	@echo '* dist'
	@echo '* clean'
	@echo '* check'

PYSITE!=python3 -c 'import site; print(site.getsitepackages()[0])'

tests::
	@python3 tests/general.py

install: setup.py ${MOD}.py
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the module!"; \
		exit 1; \
	fi
# Let Python do the install work.
	python3 setup.py install
	rm -rf build

deinstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to deinstall the program!"; \
		exit 1; \
	fi
	rm -f ${PYSITE}/${MOD}.py

dist:
# Create distribution file. Use zip format to make deployment easier on windoze.
	python3 setup.py sdist --format=zip
	mv Makefile.org Makefile
	rm -f MANIFEST

clean::
	rm -rf dist build backup-*.tar.gz *.py[co] MANIFEST tests/*.d

check: ${MOD}.py .IGNORE
	pylint --rcfile=tools/pylintrc ${SRCS}
