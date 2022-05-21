<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';


if ($_SERVER['REQUEST_METHOD'] === 'POST') {

	$data = json_decode(file_get_contents("php://input", true));

	$sql = "SELECT * FROM user WHERE username = '" . mysqli_real_escape_string($dbConn, $data->username) . "' AND password = '" . mysqli_real_escape_string($dbConn, $data->password) . "' LIMIT 1";

	$result = dbQuery($sql);

	if (dbNumRows($result) < 1) {
		// user not found or incorrect password
		http_response_code(401); #401 Unauthorized
		echo json_encode(array('error' => 'Login failed: Incorrect credentials'));
	} else {

		$row = dbFetchAssoc($result);

		$username = $row['username'];
		$id = $row['id'];

		$headers = array('alg' => 'HS256', 'typ' => 'JWT');
		$payload = array('username' => $username, 'user_id' => $id, 'exp' => (time() + 3600)); // set expiration time to one hour

		$jwt = generate_jwt($headers, $payload);

		http_response_code(200); #200 Ok
		echo json_encode(array('token' => $jwt, 'accessToken' => $jwt, 'id' => $id, 'email' => 'test@test.com', 'username' => $username,  "roles" => ['ROLE_ADMIN', 'ROLE_MODERATOR', 'ROLE_USER']));
	}
}

//End of file
