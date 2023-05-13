<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'LogService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';

/**
 * Handles the logging for the meteor stations
 *
 */
class StationLogController extends AbstractController
{

  protected function get()
  {
    $service = new LogService();
    $result = $service->lastSeen();
    echo json_encode($result);
  }

  protected function post()
  {
    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
    if (!$validRequest)
      return;
    $data = json_decode(file_get_contents("php://input", true));

    try {
      switch (true) {
        case array_key_exists('HTTP_AUTHORIZATION', $_SERVER):
          $authHeader = $_SERVER['HTTP_AUTHORIZATION'];
          break;
        case array_key_exists('Authorization', $_SERVER):
          $authHeader = $_SERVER['Authorization'];
          break;
        default:
          $authHeader = null;
          break;
      }
      preg_match('/Bearer\s(\S+)/', $authHeader, $matches);
      if (!isset($matches[1])) {
        http_response_code(401);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(array('error' => 'Authorization failed'));
        return;
      }

      if (get_bearer_token() != Config::log_key) {
        http_response_code(401);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(array('error' => 'Authorization failed'));
        return;
      }

    }
    catch (Exception $e) {
      return false;
    }

    $service = new LogService();
    $result = $service->log($data);

    if ($result) {
      http_response_code(200);
      header('Content-Type: application/json; charset=utf-8');
      echo json_encode(array('msg' => 'Success!'));
      return;
    }
    else {
      http_response_code(500);
      header('Content-Type: application/json; charset=utf-8');
      echo json_encode(array('error' => 'Failed logging to db'));
      return;
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

$controller = new StationLogController(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL, $resourceId = null);
$controller->handleRequest();