var http = require('http');

const getPage = (url, delay = 0) => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
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
        }, delay);
    });
};

module.exports = {
    getPage: getPage
};