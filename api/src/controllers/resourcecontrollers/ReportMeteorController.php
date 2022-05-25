<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// Handle form data
	

	$data = json_decode(file_get_contents("php://input", true));
	

	print($data->form->navn);

	//include script that contains function that sends mail - dependant on phpmailer       
	require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . "phpmailer" . DIRECTORY_SEPARATOR . "mailer.php";


	$email = "meteorrapport@ildkule.net";

	$body =
		'
		Hei'.$data->form->navn.' !
		Vi har mottatt forespørsel om å resette ditt passord på ildkule.net.<br/>
		Om du ikke har gjort dette, kan du set bort i fra denne e-posten.<br/>
		Om du vil resette passordet, <a href="' . Config::frontUrl . '/resetpassword?passwordResetId=' . $user->password_reset_token . '"> besøker du oss her </a><br/>
		<br/>
		Hilsen ildkule.net            
		';

	sendMeteorMail($email, "Test fra ildkule", $body, $body);

	/*

	if ($result) {
		http_response_code(200);
		echo json_encode(array('message' => 'Passordet ble endret'));
	}
	else {
		http_response_code(401);
		echo json_encode(array('error' => 'Not authorized', 'message' => 'Kunne ikke opppdatere passordet - brukernavnet er feil, eller du har allerede endret passordet'));
	}

	*/

}
else {
	http_response_code(405); #405 Method Not Allowed
	echo json_encode(array('error' => 'Not allowed'));
}