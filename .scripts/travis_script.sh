set -e;
if [ $pyver ]; then
    if [ $pyver != pypy ] && [ $pyver != pypy3 ]; then
        git clone https://github.com/MacPython/terryfy;
        source terryfy/travis_tools.sh;
        get_python_environment  $pydist $pyver;
    fi
    if [ $pyver == pypy ] || [ $pyver == pypy3 ]; then
        brew install $pyver; export PYTHON_EXE=$pyver;
        curl $GET_PIP_URL > $DOWNLOADS_SDIR/get-pip.py;
        sudo $PYTHON_EXE $DOWNLOADS_SDIR/get-pip.py --ignore-installed;
        export PIP_CMD="sudo $PYTHON_EXE -m pip";
    fi
    $PIP_CMD install virtualenv;
    virtualenv -p $PYTHON_EXE venv;
    source venv/bin/activate;
    pip install -r requirements.txt
    make cpython;
    pip install pytest-coverage pytest-benchmark codecov wheel
    py.test -vv --cov=./py_src/ ./py_src/
    python setup.py sdist --universal && pip install --no-index --find-links=./dist/ py2p
    python setup.py bdist_wheel
    mv .coverage .covvv
    make cpytest cov=true
    mv .covvv .coverage.1
    mv .coverage .coverage.2
    python -m coverage combine;
    python -m coverage xml;
    codecov --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5 --file=coverage.xml
else
    if [ $jsver == 4 ]; then
        make js_compat_test
    else
        make js_codecov
    fi
fi
