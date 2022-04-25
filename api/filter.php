<?php

ini_set('display_errors', 1);

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'MeteorController.php';

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'GET') {

  $stationName = null;
  $year = null;
  $meteorClass = null;


  
  if(isset($_GET['stationName'])) {
    $stationName = $_GET['stationName'];  }
  if(isset($_GET['year'])) {
    $year = $_GET['year'];   }
  if(isset($_GET['meteorClass'])) {
    $meteorClass = $_GET['meteorClass'];  
  }

  $controller = new MeteorController();
  $json = $controller->filter($stationName, $year, $meteorClass);
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
};
