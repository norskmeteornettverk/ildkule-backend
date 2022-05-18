

<?php

require_once 'db.php';
require_once 'jwt_utils.php';

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");

$bearer_token = get_bearer_token();

if (!empty($bearer_token)) {
	if (is_jwt_valid($bearer_token)) {
		$sql = "SELECT * FROM user_review where user_id = '" . mysqli_real_escape_string($dbConn, getUserFromToken($bearer_token)["user_id"]) . "' ";
		$results = dbQuery($sql);
		$rows = array();
		while ($row = dbFetchAssoc($results)) {
			$rows[] = $row;
		}
		echo json_encode($rows);
	} else {
		echo json_encode(array('error' => 'Access denied'));
	}
} else {
	echo json_encode(array('error' => 'Access denied'));
}


//End of file