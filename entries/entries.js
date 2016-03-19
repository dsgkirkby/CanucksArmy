var fs = require('fs');
var http = require('http');
var cheerio = require('cheerio');
var csv = require('fast-csv');
var csv_writer = require('csv-write-stream');
var _ = require('underscore');

var PERIOD = 'Period';
var TIME = 'Time';
var TYPE = 'Entry Type';
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

var FILENAME = 'ZoneEntries-TOR.csv';
var OUTPUTFILENAME = 'entries-2.csv';
var TEAMNAME = 'TOR';

var getEntries = fileName => {
	return new Promise((resolve, reject) => {
		var entries = [];
		fs.createReadStream(fileName)
			.pipe(csv({
				headers: true
			})).on('data', data => {
				entries.push(data);
			}).on('end', () => {
				resolve(entries);
			});
	});
};

var getPage = url => {
	return new Promise((resolve, reject) => {
		http.get(url, response => {

			var body = '';

			response.on('data', (chunk) => {
				body += chunk;
			});

			response.on('end', () => {
				resolve(body);
			});

			response.on('error', error => {
				reject(error);
			});
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
}

var convertTimeToFullDigits = time => {
	time = time.length < 5 ? '0' + time : time;
	return time;
}

getEntries(FILENAME).then(entries => {
	var gameSheets = [];
	var games = _.each(entries, entry => {
		if (_.find(entries, entry2 => {
			return entry[GAMEID] === entry2[GAMEID] && entry[LOCATION] === entry2[LOCATION];
		}) === entry) {
			gameSheets.push({
				game: entry[GAMEID],
				location: entry[LOCATION]
			});
		}
	});	
	

	gameSheetPromises = _.map(gameSheets, gameSheet => {
		return getPage(
			'http://www.nhl.com/scores/htmlreports/20152016/T' + 
			(gameSheet.location === 'HOME' ? 'H' : 'V') + 
			'0' + gameSheet.game + '.HTM');
	});

	Promise.all(gameSheetPromises).then(data => {
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
					end: convertTimeToFullDigits(shiftEnd),
				});
			};
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

			players.forEach(player => {
				var playerDidEntry = player === enterer;
				if (entryBurdens[player.name]) {
					entryBurdens[player.name].push(playerDidEntry);
				} else {
					entryBurdens[player.name] = [playerDidEntry];
				}
			});
		});

		var output = []

		for (var entryBurden in entryBurdens) {
			var playerEntries = entryBurdens[entryBurden].reduce((a, b) => a + b);
			var totalEntries = entryBurdens[entryBurden].length;
			output.push({
				'Player Name': entryBurden,
				'Player Entries': playerEntries,
				'On Ice Total': totalEntries,
				'Success Percentage': (playerEntries / totalEntries * 100).toFixed(2) + '%'
			});
		}

		var writer = csv_writer();
		writer.pipe(fs.createWriteStream(OUTPUTFILENAME));
		output.forEach(line => {
			writer.write(line);
		});
		writer.end();
	});
});
