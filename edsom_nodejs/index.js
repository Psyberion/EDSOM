const express = require('express');
const path = require('path');
const mysql = require('mysql');
const config = require('./config');

const app = express();

app.get('/api/lastEvent', (req, res) => {
    var cnn = mysql.createConnection(config.db);
    cnn.connect();
    //cnn.query("SELECT id, type FROM event WHERE id = (SELECT MAX(id) FROM event WHERE parsed = 'Y');",
    cnn.query("SELECT id, type FROM event ORDER BY id DESC LIMIT 5;",
        function (error, results, fields) {
            if (error) throw error;
            console.log(`The last event is: ${results[0].id} (${results[0].type})`);
            res.json(results);
        });
    cnn.end();
});

app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));
