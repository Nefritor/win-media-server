import {PythonShell} from 'python-shell';
import WSExpress from 'express-ws';
import express from 'express';
import cors from 'cors';
import http from 'http';

const PORT = 1232;
const { app, server } = startServer(PORT);

const broadcaster = openWebSocket(
    app,
    server,
    {
        'media-info': {
            onOpen: () => {
                console.log('WebSocket:', 'Socket opened');
            },
            onMessage: (data) => {
                // console.log('WebSocket:', `Data received: ${data}`);
            },
            onClose: () => {
                console.log('WebSocket:', 'Socket closed');
            }
        }
    });

startPyShell({
    onOpen: () => {
        console.log('PyShell:', 'Connection opened');
    },
    onMessage: (data) => {
        // console.log('PyShell:', `Message received: ${data}`);
        broadcaster(data);
    },
    onClose: () => {
        console.log('PyShell:', `Connection closed`);
    }
});

function startServer(port) {
    const app = express();

    app.use(express.json());
    app.use(cors());

    const server = http.createServer(app).listen(port, () => {
        console.log(`Application started on ${port}`);
    });
    return { app, server };
}

function openWebSocket(app, server, config) {
    const wss = WSExpress(app, server).getWss();

    Object.entries(config).forEach(([url, { onOpen, onMessage, onClose }]) => {
        app.ws(`/${url}`, (ws, req) => {
            onOpen?.(ws, req);
            ws.on('message', (msg) => {
                onMessage(ws, JSON.parse(msg));
            });
            ws.on('close', (code) => {
                onClose(ws, code);
            });
        });
    });

    return getBroadcaster(wss);
}

function getBroadcaster(wss) {
    return function (data, selector) {
        wss.clients.forEach((client) => {
            if (!selector || selector(client)) {
                client.send(JSON.stringify(data));
            }
        });
    };
}

function startPyShell({ onOpen, onClose, onMessage }) {
    const pyshell = new PythonShell('./scripts/main.py');
    onOpen?.();

    pyshell.on('message', (data) => {
        // console.log(data);
        onMessage?.(data);
    });

    pyshell.on('close', () => {
        onClose?.();
        pyshell.kill();
    });
    pyshell.on('error', (message) => {
        console.error('Error', message);
    });
    pyshell.on('pythonError', (message) => {
        console.error('Python error', message);
    });
}
