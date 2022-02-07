<?php 

ini_set('display_errors', 1);

require_once realpath($_SERVER["DOCUMENT_ROOT"]).'\config.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).'\src\models\Meteor.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).'\src\dao\DatabaseConnection.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).'\src\dao\MeteorDAO.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).'\src\controllers\Controller.php'; 

header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");

if ($_SERVER['REQUEST_METHOD'] === 'GET') {  
  $controller = new Controller();  
  print ($controller->getAllMeteors());  
};