<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'MeteorService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'FileToObjectMapper.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'helpers' . DIRECTORY_SEPARATOR . 'MeteorThumbnailCreator.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';

/**
 * Handles loading of meteor data source files to data storage
 *
 */
class MediaLoadController extends AbstractController
{

  protected function get()
  {
    http_response_code(403);
  }

  protected function post()
  {
    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
    if (!$validRequest) {
      return;
    }

    if (!isset($_SERVER["HTTP_AUTHORIZATION"])) {
      http_response_code(401);
      echo json_encode(array('error' => 'Not authorized', 'message' => 'Feil brukernavn eller passord'));
      return;
    }

    // Control basic authentication (use basic auth for as specified for job initiated by cron)
    $auth = $_SERVER["HTTP_AUTHORIZATION"];
    $auth_array = explode(" ", $auth);
    $un_pw = explode(":", base64_decode($auth_array[1]));
    $un = $un_pw[0];
    $pw = $un_pw[1];

    if (!($un == Config::apiUser && $pw == Config::apiPassword)) {
      http_response_code(401);
      echo json_encode(array('error' => 'Not authorized', 'message' => 'Feil brukernavn eller passord'));
      return;
    }

    // If authenticated, start creating images
    ini_set('max_execution_time', 600);   
    $meteorDataFolder = realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder;
    $imageFolder = realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'img';

    $creator = new MeteorThumbnailCreator($meteorDataFolder, $imageFolder);
    $counts = $creator->createMeteorThumbnails();    

    http_response_code(200);
    echo json_encode(array('message' => 'Loading completed', 'counts' => $counts));
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

$controller = new MediaLoadController(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL, $resourceId = null);
$controller->handleRequest();