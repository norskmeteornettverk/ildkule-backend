<?php


session_start();

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'FrontController.php';


 // Allow from any origin
 if (isset($_SERVER['HTTP_ORIGIN'])) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400');    // cache for 1 day
    header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT'); 
    header( 'Access-Control-Allow-Headers: Content-Type, x-requested-with'); 
  }
 
$frontController = new FrontController();

$frontController->get('/api/search/$query', '/api/search.php');
$frontController->get('/api/meteors', '/api/meteors.php');
$frontController->get('/api/meteors/load', '/api/load.php');
$frontController->get('/api/meteor/$id', '/api/meteor.php');
$frontController->put('/api/meteor/$id', '/api/meteor.php');
$frontController->post('/api/login', '/api/login.php');
$frontController->get('/api/users', '/api/users.php');
$frontController->get('/api/filter', '/api/filter.php');
$frontController->post('/api/classify', '/api/classify.php');
$frontController->get('/api/report/$report', '/api/report.php');


/*
// Dynamic GET. Example with 1 variable
// The $id will be available in user.php
get('/user/$id', 'user.php');

// Dynamic GET. Example with 2 variables
// The $name will be available in user.php
// The $last_name will be available in user.php
get('/user/$name/$last_name', 'user.php');

// Dynamic GET. Example with 2 variables with static
// In the URL -> http://localhost/product/shoes/color/blue
// The $type will be available in product.php
// The $color will be available in product.php
get('/product/$type/color/:color', 'product.php');

// Dynamic GET. Example with 1 variable and 1 query string
// In the URL -> http://localhost/item/car?price=10
// The $name will be available in items.php which is inside the views folder
get('/item/$name', 'views/items.php');


// ##################################################
// ##################################################
// ##################################################
// any can be used for GETs or POSTs

// For GET or POST
// The 404.php which is inside the views folder will be called
// The 404.php has access to $_GET and $_POST
any('/404','views/404.php');
*/