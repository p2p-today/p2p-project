Use In a Browser
~~~~~~~~~~~~~~~~

In each release, a set of browser scripts (regular and minified) are included. To use the library, two scripts must be included in your page. All others are optional (excepting internal dependencies, such as :js:class:`js2p.sync.sync_socket` relying on :js:class:`js2p.mesh.mesh_socket`).

Your page will look something like:

.. code-block:: html

    <head>
        <script type="text/javascript" src="./build/browser-min/js2p-browser-0.6.676-base.min.js"></script>
        <!-- Other js2p loaders here -->
        <script type="text/javascript" src="./build/browser-min/js2p-browser-0.6.676.min.js"></script>
    </head>

The two scripts shown are the only required. The library will automatically load any other provided components.

Including these scripts maps the library to the global object ``js2p``. Each component is then mapped to a section of ``js2p``. So in this example, :js:data:`js2p.base` would be the only included component.

Caveats
=======

1. Browsers cannot receive incoming connections. This means that at some point you **must** connect to a server node. To avoid confusion, a good practice is to provide your ``addr`` and ``port`` as ``null``.

#. Browser nodes may **only** be used with the WebSocket transport layer. This means that you **must** specify a custom :js:class:`js2p.base.Protocol`, where the second argument is ``'ws'``.

#. Scripts **must** be included in the correct load order. This means that dependencies come first. As of this document's last update, the preferred order is:

    1. ``js2p-browser-base.js`` (required)
    #. ``js2p-browser-mesh.js``
    #. ``js2p-browser-sync.js`` and/or ``js2p-browser-chord.js``
    #. ``js2p-browser.js`` (required)

Example
=======

This example shows the simple construction of a :js:class:`js2p.sync.sync_socket`. Note the order of script inclusion.

.. code-block:: html

    <!doctype html>
    <html>
        <head>
            <script type="text/javascript" src="./build/browser/js2p-browser-0.6.676-base.js"></script>
            <script type="text/javascript" src="./build/browser/js2p-browser-0.6.676-mesh.js"></script>
            <script type="text/javascript" src="./build/browser/js2p-browser-0.6.676-sync.js"></script>
            <script type="text/javascript" src="./build/browser/js2p-browser-0.6.676.js"></script>
        </head>
        <body>
            <script type="text/javascript">
                const socket = new js2p.sync.sync_socket(null, null, true, new js2p.base.Protocol('chat', 'ws'));
                socket.on('connect', (conn)=>{
                    // whatever actions to perform on connection
                });
                socket.connect('example.com', 5555);
                // The rest of your script
            </script>
        </body>
    </html>
