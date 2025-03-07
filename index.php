<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "vulnerable_db";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$id = isset($_GET['id']) ? $_GET['id'] : '';

$sql = "SELECT * FROM users WHERE id = '$id'";
$result = $conn->query($sql);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Information</title>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .container {
            width: 50%;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .user-info {
            margin-top: 20px;
        }
        .user-info p {
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>User Information</h1>
        <form method="GET" action="">
            <label for="id">User ID:</label>
            <input type="text" name="id" id="id">
            <button type="submit">Get User Info</button>
        </form>
        <div class="user-info">
            <?php
            if ($result && $result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {
                    echo "<p><strong>ID:</strong> " . $row["id"]. "</p>";
                    echo "<p><strong>Name:</strong> " . $row["name"]. "</p>";
                    echo "<p><strong>Email:</strong> " . $row["email"]. "</p>";
                }
            } else {
                echo "<p>No user found with ID: " . htmlspecialchars($id) . "</p>";
            }
            $conn->close();
            ?>
        </div>
    </div>
</body>
</html>
