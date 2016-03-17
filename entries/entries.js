var fs = require('fs');
var http = require('http');
var cheerio = require('cheerio');
var csv = require('fast-csv');

var PERIOD = 0;
var TIME = 1;
var TYPE = 2;
var PLAYER = 3;
var NOTES = 4;
var TMSTRENGTH = 5;
var OPPSTRENGTH = 6;
var WASCONTROLLED = 7;
var FEN = 8;
var GOAL = 9;
var DIDFAIL = 10;
var GAMEID = 11;
var OPP = 12;
var LOCATION = 13;
var TMSCORE = 14;
var OPPSCORE = 15;

var SHIFTNUMBER = 0;
var SHIFTPERIOD = 1;
var SHIFTSTART = 2;
var SHIFTEND = 3;

var row = [1,0.829861111,'F','8WSH',null,5,5,null,0,0,'8WSH',20423,'FLA','HOME',0,1];

var getPage = function(url) {
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
		return p;
	} else {
		p = parseFloat(p);
		var minutes = Math.floor(20 * p);
		if (minutes.length < 2) {
			minutes = '0' + minutes;
		}
		var seconds = Math.floor(((20 * p) % 1) * 100);
		return minutes + ':' + seconds;
	}
}

var convertTimeToFullDigits = time => {
	time = time.length < 5 ? '0' + time : time;
	return time;
}

var homeShiftPagePromise = getPage('http://www.nhl.com/scores/htmlreports/20152016/TH0' + row[GAMEID] + '.HTM')
// var visitorShiftPagePromise = getPage('http://www.nhl.com/scores/htmlreports/20152016/TV0' + row[GAMEID] + '.HTM')

homeShiftPagePromise.then(page => {
	var $ = cheerio.load(page);

	var shifts = [];
	var $shifts = $('.oddColor, .evenColor');

	var currentName;
	var gameId = row[GAMEID];

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

		shiftStart = shiftStart.substring(0, shiftStart.indexOf('/') - 1);
		shiftEnd = shiftEnd.substring(0, shiftEnd.indexOf('/') - 1);

		shifts.push({
			name: currentName,
			period: parseInt($($data[SHIFTPERIOD]).text()),
			start: convertTimeToFullDigits(shiftStart),
			end: convertTimeToFullDigits(shiftEnd),
		});
	}

	var time = getTimeFromPercentage(row[TIME]);
	console.log(time);

	var players = shifts.filter(shift => {
		var time = getTimeFromPercentage(row[TIME]);
		return shift.period === row[PERIOD] && shift.start < time && shift.end > time;
	});

	console.log(players);
});
