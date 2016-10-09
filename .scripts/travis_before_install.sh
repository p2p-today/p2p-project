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
fi