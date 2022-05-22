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

$controller = new ContactController(AbstractController::AUTHENTICATION_IGNORE , AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_IGNORE, $resourceId = null);
$controller->handleRequest();