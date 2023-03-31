<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'MeteorService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';

/**
 * Handles loading of meteor data source files to data storage
 *
 */
class FileLoadController extends AbstractController
{

  protected function get()
  {
    http_response_code(403);
  }

  protected function post()
  {

    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
    if (!$validRequest)
      return;

    $root_folder = $_SERVER["DOCUMENT_ROOT"] . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR; # root folder for data files
    $data = json_decode(file_get_contents("php://input", true)); # get parameters
    if (isset($_SERVER["HTTP_AUTHORIZATION"])) {
      // Control basic authentication before loading files
      $auth = $_SERVER["HTTP_AUTHORIZATION"];
      $auth_array = explode(" ", $auth);
      $un_pw = explode(":", base64_decode($auth_array[1]));
      $un = $un_pw[0];
      $pw = $un_pw[1];
      // If authenticated, start loading files
      if ($un == "sys_admin" && $pw == "secretpassword") {
        $meteorService = new MeteorService();
        try {
          $meteorService->loadMeteorsFromFiles($root_folder, $data->date_from, $data->date_to);
          http_response_code(200);
          echo json_encode(array('message' => 'Innlasting av data fullfoert'));
        } catch (InvalidArgumentException $e) {
          // date format could be wrong 
          http_response_code(400);
          echo json_encode(array('error' => 'Bad parameters', 'message' => 'Feil i input parameterne'));
        }
      } else {
        http_response_code(401);
        echo json_encode(array('error' => 'Not authorized', 'message' => 'Feil brukernavn eller passord'));
      }
    }
  }


  protected function put()
  {
    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
    if (!$validRequest)
      return;

    $root_folder = $_SERVER["DOCUMENT_ROOT"] . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR; # root folder for data files
    $data = json_decode(file_get_contents("php://input", true)); # get parameters
    if (isset($_SERVER["HTTP_AUTHORIZATION"])) {
      // Control basic authentication before loading files
      $auth = $_SERVER["HTTP_AUTHORIZATION"];
      $auth_array = explode(" ", $auth);
      $un_pw = explode(":", base64_decode($auth_array[1]));
      $un = $un_pw[0];
      $pw = $un_pw[1];
      // If authenticated, start loading files
      if ($un == Config::apiUser && $pw == Config::apiPassword) {
        $meteorService = new MeteorService();
        $meteorService->syncMeteorsFromFiles(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder);
        http_response_code(200);
        echo json_encode(array('message' => 'Innlasting av data fullfoert'));
      }
    } else {
      http_response_code(401);
      echo json_encode(array('error' => 'Not authorized', 'message' => 'Feil brukernavn eller passord'));
    }
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

$controller = new FileLoadController(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL, $resourceId = null);
$controller->handleRequest();