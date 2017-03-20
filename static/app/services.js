var app = angular.module("Normals");

app.factory("HttpErrorHandler", function() {
    return {
        clearError : function(scope) {
            scope.hasError = false;
            scope.errorMessage = null;
        },
        handleError : function(scope, errResp) {
            scope.hasError = true;
            if(errResp.data != undefined && errResp.data.message != undefined) {
                scope.errorMessage = errResp.data.message;
            } else {
                scope.errorMessage = "An unexpected error occurred";
            }
        }
    }
});

app.factory("StatService", ["$http", function($http) {
   return {
        list : function(stationId) {
            return $http.get("normals/" + stationId);
        }
    }
}]);

app.factory("StationService", ["$http", function($http) {
    return {
        list : function() {
            return $http.get("stations")
        }
    }
}]);

