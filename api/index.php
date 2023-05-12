<?php
//require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'handlers' . DIRECTORY_SEPARATOR . 'ErrorHandler.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'bootstrap.php';
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
  header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
  header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT, PATCH'); 
  http_response_code(200);
  die();
}
$frontController = new FrontController();
/* The following section routes requests to the correct controller */
/* User functions */
$frontController->post(	'/api/user'	                            ,'/api/src/controllers/resourcecontrollers/UserController.php'                  ); # Post a new user
$frontController->get(	'/api/user/$id'	                        ,'/api/src/controllers/resourcecontrollers/UserController.php'                  ); # Get user
$frontController->post(	'/api/login'	                          ,'/api/src/controllers/resourcecontrollers/UserLoginController.php'             ); # Post a new login 
$frontController->put(	'/api/user/$id/tutorialcomplete'	      ,'/api/src/controllers/resourcecontrollers/UserTutorialController.php'          ); # Update users tutorial complete status
$frontController->put(	'/api/user/$id/password'	              ,'/api/src/controllers/resourcecontrollers/UserPasswordController.php'          ); # Update password
$frontController->get(	'/api/user/$id/details'	                ,'/api/src/controllers/resourcecontrollers/UserDetailsController.php'           ); # Get user details
$frontController->put(	'/api/passwordresetrequest'             ,'/api/src/controllers/resourcecontrollers/UserPasswordResetController.php'     ); # Update password
$frontController->post(	'/api/passwordresetrequest'             ,'/api/src/controllers/resourcecontrollers/UserPasswordResetController.php'     ); # Post a password reset request
/* User administration */
$frontController->put(	'/api/user/$id/userlevel'	              ,'/api/src/controllers/resourcecontrollers/UserLevelController.php'             ); # Update the user's level
$frontController->put(	'/api/user/$id/userrole'	              ,'/api/src/controllers/resourcecontrollers/UserRoleController.php'              ); # Update the user's role
$frontController->put(	'/api/user/$id/active'	                ,'/api/src/controllers/resourcecontrollers/UserActiveController.php'            ); # Update the user's active status
$frontController->patch('/api/user/$id'	                        ,'/api/src/controllers/resourcecontrollers/UserController.php'                  ); # Update provided fields of a user
$frontController->get(	'/api/users'	                          ,'/api/src/controllers/resourcecontrollers/UserListController.php'              ); # List users
/* Meteor functions */
$frontController->get(	'/api/meteors'	                        ,'/api/src/controllers/resourcecontrollers/MeteorListController.php'            ); # List meteors
$frontController->get(	'/api/meteor/$id'	                      ,'/api/src/controllers/resourcecontrollers/MeteorController.php'                ); # Get meteor
$frontController->post(	'/api/meteor/$id/review'                ,'/api/src/controllers/resourcecontrollers/MeteorReviewController.php'          ); # Post review 
/* Meteor administration */
$frontController->put(	'/api/meteor/$id'	                      ,'/api/src/controllers/resourcecontrollers/MeteorController.php'                ); # Update meteor
$frontController->put(	'/api/meteor/$id/classification'	      ,'/api/src/controllers/resourcecontrollers/MeteorClassificationController.php'  ); # Update meteor classification
$frontController->get(	'/api/insight/$reportname'              ,'/api/src/controllers/resourcecontrollers/InsightDashboardController.php'      ); # Get insight dashboard
$frontController->get(	'/api/meteorboard'                      ,'/api/src/controllers/resourcecontrollers/MeteorAdminBoardController.php'      ); # List meteors with admin details
/* Various functions */
$frontController->post(	'/api/meteorload'	                      ,'/api/src/controllers/resourcecontrollers/FileLoadController.php'              ); # Post a loading request 
$frontController->post(	'/api/reportmeteor'	                    ,'/api/src/controllers/resourcecontrollers/ReportMeteorController.php'          ); # Post a seen meteor
$frontController->post(	'/api/contact'	                        ,'/api/src/controllers/resourcecontrollers/ContactController.php'               ); # Post a contact form
$frontController->post(	'/api/stationlog'	                      ,'/api/src/controllers/resourcecontrollers/StationLogController.php'            ); # Post a log from a meteor station
$frontController->get(	'/api/stationlog'	                      ,'/api/src/controllers/resourcecontrollers/StationLogController.php'            ); # List log
// return 404 if the routing has not picked up the request
http_response_code(404);
header('Content-Type: application/json; charset=utf-8');
echo json_encode(array('error' => "Resource or method doesn't exists", 'message' => 'Ressursen eller funksjonen eksisterer ikke'));

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