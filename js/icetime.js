var commandLineArgs = require('command-line-args');
var helpers = require('./helpers');
var cheerio = require('cheerio');

var cli = commandLineArgs([
    {name: 'games', type: String, defaultOption: true}
]);

// var options = cli.parse();

var gameIds = cli.games.split(',');

let delay = 0;

var gameSheetPromises = gameIds.map((gameId) => {
    delay += 1000;
    return helpers.getPage('http://www.nhl.com/scores/htmlreports/20152016/' + gameId + '.HTM', delay);
});

var convertTimeStringToSeconds = (time) => {
    var parts = time.split(':');
    var minutes = Number(parts[0]);
    var seconds = Number(parts[1]);
    return minutes + seconds / 60;
};

Promise.all(gameSheetPromises).then((data) => {
    try {
        var results = {};

        data.forEach((page) => {
            var $ = cheerio.load(page);
            var $names = $(".playerHeading");
            var $evtoi = $("td.bborder.lborder:contains('TOT')").next().next().next().next();
            for (var i = 0; i < $names.length; i++) {
                var name = $($names[i]).text();
                var iceTime = $($evtoi[i]).text();
                if (!results[name]) {
                    results[name] = 0;
                }
                results[name] += convertTimeStringToSeconds(iceTime);
            }
        });

        for (var result in results) {
            if (!results.hasOwnProperty(result)) {
                continue;
            }
            console.log(result + ': ' + results[result].toFixed(2));
        }
    } catch (e) {
        console.error(e.stack);
    }

});