<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	// Handle form data
	

	$data = json_decode(file_get_contents("php://input", true));

	// reCAPTCHA validation
	$rcToken = $data->rcToken;    
	$recaptcha_secret = Config::recaptcha_secret;
	$response = file_get_contents("https://www.google.com/recaptcha/api/siteverify?secret=".$recaptcha_secret."&response=".$rcToken);
	$response = json_decode($response, true);
	if($response["success"] === false) {
	  http_response_code(401);
	  $message = 'Kontaktskjema mottatt, men forespørsel ble ikke autetisert som en vanlig bruker med reCAPTCHA';
	  echo json_encode(array(
		  					 'error' => $message,
	  						 'message' => $message
							));
	} 

	//include script that contains function that sends mail - dependant on phpmailer       
	require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . "phpmailer" . DIRECTORY_SEPARATOR . "mailer.php";


	$email = "meteorrapport@ildkule.net";

	$body =
		'Hei!<br>' . $data->form->navn . ' har meldt inn en ny observasjon via ildkule.net.<br><br>' .
		'<table style="border: solid 1px; padding: 5px; text-align: left; width=50%">
		<tr style="background-color: #D6EEEE;">
		  <th>Felt</th>
		  <th>Innrapportert data</th>
		</tr>
		<tr>
		  <td style>Kontaktinformasjon</td>
		  <td>'. $data->form->navn .',<br> ' . $data->form->epost . ',<br>Tlf: ' . $data->form->telefon . '</td>
		</tr>
		<tr style="background-color: #D6EEEE;">
		  <td>Observasjonssted</td>
		  <td>Lat: ' . $data->form->latitude . ',<br> Long: ' . $data->form->longitude . '</td>
		</tr>
        <tr>
		  <td>Først sett</td>
		  <td>Himmelretning: ' . $data->form->firstdirection . ',<br> Høyde: '. $data->form->firstheight . '</td>
		</tr>        
        <tr style="background-color: #D6EEEE;">
		  <td>Sist sett</td>
		  <td>Himmelretning: ' . $data->form->lastdirection . ',<br> Høyde: ' . $data->form->lastheight . '</td>
		</tr>
         <tr>
		  <td>Farge</td>
		  <td>' . $data->form->farge . '</td>
		</tr>
        <tr style="background-color: #D6EEEE;">
		  <td>Lysstyrke</td>
		  <td>' . $data->form->lysstyrke . '</td>
		</tr>
        <tr>
		  <td>Varighet</td>
		  <td>' . $data->form->varighet . '</td>
		</tr>
        <tr style="background-color: #D6EEEE;">
		  <td>Kommentarer:</td>
		  <td>' . $data->form->melding . '</td>
		</tr>
	  </table><br><br>
	  Denne e-posten er automatisk sendt fra ildkule.net.';

	sendMeteorMail($email, "Ny observasjon fra ildkule.net", $body, $body);

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