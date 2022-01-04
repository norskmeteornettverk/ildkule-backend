<?php

require_once 'db_connection.php';

function dbQuery($sql) {
	global $dbConn;
	$result = mysqli_query($dbConn, $sql) or die(mysqli_error($dbConn));
	return $result;
}

function dbFetchAssoc($result) {
	return mysqli_fetch_assoc($result);
}

function dbNumRows($result) {
    return mysqli_num_rows($result);
}

function closeConn() {
	global $dbConn;
	mysqli_close($dbConn);
}
	
//End of file