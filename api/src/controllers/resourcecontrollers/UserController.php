<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'User.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'UserDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'service'.DIRECTORY_SEPARATOR.'UserService.php'; 

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST");

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// Create new account 
	$data = json_decode(file_get_contents("php://input", true));
	$userService = new UserService();
	$userService->createNewUser($data->username, $data->password);
} elseif ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($id)) {
	// Get user account
	$bearer_token = get_bearer_token();
	if (is_jwt_valid($bearer_token)) {
		$sql = "SELECT id, username, role, user_level, create_time, update_time FROM user where username = '" . mysqli_real_escape_string($dbConn, getUserFromToken($bearer_token)["username"]) . "' limit 1";
		$results = dbQuery($sql);
		$rows = array();
		while ($row = dbFetchAssoc($results)) {
			$rows[] = $row;
		}
		if (!empty($rows)) {
			echo json_encode($rows[0]);
		} else {
			http_response_code(404); #404 Not found
			echo json_encode(array('error' => 'User not found'));
		}
	} else {
		http_response_code(401); #401 Unauthorized
		echo json_encode(array('error' => 'Unauthorized'));
	}
} else {
	http_response_code(405); #405 Method Not Allowed
	echo json_encode(array('error' => 'Not allowed'));
}
