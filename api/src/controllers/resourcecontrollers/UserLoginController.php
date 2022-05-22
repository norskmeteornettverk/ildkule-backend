<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api'. DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'BaseController.php';

class UserLoginController extends BaseController
{

	protected function get()
	{
		http_response_code(403);
	}


	protected function post()
	{
		$data = json_decode(file_get_contents("php://input", true));
		$dbConn = mysqli_connect(Config::host, Config::user, Config::password, Config::database);		
		$sql = "SELECT * FROM user WHERE username = '" . mysqli_real_escape_string($dbConn, $data->username) . "' AND password = '" . mysqli_real_escape_string($dbConn, $data->password) . "' LIMIT 1";
		$result = dbQuery($sql);
		if (dbNumRows($result) < 1) {
			// user not found or incorrect password
			http_response_code(401); #401 Unauthorized
			echo json_encode(array('error' => 'Login failed: Incorrect credentials', 'message' => 'Feil brukernavn eller passord'));
		}
		else {
			$row = dbFetchAssoc($result);
			$username = $row['username'];
			$id = $row['id'];
			$headers = array('alg' => 'HS256', 'typ' => 'JWT');
			$payload = array('username' => $username, 'user_id' => $id, 'exp' => (time() + 36000)); // set expiration time to ten hours
			$jwt = generate_jwt($headers, $payload);
			http_response_code(200); #200 Ok
			echo json_encode(array('message' => 'Innlogging utført!','token' => $jwt, 'accessToken' => $jwt, 'id' => $id, 'email' => 'test@test.com', 'username' => $username, "user_level" => 'LEVEL_MEDIUM', "roles" => ['ROLE_ADMIN', 'ROLE_MODERATOR', 'ROLE_USER']));
		}
	}


	protected function put()
	{
		http_response_code(403);
	}


	protected function patch()
	{
		http_response_code(403);
	}


	protected function delete()
	{
		http_response_code(403);
	}


}

$controller = new UserLoginController(false, null, null, true, null);
$controller->handleRequest();

