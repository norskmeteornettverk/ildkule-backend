<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';

/**
 * Handles the contact requests sent in a form
 *
 */
class ContactController extends AbstractController
{

  protected function get()
  {
    http_response_code(403);
  }

  protected function post()
  {
    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
    if (!$validRequest)  return;

    $data = json_decode(file_get_contents("php://input", true));

    // reCAPTCHA validation
    $rcToken = $data->rcToken;    
    $recaptcha_secret = Config::recaptcha_secret;
    $response = file_get_contents("https://www.google.com/recaptcha/api/siteverify?secret=".$recaptcha_secret."&response=".$rcToken);
    $response = json_decode($response, true);
    if($response["success"] === false) {
      http_response_code(401);
      echo json_encode(array('message' => 'Kontaktskjema mottatt, men forespørsel ble ikke autetisert som en vanlig bruker med reCAPTCHA'));
    } 

    //include script that contains function that sends mail - dependant on phpmailer       
    require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . "phpmailer" . DIRECTORY_SEPARATOR . "mailer.php";

    $email = "meteorrapport@ildkule.net"; //Send contact form to this e-mail

    $body =
      'Hei!<br>' . $data->form->fornavn . ' har sendt inn et kontaktskjema via ildkule.net.<br><br>' .
      '<table style="border: solid 1px; padding: 5px; text-align: left;">
      <tr style="background-color: #D6EEEE;">
        <th>Felt</th>
        <th>Verdi</th>
      </tr>
      <tr>
        <td >Fornavn</td>
        <td>' . $data->form->fornavn . '</td>
      </tr>
      <tr style="background-color: #D6EEEE;">
        <td>Etternavn</td>
        <td>' . $data->form->etternavn . '</td>
      </tr>
      <tr>
        <td >E-post</td>
        <td>' . $data->form->epost . '</td>
      </tr>
      <tr style="background-color: #D6EEEE;">
        <td>Melding</td>
        <td>' . $data->form->melding . '</td>
      </tr>       
      </table><br><br>
      Denne e-posten er automatisk sendt fra ildkule.net.';

    try {
      sendMeteorMail($email, "Ny kontaktmelding fra ildkule.net", $body, $body);
      http_response_code(200);
      echo json_encode(array('message' => 'Kontaktskjema mottatt og sendt'));
    }
    catch (Exception $e) {
      http_response_code(500);
      error_log("Something went wrong when trying to contact form to mail");
      echo json_encode(array('error' => 'Beklager, vi kunne ikke motta og sende kontaktskjemaet - prøv igjen ved senere anledning'));
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

$controller = new ContactController(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL, $resourceId = null);
$controller->handleRequest();