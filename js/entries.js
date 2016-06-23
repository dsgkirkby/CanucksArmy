var fs = require('fs');
var http = require('http');
var cheerio = require('cheerio');
var csv = require('fast-csv');
var csv_writer = require('csv-write-stream');
var commandLineArgs = require('command-line-args');
var _ = require('underscore');
var helpers = require('./helpers');

var PERIOD = 'Period';
var TIME = 'Time';
var TYPE = 'Entry type';
var PLAYER = 'Player';
var NOTES = 'Notes';
var TMSTRENGTH = 'Team strength';
var OPPSTRENGTH = 'Opp strength';
var WASCONTROLLED = 'Controlled?';
var FEN = 'Fen total';
var GOAL = 'Goal total';
var DIDFAIL = 'Fail';
var GAMEID = 'Game';
var OPP = 'Opp';
var LOCATION = 'Location';
var TMSCORE = 'Team Score';
var OPPSCORE = 'Opp Score';

var SHIFTNUMBER = 0;
var SHIFTPERIOD = 1;
var SHIFTSTART = 2;
var SHIFTEND = 3;

var ENTRYTYPES = {
    CONTROLLED: 'C',
    DUMPIN: 'D',
    FAILED: 'F'
};

var WEIGHTINGS = {};
WEIGHTINGS[ENTRYTYPES.CONTROLLED] = 2;
WEIGHTINGS[ENTRYTYPES.DUMPIN] = 1;
WEIGHTINGS[ENTRYTYPES.FAILED] = 0;

var cli = commandLineArgs([
    {name: 'team', type: String, defaultOption: true}
]);

var options = cli.parse();

var TEAMNAME = options.team;
var FILENAME = 'ZoneEntries-' + TEAMNAME + '.csv';
var OUTPUTFILENAME = 'burdens-' + TEAMNAME + '.csv';

var getCsv = fileName => {
    return new Promise((resolve, reject) => {
        var csvData = [];
        fs.createReadStream(fileName)
            .pipe(csv({
                headers: true
            })).on('data', data => {
            csvData.push(data);
        }).on('end', () => {
            resolve(csvData);
        });
    });
};

var getTimeFromPercentage = p => {
    if (isNaN(p)) {
        return convertTimeToFullDigits(p);
    } else {
        p = parseFloat(p);
        p /= 0.833333333;
        var minutes = Math.floor(20 * p).toString();
        if (minutes.length < 2) {
            minutes = '0' + minutes;
        }
        var seconds = Math.floor(((20 * p) % 1) * 60).toString();
        if (seconds.length < 2) {
            seconds = '0' + seconds;
        }
        return minutes + ':' + seconds;
    }
};

var convertTimeToFullDigits = time => {
    time = time.length < 5 ? '0' + time : time;
    return time;
};

var getEntrySummary = entries => {
    var add = (a, b) => a + b;

    var player =
        (entries[ENTRYTYPES.CONTROLLED] || []).reduce(add, 0) * WEIGHTINGS[ENTRYTYPES.CONTROLLED] +
        (entries[ENTRYTYPES.DUMPIN] || []).reduce(add, 0) * WEIGHTINGS[ENTRYTYPES.DUMPIN] +
        (entries[ENTRYTYPES.FAILED] || []).reduce(add, 0) * WEIGHTINGS[ENTRYTYPES.FAILED];
    var onIce =
        (entries[ENTRYTYPES.CONTROLLED] || []).length * WEIGHTINGS[ENTRYTYPES.CONTROLLED] +
        (entries[ENTRYTYPES.DUMPIN] || []).length * WEIGHTINGS[ENTRYTYPES.DUMPIN] +
        (entries[ENTRYTYPES.FAILED] || []).length * WEIGHTINGS[ENTRYTYPES.FAILED];
    var burden = (player / onIce * 100).toFixed(2) + '%';
    return {
        player: player,
        onIce: onIce,
        burden: burden
    }
};

