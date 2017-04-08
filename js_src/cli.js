if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.m = {};
    m = root;
}

const equal = require('equal');

m.seed_nodes = {}

m.cli_seed = function(addr, port, transport, out_addr, verbosity) {
    const js2p = require('./js2p.js');
    m.seed_nodes[transport] = js2p.bootstrap(
        js2p.chord.ChordSocket,
        new js2p.base.Protocol('bootstrap', transport),
        addr,
        port,
        out_addr,
        verbosity
    );
    m.seed_nodes[transport].join();
};

const argv = require('yargs')
    .usage('Usage: js2p <command> [options]')
    .option('v', {describe: 'the verbosity level you would like'})
    .count('v')
    .command('repl',
             'Opens an interactive interface',
             ()=>{},
             (yargv)=>{
                require('./ctl.js');
             })
    .command('seed <addr> <port> [transport] [outward_address] [outward_port]',
             'Seed the bootstrap network for a given transport method',
             ()=>{},
             (yargv)=>{
                let transport = yargv.transport || 'Plaintext';
                let out_addr = undefined;
                if (yargv.outward_port !== undefined)   {
                    out_addr = [yargv.outward_address, parseInt(yargv.outward_port)];
                }
                else if (yargv.outward_address !== undefined)   {
                    out_addr = [yargv.outward_address, parseInt(yargv.port)];
                }
                m.cli_seed(yargv.addr, parseInt(yargv.port), transport, out_addr, yargv.v);
    })
    .example('js2p seed 0.0.0.0 44566 SSL -vvvvv')
    .example('js2p seed 0.0.0.0 44565 Plaintext euclid.nmu.edu')
    .help('h')
    .alias('h', 'help')
    .demandCommand(1, 'Please enter a single command')
    .argv;
