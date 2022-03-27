<?php

require_once 'db.php';
require_once 'jwt_utils.php';

 
header("Access-Control-Allow-Headers: *");


if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// get posted data
	 $data = json_decode(file_get_contents("php://input", true));	

	 $classification =   mysqli_real_escape_string($dbConn,$data->confirmed) ;

	 $confirmed = -1;

	 if ($classification == "Positive") {
		$confirmed = 1;
		} elseif ( $classification == "Negative") {
			$confirmed = 0;
		} else {
				$confirmed =-1;
			};	
		
	
	$sql = "INSERT INTO user_review (user_id, confirmed, meteor_id) VALUES (" .  strval(  $data->userID) . ", " . strval(  $confirmed) . ", " .strval(   $data->meteorID) . ")  ON DUPLICATE KEY UPDATE confirmed = VALUES(confirmed); ";
	$result = dbQuery($sql);
	
	if($result) {
		echo json_encode(array('msg' => 'Success!'));		
	} else {	
		echo json_encode(array('error' => 'Error in data, sql failed'.$sql));			
	} 
	
}

