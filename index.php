<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WORMX Infection</title>
    <style>
        body {
            background-color: red;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
            color: white;
            font-size: 2em;
            animation: flicker 1.5s infinite;
        }

        @keyframes flicker {
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
                opacity: 1;
            }
            20%, 24%, 55% {
                opacity: 0.5;
            }
        }
    </style>
</head>
<body>
    <div>YOU ARE INFECTED BY WORMX!</div>
</body>
</html>
