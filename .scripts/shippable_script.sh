set -e;
if [ $pyver ]; then
    pip install codecov
    pip install -r requirements.txt
    make cpython pytestdeps
    py.test -vv --cov=./py_src/ ./py_src/
    python setup.py sdist --universal && pip install --no-index --find-links=./dist/ py2p
    mv .coverage .covvv
    make cpytest cov=true
    mv .covvv .coverage.1
    mv .coverage .coverage.2
    coverage combine
    coverage xml
    codecov --token=d89f9bd9-27a3-4560-8dbb-39ee3ba020a5 --file=coverage.xml
elif [ $jsver ]; then
    sudo apt-get install build-essential libssl-dev
    wget -qO- https://raw.githubusercontent.com/creationix/nvm/v0.32.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" # This loads nvm
    command -v nvm
    nvm install $jsver
    nvm use $jsver
    node --version
    export CODECOV_TOKEN=":d89f9bd9-27a3-4560-8dbb-39ee3ba020a5"
    make js_codecov
fi
