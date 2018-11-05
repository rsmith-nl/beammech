.PHONY: all install tests dist clean backup deinstall check tags format
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
	@echo '* tags'
	@echo '* format'

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

# Create distribution file. Use zip format to make deployment easier on windoze.
dist:
	python3 -B setup.py sdist --format=zip
	rm -f MANIFEST

clean::
	rm -rf dist build backup-*.tar.gz MANIFEST __pycache__

check::
	pylama -i E501 ${MOD}.py tests/*.py

tags::
	exctags -R

format::
	yapf-3.7 -i ${MOD}.py tests/*.py

tests::
	pytest-3.7 -v tests
