<?php

function myErrorHandler()
{
    //setter php til å returnere kode 500 ved fatal exception
    $last_error = error_get_last();
    if ($last_error && $last_error['type'] == E_ERROR) {
        header("HTTP/1.1 500 Internal Server Error");
    }
    //angir hvilke errors vi vil ha med
    error_reporting(E_ALL);
    //enabler logging i php.ini
    ini_set('log_errors', 1);
    //hindrer php-feil til å bli eksponert ut på web, boolean verdi av/på
    ini_set('display_errors', 0);
    //skriver errors til en logfil, og angir plasseringen av loggen. 
    ini_set('error_log', './php_errors.log');

}

// Set user-defined error handler function. Hvis vi bruker include() eller autoloader så må vi huske å sette funskjonen i filene vi ønsker det.
set_error_handler("myErrorHandler");
?>



