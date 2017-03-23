var app = angular.module("Normals", ["ui.router"]);

app.config(function($stateProvider, $urlRouterProvider) {
    $stateProvider.state({
        name : "daily-view",
        url : "/daily",
        templateUrl : "static/partials/daily-view.html",
        controller : "DailyViewController"
    });

    $urlRouterProvider.otherwise("/daily")

});


