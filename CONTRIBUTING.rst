Contributing
============

Issues
~~~~~~

You may submit an issue via `this link`_ if you have a GitHub account,
or `this one`_ if you do not.

Issues should have a description of the problem, as well as all of the
following, if possible

#. A log from this time
#. The output from ``node.status``

Big Fixes
~~~~~~~~~

Bug fixes should be submitted as a pull request. If you are submitting a
bug fix, please title it as such, and provide a description of the bug
you’re fixing.

Because I use waffle.io, I appreciate it if the description includes a
list like the following:

-  Connects to #71
-  Connects to #99
-  Connects to #108

This associates the pull request with the related issues.

New Features
~~~~~~~~~~~~

New features should be submitted as a pull request. If you are
submitting a new feature, please title it as such, and provide a
description of it. Any new feature should maintain the current API where
possible, and make explicit when it does not. Your PR will not be merged
until the other implementations can be made to match it, so it helps if
you try to implement it in them as well.

Because I use waffle.io, I appreciate it if the description includes a
list like the following:

-  Connects to #71
-  Connects to #99
-  Connects to #108

This associates the pull request with the related issues.

New Network Schemas
~~~~~~~~~~~~~~~~~~~

If you want to add a new network schema, the following things are
required. These are written for the Python implementation, but it
applies to the others where possible.

#. It must keep the current inheritence structure (ie, “socket”, daemon,
   connection, inheriting from base\_socket, base\_daemon,
   base\_connection)
#. It must use the current packet format (or any changes must be
   propagated to the other schemas)
#. Where possible, it should use the same flags as the current OP-codes
#. Where possible, it should keep a similar API
#. Message handlers should use the ``register_handler`` mechanism

New Language Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you would like to write an implementation in a new language, thank
you! Following these rules will make things much faster to merge, though
exceptions can be made if necessary.

#. The new implementation should be in a folder labelled lang\_src (ex:
   py\_src)
#. Setup scripts should be in the top level folder
#. It must at minimum support the mesh network implementation
#. Where possible, it should maintain the current
   inheritence/architecture scheme
#. Where possible, it should use the same flags as the current OP-codes
#. Where possible, it should keep a similar API
#. Where possible, it should have unit tests
#. Where reasonable, users should be able to register custom callbacks

When this is ready, submit this as a pull request. If you name it as
such, it will take priority over everything but critical bugfixes. After
a review, we will discuss possible changes and plans for future
modifications, and then merge.

.. _this link: https://github.com/gappleto97/p2p-project/issues/new
.. _this one: https://gitreports.com/issue/gappleto97/p2p-project