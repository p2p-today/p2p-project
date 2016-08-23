pip = -m pip install
py_deps = $(pip) cryptography
py_test_deps = $(pip) pytest-coverage
docs_deps = $(pip) sphinx sphinxcontrib-napoleon
ifeq ($(shell python -c 'import sys; print(int(hasattr(sys, "real_prefix")))'), 0) # check for virtualenv
	py_deps += --user
	py_test_deps += --user
	docs_deps += --user
endif

python: LICENSE setup.py
	python $(py_deps); python setup.py build --universal

python3: LICENSE setup.py
	python3 $(py_deps); python3 setup.py build --universal

python2: LICENSE setup.py
	python2 $(py_deps); python2 setup.py build --universal

cpython: LICENSE setup.py
	python $(py_deps); python setup.py build

cpython3: LICENSE setup.py
	python3 $(py_deps); python3 setup.py build

cpython2: LICENSE setup.py
	python2 $(py_deps); python2 setup.py build

pytest: LICENSE setup.py setup.cfg
	make python; python $(py_test_deps); python -m pytest -c ./setup.cfg build/li*

py2test: LICENSE setup.py setup.cfg
	make python2; python2 $(py_test_deps);  python2 -m pytest -c ./setup.cfg build/li*

py3test: LICENSE setup.py setup.cfg
	make python3; python3 $(py_test_deps);  python3 -m pytest -c ./setup.cfg build/li*

cpytest: LICENSE setup.py setup.cfg
	make cpython; python $(py_test_deps);  python -m pytest -c ./setup.cfg build/lib.*

cpy2test: LICENSE setup.py setup.cfg
	make cpython2; python2 $(py_test_deps);  python2 -m pytest -c ./setup.cfg build/lib.*2*

cpy3test: LICENSE setup.py setup.cfg
	make cpython3; python3 $(py_test_deps);  python3 -m pytest -c ./setup.cfg build/lib.*3*

html:
	cd ./docs; rm -r .build; make html

py_all: LICENSE setup.py setup.cfg
	make python; make cpython3; make cpython2; python $(docs_deps); make html