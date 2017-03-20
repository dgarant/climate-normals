var app = angular.module("Normals", ["ui.router"]);

app.config(function($stateProvider, $urlRouterProvider) {
    $stateProvider.state({
        name : "monthly-view",
        url : "/monthly",
        templateUrl : "static/partials/monthly-view.html",
        controller : "MonthlyViewController"
    });

    $urlRouterProvider.otherwise("/monthly")

});


