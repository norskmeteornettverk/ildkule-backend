<?php

require_once 'db.php';
require_once 'jwt_utils.php';


header("Access-Control-Allow-Headers: *");
header("Access-Control-Allow-Headers: POST");


if ($_SERVER['REQUEST_METHOD'] === 'POST') {


	$bearer_token = get_bearer_token();

	if (is_jwt_valid($bearer_token)) {

		// get posted data
		$data = json_decode(file_get_contents("php://input", true));



		$classification =   mysqli_real_escape_string($dbConn, $data->confirmed);

		$confirmed = -1;

		if ($classification == "Positive") {
			$confirmed = 1;
		} elseif ($classification == "Negative") {
			$confirmed = 0;
		} else {
			$confirmed = -1;
		};

		$sql = "INSERT INTO user_review (user_id, confirmed, meteor_id) VALUES (" .  strval($data->userID) . ", " . strval($confirmed) . ", " . strval($data->meteorID) . ")  ON DUPLICATE KEY UPDATE confirmed = VALUES(confirmed); ";
		error_log($sql);
		$result = dbQuery($sql);

		if ($result) {
			if ($classification == "Positive") {
				echo json_encode(array('msg' => 'Takk for din anbefaling (Ja)'));
			} elseif ($classification == "Negative") {
				echo json_encode(array('msg' => 'Takk for din anbefaling (Nei)'));
			} else {
				echo json_encode(array('msg' => 'Anbefalingen er nullstilt'));
			};
			
		} else {
			echo json_encode(array('error' => 'Error in data, sql failed' . $sql));
		}
	} else {
		echo json_encode(array('error' => 'Invalid access'));
	}
}
