<?php

require_once 'db.php';
require_once 'jwt_utils.php';

 
header("Access-Control-Allow-Headers: *");



if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// get posted data
	 $data = json_decode(file_get_contents("php://input", true));	
	
	$sql = "SELECT * FROM user WHERE username = '" . mysqli_real_escape_string($dbConn, $data->username) . "' AND password = '" . mysqli_real_escape_string($dbConn, $data->password) . "' LIMIT 1";
	
	$result = dbQuery($sql);
	
	if(dbNumRows($result) < 1) {
		echo json_encode(array('error' => 'Invalid User'));
	} else {

		$row = dbFetchAssoc($result);
		
		$username = $row['username'];
		$id = $row['id'];
		
		$headers = array('alg'=>'HS256','typ'=>'JWT');
		$payload = array('username'=>$username, 'user_id'=>$id, 'exp'=>(time() + 900));

		$jwt = generate_jwt($headers, $payload);
		
		echo json_encode(array('token' => $jwt, 'accessToken' => $jwt , 'id'=>$id, 'email' => 'test@test.com', 'username'=>$username,  "roles"=> ['ROLE_ADMIN','ROLE_MODERATOR','ROLE_USER']  ));
	} 
	
}

//End of file

/*

  id: user.id,
          username: user.username,
          email: user.email,
          roles: authorities,
          accessToken: token

*/