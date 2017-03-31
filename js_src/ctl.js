const cli = require('./cli.js');
const vorpal = require('vorpal')();

vorpal
    .command('seed <addr> <port> [transport] [out_addr] [out_port]', 'Seeds the network')
    .action(function(args, repl)    {
        let out_addr = undefined;
        if (args.out_port !== undefined)   {
            out_addr = [args.out_addr, parseInt(args.out_port)];
        }
        else if (args.out_addr !== undefined)   {
            out_addr = [args.out_addr, parseInt(args.port)];
        }
        cli.cli_seed(
            args.addr,
            parseInt(args.port),
            args.transport || 'Plaintext',
            out_addr,
            0
        );
        repl();
    });

vorpal
  .delimiter('[js2p]#')
  .show();
