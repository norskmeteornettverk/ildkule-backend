<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'MeteorService.php';



class MeteorAdminBoardController extends AbstractController
{

  protected function get()
  {

    $validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_PERFORM_CONTROL, AbstractController::USER_ROLE_ADMIN, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_IGNORE);
    if (!$validRequest)  return;
    
    $meteorService = new MeteorService();

    if (isset($_GET['page'])) {
      $json = $meteorService->getAllMeteors($_GET['page']);
    }
    else {
      $json = $meteorService->getAllMeteors();
    }

    http_response_code(200);
    header('Content-Type: application/json; charset=utf-8');

    if ($json === false) {
      // Avoid echo of empty string (which is invalid JSON), and
      // JSONify the error message instead:
      $json = json_encode(["jsonError" => json_last_error_msg()]);
      if ($json === false) {
        // This should not happen, but we go all the way now:
        $json = '{"jsonError":"unknown"}';
      }
      // Set HTTP response status code to: 500 - Internal Server Error
      http_response_code(500);
    }
    echo $json;
    ;

  }

  protected function post()
  {
    http_response_code(403);
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

$controller = new MeteorAdminBoardController(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL, $resourceId = null);
$controller->handleRequest();