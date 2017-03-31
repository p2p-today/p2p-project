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

const js2p = require('./js2p.js');
const equal = require('equal');

m.cli_seed = function(addr, port, transport, out_addr, verbosity) {
    console.log(addr, port, transport, out_addr, verbosity);
};

const argv = require('yargs')
    .usage('Usage: js2p <command> [options]')
    .option('v', {describe: 'the verbosity level you would like'})
    .count('v')
    .command('seed <addr> <port> [transport] [outward_address] [outward_port]',
             'Seed the bootstrap network for a given transport method',
             ()=>{},
             (yargv)=>{
                let transport = yargv.transport || 'Plaintext';
                let out_addr = undefined;
                if (yargv.outward_port !== undefined)   {
                    out_addr = [outward_address, outward_port];
                }
                else if (yargv.outward_address !== undefined)   {
                    out_addr = [outward_address, port];
                }
                m.cli_seed(yargv.addr, yargv.port, transport, out_addr, yargv.v);
    })
    .example('js2p seed 0.0.0.0 44566 SSL -vvvvv')
    .example('js2p seed 0.0.0.0 44565 Plaintext euclid.nmu.edu')
    .command('repl',
             'Opens an interactive interface',
             ()=>{},
             (yargv)=>{
                require('./ctl.js');
             })
    .help('h')
    .alias('h', 'help')
    .argv;
