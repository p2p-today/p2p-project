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
    .command('list seeds', 'List the nodes that you currently have seeding the network')
    .action(function(args, repl)    {
        Object.keys(cli.seed_nodes).forEach((transport)=>{
            let node = cli.seed_nodes[transport];
            let formatted_transport = `${transport}:${' '.repeat(10 - transport.length)}`;
            console.log(`${formatted_transport}${node.out_addr[0]}:${node.out_addr[1]} (${node.id})`);
            console.log(`\t\tseeding ${node.routing_table.size} nodes`);
            console.log(`\t\tseeding ${node.__keys.size} networks`);
        });
        repl();
    });

vorpal
    .command('stop seeding [transport]', 'Halts seeding a specific transport method if given, all if not')
    .action(function(args, repl)    {
        if (args.transport) {
            // cli.seed_nodes[args.transport].close();
            delete cli.seed_nodes[args.transport];
        }
        else    {
            Object.keys(cli.seed_nodes).forEach((transport)=>{
                // cli.seed_nodes[transport].close();
                delete cli.seed_nodes[transport];
            });
        }
        repl();
    })

vorpal
  .delimiter('[js2p]#')
  .show();
