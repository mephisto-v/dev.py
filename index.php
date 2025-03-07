<?php
// Connect to MySQL
$host = "localhost";
$user = "root";  // Default XAMPP MySQL user
$pass = "";      // Default XAMPP MySQL password (empty)
$db = "vulnerable_db";

$conn = new mysqli($host, $user, $pass, $db);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Get 'id' parameter from URL
$id = $_GET['id'] ?? 1;

// **Vulnerable SQL Query (No Prepared Statements)**
$sql = "SELECT * FROM users WHERE id = $id";
$result = $conn->query($sql);

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fake User Profile</title>
</head>
<body>
    <h1>User Profile</h1>
    <?php if ($result && $result->num_rows > 0): ?>
        <?php while ($row = $result->fetch_assoc()): ?>
            <p><strong>ID:</strong> <?= $row['id'] ?></p>
            <p><strong>Username:</strong> <?= $row['username'] ?></p>
            <p><strong>Email:</strong> <?= $row['email'] ?></p>
        <?php endwhile; ?>
    <?php else: ?>
        <p>No user found.</p>
    <?php endif; ?>

    <footer>
        <p>&copy; 2025 My Fake Website</p>
    </footer>
</body>
</html>

<?php
$conn->close();
?>
