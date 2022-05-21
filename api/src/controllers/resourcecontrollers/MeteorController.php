<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'MeteorDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'service'.DIRECTORY_SEPARATOR.'MeteorService.php'; 


// Get meteor
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
	header('Content-Type: application/json; charset=utf-8');
	$meteorService = new MeteorService();
 	$json = $meteorService->getMeteorByID($id);

	if ($json === false or !isset($json)) {
		// Avoid echo of empty string (which is invalid JSON), and
		// JSONify the error message instead:
		$json = json_encode(["jsonError" => json_last_error_msg()]);
		if ($json === false) {
		  // This should not happen, but we go all the way now:
		  $json = '{"jsonError":"unknown"}';
		}
		// Set HTTP response status code to: 500 - Internal Server Error
		http_response_code(500);
	  }
	echo $json;
};


// Updating meteor 
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {

	$bearer_token = get_bearer_token();

	if (!empty($bearer_token)) {

		// Verify user
		if (is_jwt_valid($bearer_token)) {

			$data = json_decode(file_get_contents("php://input", true));

			// handle user confirmation data - only field that gets updated
			$classification =   mysqli_real_escape_string($dbConn, $data->user_confirmed);
			$confirmed = -1;
			if ($classification == "1") {
				$confirmed = 1;
			} elseif ($classification == "0") {
				$confirmed = 0;
			} else {
				$confirmed = -1;
			};

			$sql = "update meteor set user_confirmed = " .  strval($confirmed) . " where id = " . strval($data->id);
			$result = dbQuery($sql);

			if ($result) {
				http_response_code(200);
				echo json_encode(array('msg' => 'Success!'));
			} else {
				echo json_encode(array('error' => 'Error in data, sql failed' . $sql));
			}
		} else {
			http_response_code(401);
			echo json_encode(array('error' => 'Not authorized'));
		}
	} else {
		http_response_code(401);
		echo json_encode(array('error' => 'Not authorized'));
	}
}
