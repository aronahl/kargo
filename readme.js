#!/usr/local/bin/node
const http = require('http');
const child_process = require('child_process')
const fs = require('fs');

const server = http.createServer((req,res)=> {
    var url = req.url;
    if (url == "/pandoc.css") {
        let body = [];
        fs.createReadStream(__dirname + '/pandoc.css').on('data', (chunk) => {
            body.push(chunk);
        }).on('end', () => {
            res.statusCode = 200;
            res.setHeader('Content-Type', 'text/css');
            res.end(Buffer.concat(body).toString());
        });
    }
    else if (url == "/") {
        child_process.exec("pandoc -s -f markdown_github -t html5 --css pandoc.css README.md", (error, stdout, stderr) => {
            if (error) {
                res.statusCode = 500;
                res.setHeader('Content-Type', 'text/plain');
                res.end(stderr);
                return;
            }
            res.statusCode = 200;
            res.setHeader('Content-Type', 'text/html');
            res.end(stdout);
        });
    }
    else {
        res.statusCode = 404;
        res.end();
    }
});

server.listen(9191, '127.0.0.1');
