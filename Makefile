.PHONY: all install dist clean backup deinstall check
.SUFFIXES: .ps .pdf .py

#beginskip
MOD = beammech
SRCS = ${MOD}.py

all: .git/hooks/post-commit setup.py ${MOD}.py
#endskip
PYSITE!=python -c 'import site; print site.getsitepackages()[0]'

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

#beginskip
dist:
# Make simplified makefile.
	mv Makefile Makefile.org
	awk -f tools/makemakefile.awk Makefile.org >Makefile
# Create distribution file. Use zip format to make deployment easier on windoze.
	python setup.py sdist --format=zip
	mv Makefile.org Makefile
	rm -f MANIFEST
#	sed -f tools/replace.sed port/Makefile.in >port/Makefile
#	cd dist ; sha256 py-stl-* >../port/distinfo
#	cd dist ; ls -l py-stl-* | awk '{printf "SIZE (%s) = %d\n", $$9, $$5};' >>../port/distinfo

clean::
	rm -rf dist build backup-*.tar.gz *.py[co] ${MOD}.py setup.py MANIFEST tests/*.d
#	rm -f port/Makefile port/distinfo

backup:
# Generate a full backup.
	sh tools/genbackup

check: ${MOD}.py .IGNORE
	pylint --rcfile=tools/pylintrc ${SRCS}

.git/hooks/post-commit: tools/post-commit
	install -m 755 $> $@

tools/replace.sed: .git/index
	tools/post-commit

setup.py: setup.in.py tools/replace.sed
	sed -f tools/replace.sed setup.in.py >$@

${MOD}.py: ${MOD}.in.py tools/replace.sed
	sed -f tools/replace.sed ${MOD}.in.py >$@
#endskip
