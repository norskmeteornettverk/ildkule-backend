<?php

require_once 'db.php';
require_once 'jwt_utils.php';

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");

$bearer_token = get_bearer_token();

if(is_jwt_valid($bearer_token)) {

	$sql = "SELECT id, username, role, user_level, create_time, update_time  FROM user";
	$results = dbQuery($sql);

	$rows = array();

	while($row = dbFetchAssoc($results)) {
		$rows[] = $row;
	}

	echo json_encode($rows);
} else {
	echo json_encode(array('error' => 'Access denied'));
}


//End of file