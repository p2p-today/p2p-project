var fs = require('fs');
var path = require('path');

function walk(dir, done) {
    var results = [];
    fs.readdir(dir, function(err, list) {
        if (err) return done(err);
        var pending = list.length;
        if (!pending) return done(null, results);
        list.forEach(function(file) {
            file = path.resolve(dir, file);
            file = path.relative(dir, file);
            fs.stat(file, function(err, stat) {
                if (stat && stat.isDirectory()) {
                    walk(file, function(err, res) {
                        results = results.concat(res);
                        if (!--pending) done(null, results);
                    });
                } else {
                    results.push(file);
                    if (!--pending) done(null, results);
                }
            });
        });
    });
};


function execAll(re, string) {
    var match = null;
    var matches = [];
    // For each match in the string:
    while (match = re.exec(string)) {
        matches.push(match.slice());  // Push a copy of it onto the return array
    }
    return matches;
}

var folder_map = {
    js_src: "javascript",
    jv_src: "java",
    go_src: "go",
    cp_src: "cpp",
    c_src: "c"
};
const find_relevant_comments = /\/\*\*\r?\n(?:(?:(?![\n\r])\s)*\*([^\r\n]*)\r?\n)*\s*\*\//g;  // http://regexr.com/3eb1d
const extract_lines = /(?:(?![\n\r])\s)*\*[ ]?([^\r\n\*\/][^\r\n]*)?\r?\n/g;  // http://regexr.com/3ecnv

function gen_walker(folder) {
    return function done(err, res) {
        if (err) throw err;
        var docs_folder = path.resolve('docs', folder_map[folder]);
        for (var i = 0; i < res.length; i++)  {
            var file = path.resolve('.', folder, res[i]);
            if (fs.lstatSync(file).isDirectory())   {
                continue;
            }
            var ending = res[i].substr(res[i].lastIndexOf(".") && res[i].indexOf("wrapper") < 0);
            if (ending === ".cpp" || ending === ".c")
                continue;
            var file_dest_name = res[i].substr(0, res[i].lastIndexOf(".")) + ".rst";
            var file_dest = path.resolve(docs_folder, file_dest_name);
            var string = fs.readFileSync(file);
            var comments = execAll(find_relevant_comments, string);
            var content = "";
            for (var j = 0; j < comments.length; j++) {
                var lines = execAll(extract_lines, comments[j]);
                for (var h = 0; h < lines.length; h++)  {
                    if (lines[h][1] === undefined)     {
                        content += "\n";
                    }
                    else    {
                        content += lines[h][1] + "\n";
                    }
                }
            }
            content += "\n\n";
            var options = { flag : 'w' };
            fs.writeFile(file_dest, content, options, (err) => {
                if (err && err.code !== 'ENOENT')
                    throw err;
            });
        }
    }
}

walk('js_src', gen_walker('js_src'));
walk('jv_src', gen_walker('jv_src'));
walk('go_src', gen_walker('go_src'));
walk('cp_src', gen_walker('cp_src'));
walk('c_src', gen_walker('c_src'));

// walk(dir, function(err, results) {
//       if (err) throw err;
//       console.log(results);
//     });