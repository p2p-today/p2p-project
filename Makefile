#Python setup section

pip = -m pip install
py_deps = $(pip) cryptography
py_test_deps = $(pip) pytest-coverage
docs_deps = $(pip) sphinx sphinxcontrib-napoleon sphinx_rtd_theme

ifeq ($(shell python -c 'import sys; print(int(hasattr(sys, "real_prefix")))'), 0) # check for virtualenv
	py_deps += --user
	py_test_deps += --user
	docs_deps += --user
endif

ifeq ($(shell python -c 'import sys; print((sys.version_info[0]))'), 3)
	python2 = python2
	python3 = python
else
	python2 = python
	python3 = python3
endif

ifeq ($(shell python -c "import sys; print(hasattr(sys, 'pypy_version_info'))"), True)
	pypy = True
	ifeq ($(python2), python)
		python2 = python2
	endif
else
	pypy = False
endif

pylibdir = $(shell python -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
py2libdir = $(shell $(python2) -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
py3libdir = $(shell $(python3) -c "import sys, sysconfig; print('lib.{}-{v[0]}.{v[1]}'.format(sysconfig.get_platform(), v=sys.version_info))")
ifeq ($(python2), python)
	pyunvlibdir = $(pylibdir)
else
	pyunvlibdir = lib
endif

#End python setup section

jsdeps: LICENSE
	yarn || npm install

ES5: LICENSE jsdeps
	node node_modules/babel-cli/bin/babel.js --presets es2015 js_src -d build/es5

browser: LICENSE jsdeps
	npm install browserify
	node node_modules/browserify/bin/cmd.js -e . -o ./build/js2p-browser.js -s js2p

browser-compat: browser
	node node_modules/babel-cli/bin/babel.js --presets es2015 ./build/js2p-browser.js -o ./build/js2p-browser.es5.js

browser-compat-min: browser
	node node_modules/babel-cli/bin/babel.js --presets es2015 ./build/js2p-browser.js -o ./build/js2p-browser.min.es5.js --minified --no-comments

browser-min: browser
	node node_modules/babel-cli/bin/babel.js ./build/js2p-browser.js -o ./build/js2p-browser.min.js --minified --no-comments

jsdocs:
	node js_src/docs_test.js

jstest: LICENSE jsdeps
	node node_modules/mocha/bin/mocha js_src/test/*

ES5test: LICENSE ES5
	node node_modules/mocha/bin/mocha build/es5/test/*

python: LICENSE setup.py
	python $(py_deps)
	python setup.py build --universal

python3: LICENSE setup.py
	$(python3) $(py_deps)
	$(python3) setup.py build --universal

python2: LICENSE setup.py
	$(python2) $(py_deps)
	$(python2) setup.py build --universal

pypy: LICENSE setup.py
	pypy $(py_deps)
	pypy setup.py build --universal

ifeq ($(pypy), True)
cpython: python

else
cpython: LICENSE setup.py
	python $(py_deps)
ifeq ($(debug), true)
	python setup.py build --debug
else
	python setup.py build
endif
endif

cpython3: LICENSE setup.py
	$(python3) $(py_deps)
ifeq ($(debug), true)
	$(python3) setup.py build --debug
else
	$(python3) setup.py build
endif

cpython2: LICENSE setup.py
	$(python2) $(py_deps)
ifeq ($(debug), true)
	$(python2) setup.py build --debug
else
	$(python2) setup.py build
endif

pytestdeps:
	python $(py_test_deps)

py2testdeps:
	$(python2) $(py_test_deps)

py3testdeps:
	$(python3) $(py_test_deps)

pytest: LICENSE setup.py setup.cfg python pytestdeps
ifeq ($(cov), true)
	python -m pytest -c ./setup.cfg --cov=build/$(pyunvlibdir) build/$(pyunvlibdir)
else
	python -m pytest -c ./setup.cfg build/$(pyunvlibdir)
endif

py2test: LICENSE setup.py setup.cfg python2 py2testdeps
ifeq ($(cov), true)
	$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

py3test: LICENSE setup.py setup.cfg python3 py3testdeps
	@echo $(py3libdir)
ifeq ($(cov), true)
	$(python3) -m pytest -c ./setup.cfg --cov=build/lib build/lib
else
	$(python3) -m pytest -c ./setup.cfg build/lib
endif

ifeq ($(pypy), True)
cpytest: pytest

else
cpytest: LICENSE setup.py setup.cfg cpython pytestdeps
ifeq ($(cov), true)
	python -m pytest -c ./setup.cfg --cov=build/$(pylibdir) build/$(pylibdir)
else
	python -m pytest -c ./setup.cfg build/$(pylibdir)
endif
endif

cpy2test: LICENSE setup.py setup.cfg cpython2 py2testdeps
ifeq ($(cov), true)
	$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)
else
	$(python2) -m pytest -c ./setup.cfg build/$(py2libdir)
endif

cpy3test: LICENSE setup.py setup.cfg cpython3 py3testdeps
ifeq ($(cov), true)
	$(python3) -m pytest -c ./setup.cfg --cov=build/$(py3libdir) build/$(py3libdir)
else
	$(python3) -m pytest -c ./setup.cfg build/$(py3libdir)
endif

html: jsdocs
	python $(docs_deps)
	cd docs; rm -r .build; $(MAKE) html

py_all: LICENSE setup.py setup.cfg python html cpython2 cpython3 pypy

js_all: LICENSE ES5 html browser browser-min browser-compat browser-compat-min

test_all: LICENSE jstest ES5test pytest cpy2test cpy3test
