.PHONY: all install tests dist clean backup deinstall check tags format
.SUFFIXES: .ps .pdf .py

MOD= beammech
SRCS:= ${MOD}.py

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
	@echo '* format: format the source with yapf.'

PYSITE!=python3 -B -c 'import site; print(site.getsitepackages()[0])'

install: setup.py ${MOD}.py
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to install the module!"; \
		exit 1; \
	fi
# Let Python do the install work.
	python3 -B setup.py install
	rm -rf build

uninstall::
	@if [ `id -u` != 0 ]; then \
		echo "You must be root to uninstall the program!"; \
		exit 1; \
	fi
	rm -f ${PYSITE}/${MOD}.py

# Create distribution file. Use zip format to make deployment easier on windoze.
dist:
	python3 -B setup.py sdist --format=zip
	rm -f MANIFEST

clean::
	rm -rf dist build backup-*.tar* MANIFEST
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

# The targets below are mostly for the maintainer.
check:: .IGNORE
	pylama -i E501,W605 ${MOD}.py tests/*.py

tags::
	exctags -R --verbose

format::
	yapf-3.7 -i ${MOD}.py tests/*.py

test::
	pytest-3.7 -v tests
