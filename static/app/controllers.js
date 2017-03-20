var app = angular.module("Normals");

app.controller("MonthlyViewController", [
    "$scope", "HttpErrorHandler", "StationService", "StatService",
function($scope, HttpErrorHandler, StationService, StatService) {
    var curMonth = moment().month() + 1;
    $scope.monthDays = _.range(1, moment().daysInMonth()+1);

    StationService.list().then(function(data) {
        HttpErrorHandler.clearError($scope);
        $scope.stations = data.data;
        StatService.list($scope.stations[0].station_id).then(function(data2) {
            $scope.normals = data2.data;
            $scope.dayIndexedNormals = _.indexBy(_.filter(data2.data, function(d) { return(d.month == curMonth) }), "day");
        }, function(errResp) {
            HttpErrorHandler.handleError($scope, errResp);
        });
    }, function(errResp) {
        HttpErrorHandler.handleError($scope, errResp);
    });
}]);


