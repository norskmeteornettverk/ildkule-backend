<?php
//Import PHPMailer classes into the global namespace
//These must be at the top of your script, not inside a function
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

//Load Composer's autoloader

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'vendor' . DIRECTORY_SEPARATOR . 'autoload.php' ;

function sendMeteorMail(string $email, string $subject, string $body , string $altbody)
{
    //Create an instance; passing `true` enables exceptions    
    $mail = new PHPMailer(true);
    try {
        //Server settings
        $mail->SMTPDebug = SMTP::DEBUG_SERVER; //Enable verbose debug output
        $mail->CharSet = 'UTF-8';
        $mail->isSMTP(); //Send using SMTP
        $mail->Host = Config::emailServer; //Set the SMTP server to send through
        $mail->SMTPAuth = true; //Enable SMTP authentication
        $mail->Username = Config::emailForMeteorReport; //SMTP username
        $mail->Password = Config::pwForMeteorReport; //SMTP password
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS; //Enable implicit TLS encryption
        $mail->Port = 465; //TCP port to connect to; use 587 if you have set `SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS`
        $mail->setLanguage('nb', '\vendor\phpmailer\phpmailer\language'); // Language settings - nb = norsk bokmål, fjernes denne er standard engelsk

        $mail->setFrom(Config::emailForMeteorReport, 'Norsk Meteornettverk'); //From
        $mail->addAddress($email, 'Norsk Meteornettverk'); //Add a recipient
        //$mail->addCC('cc@example.com');

        //Attachments
        //$mail->addAttachment('/tmp/imagename.jpg', 'renamethefilename.jpg');    //Add attachments - KANSKJE GENERERE EN RAPPORT INN I EN FIL SOM LEGGES VED EPOSTEN?

        //Content
        $mail->isHTML(true); //Set email format to HTML
        $mail->Subject = $subject;
        $mail->Body =  $body;
        $mail->AltBody =  $altbody;

        $mail->send();
    }
    catch (Exception $e) {
        echo "Meldingen kunne ikke sendes. Mailer Error: {$mail->ErrorInfo}";
    }
}