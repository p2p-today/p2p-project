#Python setup section

pip = -m pip install
py_deps = $(pip) cryptography
py_test_deps = $(pip) pytest-coverage
docs_deps = $(pip) sphinx sphinxcontrib-napoleon

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

pylibdir = $(shell python -c "import sys, sysconfig; print('{}.{}-{v[0]}.{v[1]}'.format('lib', sysconfig.get_platform(), v=sys.version_info))")
py2libdir = $(shell $(python2) -c "import sys, sysconfig; print('{}.{}-{v[0]}.{v[1]}'.format('lib', sysconfig.get_platform(), v=sys.version_info))")
py3libdir = $(shell $(python3) -c "import sys, sysconfig; print('{}.{}-{v[0]}.{v[1]}'.format('lib', sysconfig.get_platform(), v=sys.version_info))")
ifeq ($(python2), python2)
	pyunvlibdir = $(pylibdir)
else
	pyunvlibdir = lib
endif

#End python setup section

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

cpython: LICENSE setup.py
	python $(py_deps)
ifeq ($(pypy), True)
	@echo "Building python, rather than cpython, because this is unsupported on pypy"
	python setup.py build --universal
else
	python setup.py build
endif

cpython3: LICENSE setup.py
	$(python3) $(py_deps)
	$(python3) setup.py build

cpython2: LICENSE setup.py
	$(python2) $(py_deps)
	$(python2) setup.py build

pytest: LICENSE setup.py setup.cfg
	$(MAKE) python
	python $(py_test_deps)
	python -m pytest -c ./setup.cfg build/$(pyunvlibdir)

py2test: LICENSE setup.py setup.cfg
	$(MAKE) python2
	$(python2) $(py_test_deps)
	$(python2) -m pytest -c ./setup.cfg build/$(pyunvlibdir)

py3test: LICENSE setup.py setup.cfg
	$(MAKE) python3
	$(python3) $(py_test_deps)
	$(python3) -m pytest -c ./setup.cfg build/$(pyunvlibdir)

cpytest: LICENSE setup.py setup.cfg
	$(MAKE) cpython
	python $(py_test_deps)
	python -m pytest -c ./setup.cfg --cov=build/$(pylibdir) build/$(pylibdir)

cpy2test: LICENSE setup.py setup.cfg
	$(MAKE) cpython2
	$(python2) $(py_test_deps)
	$(python2) -m pytest -c ./setup.cfg --cov=build/$(py2libdir) build/$(py2libdir)

cpy3test: LICENSE setup.py setup.cfg
	$(MAKE) cpython3
	$(python3) $(py_test_deps)
	$(python3) -m pytest -c ./setup.cfg --cov=build/$(py3libdir) build/$(py3libdir)

html:
	python $(docs_deps)
	cd docs; rm -r .build; $(MAKE) html

py_all: LICENSE setup.py setup.cfg
	$(MAKE) python
	$(MAKE) html
	$(MAKE) cpython2
	$(MAKE) cpython3
	$(MAKE) pypy