<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'User.php';


class UserDao

{

    protected $db;
    protected $dbh;
    protected $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh = $this->db->getDbh();
    }

    public function insert($user)
    {
        $query = "INSERT INTO user (username, password) VALUES(?,?);";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->username, PDO::PARAM_STMT);
        $stmt->bindValue(2, $user->password, PDO::PARAM_STMT);
        $stmt->execute();
        $user->id = $dbh->lastInsertId();
        return $user;
    }


    public function updateTutorialPerformed($user)
    {
        $query = "update user set tutorial_completed = ? where id = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->tutorial_completed, PDO::PARAM_BOOL);
        $stmt->bindValue(2, $user->id, PDO::PARAM_INT);
        $stmt->execute();
        return $user;
    }


    public function updatePasswordResetToken($user)
    {
        $query = "update user set password_reset_token = ?, password_reset_request_time = ?  where username = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->password_reset_token, PDO::PARAM_STR);
        $stmt->bindValue(2, $user->password_reset_request_time, PDO::PARAM_STR);
        $stmt->bindValue(3, $user->username, PDO::PARAM_STR);
        $stmt->execute();
        return $user;
    }

    public function setPasswordAndClearResetToken($user)
    {
        $query = "update user set password_reset_token = null, password = ?  where username = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->password, PDO::PARAM_STR);
        $stmt->bindValue(2, $user->username, PDO::PARAM_STR);
        $stmt->execute();
        return $user;
    }


    public function findByUsername($username)
    {
        $query = "SELECT * FROM user WHERE username = :username;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':username', $username);
        $stmt->setFetchMode(PDO::FETCH_INTO, new User());
        if ($stmt->execute()) {
            return $stmt->fetch();
        }
        return null;
    }

    public function findById($id)
    {
        $query = "SELECT * FROM user WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new User());
        if ($stmt->execute()) {
            return $stmt->fetch(); // returns false if no records found
        }
        return null;
    }
}
