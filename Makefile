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

PYSITE!=python3 -B -c 'import site; print(site.getsitepackages()[0])'

install: setup.py ${MOD}.py
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the module!"; \
		exit 1; \
	fi
# Let Python do the install work.
	python3 -B setup.py install
	rm -rf build

deinstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to deinstall the program!"; \
		exit 1; \
	fi
	rm -f ${PYSITE}/${MOD}.py

dist:
# Create distribution file. Use zip format to make deployment easier on windoze.
	python3 -B setup.py sdist --format=zip
	rm -f MANIFEST

clean::
	rm -rf dist build backup-*.tar.gz *.py[co] MANIFEST tests/*.d

tests::
	py.test-3.5 -v tests
