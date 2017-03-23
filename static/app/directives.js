var app = angular.module("Normals");

app.directive("singleDistributionVis", [function() {
    function buildVis(scope, element, attrs) {

        var evalPoints = _.uniq(_.sortBy(_.range(scope.mean - 4 * scope.stddev, scope.mean + 4 * scope.stddev, 0.1 * scope.stddev).concat(
                _.range(scope.min, scope.max, 0.1 * scope.max - scope.min)), function(x) { return(x) }), true);
        if(scope.zeroTruncated) {
            var evalPoints = _.filter(evalPoints, function(p) { return p >= 0; });
        }

        var densityPoints = _.map(evalPoints, function(v) {
            return jStat.normal.pdf(v, scope.mean, scope.stddev);
        });
        var densityPairs = _.zip(evalPoints, densityPoints);
        if(scope.zeroTruncated) {
            // ensures the shape closes in the right way
            var densityPairs = [[0, 0]].concat(densityPairs);
        }

        var startX = scope.min;
        var endX = scope.max;
        var startY = 0;
        var endY = _.max(densityPoints) * 1.1;

        var svgWidth = 1000;
        var svgHeight = 1000;
        // computes the plot's y coordinate corresponding to a density
        var getYCoord = function(origY) {
           return svgHeight - (origY / endY) * svgHeight;
        }

        // computes the plot's x coordinate corresponding to a point in the data domain
        var getXCoord = function(origX) {
            return ((origX - startX) / (endX - startX)) * svgWidth;
        }

        var plotPairs = _.map(densityPairs, function(d) {
            return [getXCoord(d[0]), getYCoord(d[1])]
        });

        var boxWidth = d3.select(element.get(0)).node().getBoundingClientRect().width;
        d3.select(element.get(0)).style("height", boxWidth + "px");
        var svgElt = d3.select(element.get(0)).append("svg")
            .attr("viewBox", "-60 0 " + (svgWidth + 40) + " " + svgHeight)
            .attr("width", "100%")
            .attr("height", "100%");


        svgElt.append("rect")
            .attr("class", "grid-background")
            .attr("width", svgWidth)
            .attr("height", svgHeight);

        var xSeries = d3.scaleLinear().range([0, svgWidth]).domain([startX, endX]);
        var ySeries = d3.scaleLinear().range([svgHeight, 0]).domain([startY, endY]);
        
		svgElt.append("g")
			.attr("class", "grid")
			.attr("transform", "translate(0," + svgHeight + ")")
			.call(d3.axisBottom(xSeries).tickSize(-svgHeight).tickFormat(""))

		svgElt.append("g")
			.attr("class", "axis")
			.attr("transform", "translate(0," + svgHeight + ")")
			.call(d3.axisBottom(xSeries));

        svgElt.append("g")
            .attr("class", "grid")
            .call(d3.axisLeft(ySeries).tickSize(-svgWidth).tickFormat(""));

        svgElt.append("path")
            .attr("class", "line")
            .attr("fill", "rgba(117,138,161, 1)")
            .data([plotPairs])
            .attr("d", d3.line());
        
        console.log(scope.longTermMean);
        svgElt.append("line")
            .attr("stroke", "red")
            .attr("stroke-width", 4)
            .attr("x1", getXCoord(scope.longTermMean))
            .attr("x2", getXCoord(scope.longTermMean))
            .attr("y1", 0)
            .attr("y2", svgHeight);
        /*svgElt.selectAll("circle").data(plotPairs).enter().append("circle")
            .attr("cx", function(d) { return d[0] }).attr("cy", function(d) { return d[1] })
            .attr("r", 5);*/
   }

    return {
        link : function(scope, element, attrs) {
            scope.$watch("stddev", function(newVal, oldVal) {
                if(newVal != undefined) {
                    buildVis(scope, element, attrs);
                }
            });
        },
        scope : {
            mean: "=",
            stddev: "=",
            min: "=",
            max: "=",
            zeroTruncated: "=",
            longTermMean: "="
        }
    }
}]);
