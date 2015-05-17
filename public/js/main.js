var research27 = angular.module('research27', []);

research27.controller('indexController', function($scope){

    var socket = io("http://localhost:8000/");

    $scope.currentView = "scan";

    $scope.results = [];

    $scope.sendCommand = function(cmd){
        socket.emit('spawn', cmd);
    }

    $scope.scan = function(){
        $scope.sendCommand('')
    }

    socket.on('stdout', function(stdout){
        $scope.results.push(stdout);
    })
});
