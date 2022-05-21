<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'jwt_utils.php';


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
		http_response_code(401); #401 Unauthorized
		echo json_encode(array('error' => 'Unauthorized'));
	}
} else {	
	http_response_code(401); #401 Unauthorized
	echo json_encode(array('error' => 'Unauthorized'));
}


//End of file