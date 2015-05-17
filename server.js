var express = require('express');
var app = express();
var http = require('http').Server(app);
var fs = require('fs');
var io = require('socket.io')(http);
var exec = require('child_process').exec;
var child;

app.use(express.static(process.cwd() + '/public'));

app.get('/', function(req, res){
    res.send(fs.open('public/index.html', 'r').read());
});

io.on('connection', function(socket){
    console.log('Connected');

    socket.on('disconnect', function(){
        console.log('Disconnected');
    });

    socket.on('spawn', function(cmd){
        if(cmd && cmd.length > 0){
            child = exec(cmd);

            child.stdout.on('data', function (data) {
                io.emit('stdout', data)
            });
        }
    });
});

http.listen(8000, function(){
    console.log('Crawler server listening on *:8000');
});
