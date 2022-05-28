
<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'User.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'ObservationCamData.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Cam.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Station.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'MeteorDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'FileToObjectMapper.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'StationDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'CamDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'ObservationCamDataDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'UserReviewDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'UserDao.php';


class UserService
{

    public function createNewUser(string $username, string $password)
    {

        $user = new User();
        $user->password = $password;
        $user->username = $username;
        $userDao = new UserDao();
        $userDao->insert($user);
        return $user;
    }

    public function login(string $username, string $password)
    {
        $userDao = new UserDao();
        $user = $userDao->findByUsername($username);
        if (password_verify($password, $user->password)) {
            return true;
        }
        else {
            return false;
        }

    }

    public function tutorialPerformed(int $userId, bool $isCompleted)
    {
        $userDao = new UserDao();
        $user = $userDao->findById($userId);
        $user->tutorial_completed = $isCompleted;
        if ($user->user_level == 0 or is_null($user->user_level)) $user->user_level = 1;
        $userDao->updateTutorialPerformed($user);
    }

    public function getUserById(int $id)
    {
        $userDao = new UserDao();
        $user = $userDao->findById($id);
        return $user;
    }

    public function changePassword()
    {
        throw new Exception('Not implemented');
    }



    // send mail to user with password reset link including random id -  find if user exists, if user doesnt exist dont tell!
    public function requestPasswordReset(string $email)
    {
        //Check if user exists
        $userDao = new UserDao();
        $user = $userDao->findByUsername($email);

        //send mail to user with password reset token (if user exists) 
        if ($user) {

            // create unique password reset token so that we can identify the right user
            $user->password_reset_token = bin2hex(random_bytes(20));
            $user->password_reset_request_time = time();
            $userDao->updatePasswordResetToken($user);

            //include script that contains function that sends mail - dependant on phpmailer       
            require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . "phpmailer" . DIRECTORY_SEPARATOR . "mailer.php";

            $body =
                '
            Hei!<br/>
            Vi har mottatt forespørsel om å resette ditt passord på ildkule.net.<br/>
            Om du ikke har gjort dette, kan du set bort i fra denne e-posten.<br/>
            Om du vil resette passordet, <a href="'.Config::frontUrl.'/resetpassword?passwordResetId=' . $user->password_reset_token . '"> besøker du oss her </a><br/>
            <br/>
            Hilsen ildkule.net            
            ';
            sendMeteorMail($email, "Forespørsel om nullstilling av passordet er mottatt hos ildkule.net", $body, $body);

            return true;
        }
        return false;
    }

    public function resetPassword(string $resetID, string $email, string $newPassword)
    {
        //Check if user exists
        $userDao = new UserDao();
        $userFound = $userDao->findByUsername($email);
 
        if ($userFound) {
            $userFound->password = $newPassword;

            //Check if reset token provided is correct AND that the reset token is actuelly set to something
            if (!empty($userFound->password_reset_token) && strcmp($userFound->password_reset_token, $resetID) == 0) {
                $userDao->setPasswordAndClearResetToken($userFound);
                return true;
            }
        }
        return false;
    }


    public function listUsers()
    {
        throw new Exception('Not implemented');
    }

    public function confirmUser()
    {
        throw new Exception('Not implemented');
    }

    public function inActivateUser()
    {
        throw new Exception('Not implemented');
    }

    public function changeUserLevel()
    {
        throw new Exception('Not implemented');
    }

    public function changeUserRole()
    {
        throw new Exception('Not implemented');
    }

}