if [ $pyver ]; then
    make cpython;
else
    make ES5;
fi