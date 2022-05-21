
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

        $user = new User($username, $password);
        $userDao = new UserDao();
        $userDao->insert($user);       
        return $user;        
    }

    public function login(string $username, string $password)
    {
        $userDao = new UserDao();
        $user = $userDao->findByUsername($username);
        if (password_verify($password, $user->password)){
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
        $user->turtorial_completed = $isCompleted;
        $userDao->updateTutorialPerformed($user);
    }

    public function getUser()
    {
        throw new Exception('Not implemented');
    }

    public function changePassword()
    {
        throw new Exception('Not implemented');
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