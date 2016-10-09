if [ $pyver ]; then
    python --version;
    make cpython;
else
    make ES5;
fi