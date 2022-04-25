<?php 
header("Access-Control-Allow-Origin: *");

ini_set('display_errors', 1);


require_once 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'config.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'Meteor.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'DatabaseConnection.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'MeteorDao.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'controllers'.DIRECTORY_SEPARATOR.'MeteorController.php'; 




if ($_SERVER['REQUEST_METHOD'] === 'GET') {  
  header('Content-Type: application/json; charset=utf-8');
  $controller = new MeteorController();  
  echo ($controller->getMeteorByID($id));  
};


if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
	// get posted data
	 $data = json_decode(file_get_contents("php://input", true));	

	 $classification =   mysqli_real_escape_string($dbConn,$data->user_confirmed) ;

	 $confirmed = -1;

	 if ($classification == "1") {
		$confirmed = 1;
		} elseif ( $classification == "0") {
			$confirmed = 0;
		} else {
				$confirmed =-1;
			};	
		  	
	$sql = "update meteor set user_confirmed = " .  strval(  $confirmed) . " where id = " .strval(   $data->id) ;
	$result = dbQuery($sql);
	
	if($result) {
		echo json_encode(array('msg' => 'Success!'));		
	} else {	
		echo json_encode(array('error' => 'Error in data, sql failed'.$sql));			
	} 
	
}