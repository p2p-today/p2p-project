Use In a Browser
~~~~~~~~~~~~~~~~

How To
======

In each release, a set of browser scripts (regular and minified) are included. To use the library, two scripts must be included in your page. All others are optional (excepting internal dependencies, such as :js:class:`js2p.sync.sync_socket` relying on :js:class:`js2p.mesh.mesh_socket`).

Your header will look something like:

.. code-block:: html

    <head>
        <script type="text/javascript" src="./build/browser-min/js2p-browser-base.min.js"></script>
        <script type="text/javascript" src="./build/browser-min/js2p-browser.min.js"></script>
    </head>

The two scripts shown are the only required. The module will automatically try/catch any other components.

Including these scripts maps the library to the variable ``js2p``, rather than making you :js:func:`require` it. Each component is then mapped to a secition of ``js2p``. So in this example, :js:data:`js2p.base` would be the only included component.

Caveats
=======

1. Browser nodes cannot receive connections. This is due to browser policy, not the library. This means that at some point you *must* connect to a server node

#. Because of the above, a good practice is to provide your ``addr`` and ``port`` as ``null``

#. Browser nodes may *only* be used with the Websocket transport layer. This means that you *must* specify a custom protcol, where the second argument is ``'ws'``.
