<?php
// Assuming you have a MySQL database connection already established
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

if (isset($_GET['id'])) {
    // Vulnerable query (SQL Injection point)
    $id = $_GET['id'];
    $sql = "SELECT * FROM table_name WHERE id = $id";  // Vulnerable to SQLi here
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        // Output data from the table
        while($row = $result->fetch_assoc()) {
            echo "id: " . $row["id"]. " - Name: " . $row["name"]. "<br>";
        }
    } else {
        echo "0 results";
    }
}

$conn->close();
?>

