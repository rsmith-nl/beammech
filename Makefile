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

PYSITE!=python -c 'import site; print site.getsitepackages()[0]'

tests::
	@python tests/general.py

install: setup.py ${MOD}.py
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the module!"; \
		exit 1; \
	fi
# Let Python do the install work.
	python setup.py install
	rm -rf build

deinstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to deinstall the program!"; \
		exit 1; \
	fi
	rm -f ${PYSITE}/${MOD}.py

dist:
# Create distribution file. Use zip format to make deployment easier on windoze.
	python setup.py sdist --format=zip
	mv Makefile.org Makefile
	rm -f MANIFEST
#	sed -f tools/replace.sed port/Makefile.in >port/Makefile
#	cd dist ; sha256 py-stl-* >../port/distinfo
#	cd dist ; ls -l py-stl-* | awk '{printf "SIZE (%s) = %d\n", $$9, $$5};' >>../port/distinfo

clean::
	rm -rf dist build backup-*.tar.gz *.py[co] MANIFEST tests/*.d
#	rm -f port/Makefile port/distinfo

check: ${MOD}.py .IGNORE
	pylint --rcfile=tools/pylintrc ${SRCS}
