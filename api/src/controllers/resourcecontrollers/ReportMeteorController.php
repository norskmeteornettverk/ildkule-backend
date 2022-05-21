<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';


header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST");
	
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// Handle form data

} else {
	http_response_code(405); #405 Method Not Allowed
	echo json_encode(array('error' => 'Not allowed'));
}