<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);

 // Allow from any origin
 if (isset($_SERVER['HTTP_ORIGIN'])) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400');    // cache for 1 day
    header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT,PATCH'); 
    header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
 
  }
header( 'Access-Control-Allow-Headers: Authorization, Accept-Encoding, Accept-Language,Access-Control-Request-Headers, Origin, Referer,  Content-Type, x-requested-with, Accept, DNT, Referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site, User-Agent'); 
header( 'Access-Control-Allow-Methods: POST, GET, OPTIONS, DELETE, PUT,PATCH'); 

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'FrontController.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'security' . DIRECTORY_SEPARATOR . 'Security.php';

//Load Composer's autoloader
realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'vendor/autoload.php';


// end of file