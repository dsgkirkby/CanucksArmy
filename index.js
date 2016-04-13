var fs = require('fs');
var http = require('http');
var cheerio = require('cheerio');
var csv_writer = require('csv-write-stream');
var commandLineArgs = require('command-line-args');
var _ = require('underscore');

var cli = commandLineArgs([
	{name: 'team', type: String, defaultOption: true}
]);

var options = cli.parse();

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

getPage('http://collegehockeyinc.com/stats/boxes16.php?mmtbndk1.o03').then(data => {
	try {
		var $ = cheerio.load(data);
		var $gameTables = $('.chsboxtext');

		var $rosterTable = $($gameTables[0]);
		var $boxScoreTable = $($gameTables[1]);

		var cells = $rosterTable.find('tr:not(.chsbox10) > td').toArray();
		var players = [];

		for (var i = 0; i < cells.length; i += 5) {
			if ($(cells[i]).text().trim().length < 1) {
				i -= 4;
				continue;
			}

			var $position = $(cells[i]);
			var $number = $(cells[i + 1]);
			var $name = $(cells[i + 2]);
			var $scoring = $(cells[i + 3]);
			var $extras = $(cells[i + 4]);

			players.push({
				position: $position.text().trim(), 
				number: $number.text().trim(), 
				name: $name.text().trim(), 
				scoring: $scoring.text().trim(), 
				extras: $extras.text().trim()
			});
		}

		var rows = $boxScoreTable.find('tr:not(.chsbox10)').toArray();
		var goals = [];
		var period = 0;

		for (var j = 0; j < rows.length; j++) {
			var $mainRow = $(rows[j]);
			var $secondaryRow = $(rows[j + 1]);

			if ($mainRow.text().indexOf('(20:00)') > 0) {
				period++;
				continue;
			}

			var $mainFields = $mainRow.find('td').toArray().map($);
			var $secondaryFields = $secondaryRow.find('td').toArray().map($);

			if ($mainFields[0].text().trim().length < 1) {
				continue;
			}

			var scoring = $mainFields[6].text();
			var onIce = $secondaryFields[1].text().split(/\s+/);

			goals.push({
				period: period,
				time: $mainFields[7].text().trim(),
				team: $mainFields[0].text().trim(),
				score: $mainFields.slice(1,4).map(a => a.text().trim()).join(' '),
				type: $mainFields[4].text().trim(),
				scorer: scoring.substring(0, scoring.indexOf('(') || scoring.length).trim(),
				assists: scoring.substring(scoring.indexOf('(') + 1 || 0, scoring.indexOf(')') || 0),
				offense: onIce[3],
				defense: onIce[6]
			});
		}

		var writer = csv_writer();
		writer.pipe(fs.createWriteStream('goals.csv'));
		goals.forEach(goal => {
			writer.write(goal);
		});
		writer.end();
		var writer2 = csv_writer();
		writer2.pipe(fs.createWriteStream('roster.csv'));
		players.forEach(player => {
			writer2.write(player);
		});
		writer2.end();
	} catch (e) {
		console.log(e);
	}
});