Promise.all([getCsv(FILENAME)]).then(data => {
    try {
        var entries = data[0];

        var gameSheets = [];
        _.each(entries, entry => {
            if (_.find(entries, entry2 => {
                    return entry[GAMEID] === entry2[GAMEID] && entry[LOCATION] === entry2[LOCATION];
                }) === entry) {
                gameSheets.push({
                    game: entry[GAMEID],
                    location: entry[LOCATION]
                });
            }
        });

        let delay = 0;

        var gameSheetPromises = _.map(gameSheets, gameSheet => {
            delay += 1000;
            return helpers.getPage(
                'http://www.nhl.com/scores/htmlreports/20152016/T' +
                (gameSheet.location.toLowerCase() === 'home' ? 'H' : 'V') +
                '0' + gameSheet.game + '.HTM', delay);
        });

        Promise.all(gameSheetPromises).then(data => {

            try {
                var shifts = [];
                var entryBurdens = {};

                data.forEach((page, index) => {
                    var $ = cheerio.load(page);

                    var $shifts = $('.oddColor, .evenColor');

                    var currentName;
                    var gameId = gameSheets[index].game;

                    for (var shiftId in $shifts.toArray()) {
                        var $shift = $($shifts[shiftId]);

                        var $data = $shift.find('td');
                        if ($data.length !== 6) {
                            continue;
                        }

                        if ($($data[SHIFTNUMBER]).text() === '1') {
                            currentName = $shift.prev().prev().text()
                        }

                        var shiftStart = $($data[SHIFTSTART]).text();
                        var shiftEnd = $($data[SHIFTEND]).text();

                        shiftStart = shiftStart.substring(shiftStart.indexOf('/') + 2);
                        shiftEnd = shiftEnd.substring(shiftEnd.indexOf('/') + 2);

                        shifts.push({
                            name: currentName.trim(),
                            period: parseInt($($data[SHIFTPERIOD]).text()),
                            gameId: gameId,
                            start: convertTimeToFullDigits(shiftStart),
                            end: convertTimeToFullDigits(shiftEnd)
                        });
                    }
                });

                var failed = 0;
                var successful = 0;

                entries.forEach(entry => {
                    if (entry[PLAYER].indexOf(TEAMNAME) < 0) {
                        return;
                    }

                    var time = getTimeFromPercentage(entry[TIME]);

                    var players = shifts.filter(shift => {
                        return shift.period == entry[PERIOD]
                            && shift.gameId == entry[GAMEID]
                            && shift.start >= time
                            && shift.end <= time;
                    });

                    var entererNumber = entry[PLAYER].substr(0, entry[PLAYER].indexOf(TEAMNAME));

                    var enterer = players.find(player => {
                        return player.name.substr(0, entererNumber.length) === entererNumber ? 1 : 0;
                    });

                    if (!enterer) {
                        failed++;
                        return;
                    } else {
                        successful++;
                    }

                    var entryType = entry[TYPE];

                    players.forEach(player => {
                        var playerDidEntry = player === enterer;
                        if (!entryBurdens[player.name]) {
                            entryBurdens[player.name] = {};
                        }

                        if (!entryBurdens[player.name][entryType]) {
                            entryBurdens[player.name][entryType] = [];
                        }

                        entryBurdens[player.name][entryType].push(playerDidEntry ? 1 : 0);
                    });
                });

                var output = [];

                for (var playerName in entryBurdens) {
                    var entryBurden = entryBurdens[playerName];
                    var summary = getEntrySummary(entryBurden);

                    output.push({
                        'Player Name': playerName,
                        'Player Entries': summary.player,
                        'On Ice Total': summary.onIce,
                        'Burden Percentage': summary.burden
                    });
                }

                var writer = csv_writer();
                writer.pipe(fs.createWriteStream(OUTPUTFILENAME));
                output.forEach(line => {
                    writer.write(line);
                });
                writer.end();
                console.log('success!');
                console.log(successful + ' successful, ' + failed + 'failed');
            } catch (e) {
                console.error(e.stack);
            }
        });
    } catch (e) {
        console.error(e.stack);
    }
});
