<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'db_connection.php'; 

function dbQuery($sql) {
	//global $dbConn;
	//$result = mysqli_query($dbConn, $sql) or die(mysqli_error($dbConn));
	$dbConn=mysqli_connect('sql31.mcb.webhuset.no', '153413_ildkule_dev', 'griHUPU388', '153413_ildkule_dev');
	$result = mysqli_query($dbConn, $sql) or die(mysqli_error($dbConn));
	mysqli_close($dbConn);
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