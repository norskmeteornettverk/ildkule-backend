<?php

session_start();
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
#error_reporting(E_ALL);

 // Allow from any origin
 if (isset($_SERVER['HTTP_ORIGIN'])) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400');    // cache for 1 day
    header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT'); 
    header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
 
  }
header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT'); 

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'FrontController.php';
$frontController = new FrontController();

/* The following section routes requests to the correct controller */
$frontController->post(      '/api/meteors/load',       '/api/LoadController.php'               );  # Loading data from files
$frontController->get(      '/api/meteors',             '/api/MeteorsController.php'            ); # Get all loaded meteors
$frontController->get(      '/api/search/$query',       '/api/SearchController.php'             ); # Get all meteors by search string
$frontController->get(      '/api/filter',              '/api/MeteorFilterController.php'       ); # Get all meteors by filtering
$frontController->get(      '/api/meteor/$id',          '/api/MeteorController.php'             ); # Get single meteor
$frontController->put(      '/api/meteor/$id',          '/api/MeteorController.php'             ); # Update meteor - e.g. update verification on meteor
$frontController->post(     '/api/classify',            '/api/MeteorReviewController.php'       ); # Review meteor
$frontController->post(     '/api/user/new',            '/api/NewUserController.php'            ); # Register new user
$frontController->post(     '/api/login',               '/api/LoginController.php'              ); # Login user
$frontController->get(      '/api/users',               '/api/UsersController.php'              ); # Get all users
$frontController->get(      '/api/user',                '/api/UserController.php'               ); # Get user
$frontController->post(     '/api/user/myreviews',      '/api/MyReviewsController.php'          );  # Get users' reviews
$frontController->post(     '/api/user/myreviews',      '/api/MyReviewsController.php'          );  # Get users' reviews
$frontController->get(      '/api/report/$report',      '/api/ReportController.php'             ); # Get report

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
  header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
  header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT'); 
  http_response_code(200);
  die();
}

$frontController->any(      '/404',                     '/api/404.php'                          ); # 404


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