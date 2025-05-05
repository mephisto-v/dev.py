const express = require('express');
const http = require('http');
const { v4: uuid } = require('uuid');
const socketIO = require('socket.io');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');

const app = express();
const expressHTTPServer = http.createServer(app);
const io = new socketIO.Server(expressHTTPServer);

// Middleware
app.use(express.static('public'));
app.set('view engine', 'ejs');
app.use(bodyParser.json());

// Database setup
const db = new sqlite3.Database('./users.db', (err) => {
    if (err) {
        console.error('Could not connect to database', err);
    } else {
        console.log('Connected to SQLite database');
        db.run(
            `CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )`
        );
    }
});

// Routes
app.get('/', (req, res) => {
    res.redirect(`/${uuid()}`);
});

app.get('/:roomId', (req, res) => {
    const roomId = req.params.roomId;
    res.render('index', {
        roomId
    });
});

// User registration
app.post('/register', async (req, res) => {
    const { username, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);

    db.run(
        `INSERT INTO users (username, password) VALUES (?, ?)`,
        [username, hashedPassword],
        (err) => {
            if (err) {
                if (err.code === 'SQLITE_CONSTRAINT') {
                    res.status(400).send('Username already exists');
                } else {
                    console.error(err);
                    res.status(500).send('Internal server error');
                }
            } else {
                res.status(201).send('User registered successfully');
            }
        }
    );
});

// User login
app.post('/login', (req, res) => {
    const { username, password } = req.body;

    db.get(
        `SELECT * FROM users WHERE username = ?`,
        [username],
        async (err, user) => {
            if (err) {
                console.error(err);
                res.status(500).send('Internal server error');
            } else if (!user) {
                res.status(404).send('User not found');
            } else {
                const isPasswordValid = await bcrypt.compare(password, user.password);
                if (isPasswordValid) {
                    // Generate a session token (simplified for example purposes)
                    const sessionToken = uuid();
                    res.status(200).send({ token: sessionToken });
                } else {
                    res.status(401).send('Invalid password');
                }
            }
        }
    );
});

// Socket.IO setup
io.on('connection', (socket) => {
    console.log('Socket connected!');

    // Joining a new room
    socket.on('joinRoom', (roomId) => {
        socket.join(roomId);
        // Notify others about the new joining in the room
        socket.to(roomId).emit('newJoining');
    });

    // Send the offer
    socket.on('sendTheOffer', (offer, roomId) => {
        socket.to(roomId).emit('receiveOffer', offer);
    });

    // Send the answer
    socket.on('sendTheAnswer', (answer, roomId) => {
        socket.to(roomId).emit('receiveAnswer', answer);
    });

    // Send ICE candidate
    socket.on('sendIceCandidate', (candidate, roomId) => {
        socket.to(roomId).emit('receiveCandidate', candidate);
    });
});

// Start the server
expressHTTPServer.listen(8080, '0.0.0.0', () => {
    console.log('Server is running on http://0.0.0.0:8080');
});
