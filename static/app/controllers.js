var app = angular.module("Normals");

app.controller("DailyViewController", [
    "$scope", "HttpErrorHandler", "StationService", "StatService",
function($scope, HttpErrorHandler, StationService, StatService) {
    var curMonth = moment().month() + 1;
    $scope.monthDays = _.range(1, moment().daysInMonth()+1);
    $scope.statName = "tempf_tavg";


    // convert daily statistics into a set of normal distribution parameters
    function processStats(dayIndexedNormals) {
        var dailyStats = new Object()

        var sdBoundFactor = 3.5;
        _.each(["snow_depth_inches", "tempf_tavg"], function(featureName) {
            var lBound = Number.MAX_VALUE;
            var uBound = Number.MIN_VALUE;
            var zeroTruncated = featureName == "snow_depth_inches" ? true : false;

            _.each(dayIndexedNormals, function(dayStats, day) {
                if(dailyStats[day] == undefined) {
                    dailyStats[day] = new Object();
                }

                if(featureName == "snow_depth_inches") {
                    // approximating the distribution as a normal
                    var dlower = dayStats.snow_depth_inches_50pctl - dayStats.snow_depth_inches_25pctl;
                    var dupper = dayStats.snow_depth_inches_75pctl - dayStats.snow_depth_inches_50pctl;

                    var mean = dayStats.snow_depth_inches_50pctl;
                    // Z score of 0.675 is at 75th percentile for standard normal
                    var stdDev = (dlower + dupper / 2.0) / 0.675;
                    if(stdDev == 0) {
                        stdDev = 0.001;
                    }
                } else {
                    var mean = dayStats[featureName + "_normal"];
                    var stdDev = dayStats[featureName + "_stddev"];
                }

                dailyStats[day][featureName] = {"mean" : mean, "stddev" : stdDev, "zeroTruncated" : zeroTruncated};
                if(mean - sdBoundFactor * stdDev < lBound) {
                    lBound = mean - sdBoundFactor * stdDev;
                }
                if(mean + sdBoundFactor * stdDev > uBound) {
                    uBound = mean + sdBoundFactor * stdDev;
                }
            });

            var dailyMeans = _.map(dailyStats, function(v) { return v[featureName].mean });
            var monthlySum = _.reduce(dailyMeans, function(memo, num) { return memo + num }, 0);
            var monthlyMean = monthlySum / _.values(dailyStats).length;

            _.each(dailyStats, function(dayStats) {
                if(zeroTruncated) {
                    dayStats[featureName].min = Math.max(0, lBound);
                    dayStats[featureName].max = Math.max(0, uBound);
                } else {
                    dayStats[featureName].min = lBound;
                    dayStats[featureName].max = uBound;
                }
                dayStats[featureName].longTermMean = monthlyMean;
            });
        });
        return dailyStats;
    }

    StationService.list().then(function(data) {
        HttpErrorHandler.clearError($scope);
        $scope.stations = data.data;
        StatService.list($scope.stations[0].station_id).then(function(data2) {
            $scope.normals = data2.data;
            $scope.dayIndexedNormals = _.indexBy(_.filter(data2.data, function(d) { return(d.month == curMonth) }), "day");
            $scope.dailyStats = processStats($scope.dayIndexedNormals);
        }, function(errResp) {
            HttpErrorHandler.handleError($scope, errResp);
        });
    }, function(errResp) {
        HttpErrorHandler.handleError($scope, errResp);
    });


}]);


