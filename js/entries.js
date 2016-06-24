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

var TEAMNAME = cli.team;
var FILENAME = 'ZoneEntries-' + TEAMNAME + '.csv';
var OUTPUTFILENAME = 'burdens-' + TEAMNAME + '.csv';

var add = (a, b) => Number(a) + Number(b);

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

var convertTimeStringToMinutes = (time) => {
    var parts = time.split(':');
    var minutes = Number(parts[0]);
    var seconds = Number(parts[1]);
    return minutes + seconds / 60;
};

var getEntrySummary = entries => {
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
            if (_.find(entries, entry2 =>
                entry[GAMEID] === entry2[GAMEID] && entry[LOCATION] === entry2[LOCATION]) === entry) {
                gameSheets.push({
                    game: entry[GAMEID],
                    location: entry[LOCATION]
                });
            }
        });

        let delay = 0;

        var gameSheetPromises = _.map(gameSheets, gameSheet => {
            delay += 500;
            return helpers.getPage(
                'http://www.nhl.com/scores/htmlreports/20152016/T' +
                (gameSheet.location.toLowerCase() === 'home' ? 'H' : 'V') +
                '0' + gameSheet.game + '.HTM', delay);
        });

        Promise.all(gameSheetPromises).then(data => {

            try {
                var shifts = [];
                var entryBurdens = {};
                var oppositionEntries = {};
                var icetimes = {};

                data.forEach((page, index) => {
                    var $ = cheerio.load(page);

                    var $names = $(".playerHeading");
                    var $evtoi = $("td.bborder.lborder:contains('TOT')").next().next().next().next();
                    for (var i = 0; i < $names.length; i++) {
                        var name = $($names[i]).text();
                        var iceTime = $($evtoi[i]).text();
                        if (!icetimes[name]) {
                            icetimes[name] = 0;
                        }
                        icetimes[name] += convertTimeStringToMinutes(iceTime);
                    }

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
                    if (entry[TMSTRENGTH] !== entry[OPPSTRENGTH]) {
                        return;
                    }

                    var entererNumber = entry[PLAYER].substr(0, entry[PLAYER].search(/[^0-9]/));

                    if (entererNumber.length < 1) {
                        return;
                    }

                    var time = getTimeFromPercentage(entry[TIME]);

                    var players = shifts.filter(shift => {
                        return shift.period == entry[PERIOD]
                            && shift.gameId == entry[GAMEID]
                            && shift.start >= time
                            && shift.end <= time;
                    });

                    var enterer = players.find(player => {
                        return player.name.substr(0, entererNumber.length) === entererNumber ? 1 : 0;
                    });

                    var entryMadeByOpposingTeam = entry[PLAYER].indexOf(TEAMNAME) < 0;

                    if (!enterer && !entryMadeByOpposingTeam) {
                        failed++;
                        return;
                    } else {
                        successful++;
                    }

                    var entryType = entry[TYPE];

                    players.forEach(player => {
                        if (entryMadeByOpposingTeam) {
                            if (!oppositionEntries[player.name]) {
                                oppositionEntries[player.name] = {};
                            }

                            if (!oppositionEntries[player.name][entryType]) {
                                oppositionEntries[player.name][entryType] = [];
                            }

                            oppositionEntries[player.name][entryType].push(entry[FEN]);
                        } else {
                            var playerDidEntry = player === enterer;
                            if (!entryBurdens[player.name]) {
                                entryBurdens[player.name] = {};
                            }

                            if (!entryBurdens[player.name][entryType]) {
                                entryBurdens[player.name][entryType] = [];
                            }

                            entryBurdens[player.name][entryType].push(playerDidEntry ? 1 : 0);
                        }

                    });
                });

                var output = [];

                for (var playerName in entryBurdens) {
                    var entryBurden = entryBurdens[playerName];
                    var summary = getEntrySummary(entryBurden);
                    var controlledAgainst = oppositionEntries[playerName][ENTRYTYPES.CONTROLLED].length;
                    var shotsFromControlledAgainst = oppositionEntries[playerName][ENTRYTYPES.CONTROLLED].reduce(add);
                    var uncontrolledAgainst = oppositionEntries[playerName][ENTRYTYPES.DUMPIN].length;
                    var shotsFromUncontrolledAgainst = oppositionEntries[playerName][ENTRYTYPES.DUMPIN].reduce(add);
                    var failedAgainst = oppositionEntries[playerName][ENTRYTYPES.FAILED].length;

                    output.push({
                        'Player Name': playerName,
                        'Player Entries': summary.player,
                        'On Ice For Total': summary.onIce,
                        'Burden Percentage': summary.burden,
                        'Controlled Against': controlledAgainst,
                        'Shots From Controlled Against': shotsFromControlledAgainst,
                        'Dump Ins Against': uncontrolledAgainst,
                        "Shots From Dump Ins Against": shotsFromUncontrolledAgainst,
                        "ES Ice Time": icetimes[playerName],
                        "Failed Against": failedAgainst,
                        "Total Against": controlledAgainst + uncontrolledAgainst,
                        "Total Shots Against": shotsFromControlledAgainst + shotsFromUncontrolledAgainst
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
