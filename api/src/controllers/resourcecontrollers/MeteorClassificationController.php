<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'jwt_utils.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'MeteorDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'MeteorController.php';


// Set or update meteor classification
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {

	$bearer_token = get_bearer_token();

	if (!empty($bearer_token)) {

		// Verify user
		if (is_jwt_valid($bearer_token)) {

			$data = json_decode(file_get_contents("php://input", true));

			// handle user classification - only field that gets updated!
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
