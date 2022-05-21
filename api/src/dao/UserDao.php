<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'User.php'; 

class UserDao 
{

    protected  $db;
    protected  $dbh;
    protected  $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh =  $this->db->getDbh();
    }

    public function insert($user)
    {
        $query = "INSERT INTO user (username, password) VALUES(?,?);"; 
        $dbh =  $this->db->getDbh();
        $stmt = $dbh->prepare( $query);
        $stmt->bindValue(1, $user->username, PDO::PARAM_STMT);      
        $stmt->bindValue(2, $user->password, PDO::PARAM_STMT);    
        $stmt->execute();
        $user->id = $dbh->lastInsertId();
        return $user;
     }


     public function updateTutorialPerformed($user)
     {
         $query = "update user set tutorial_completed = ? where id = ? ;"; 
         $dbh =  $this->db->getDbh();
         $stmt = $dbh->prepare( $query);
         $stmt->bindValue(1, $user->tutorial_completed, PDO::PARAM_BOOL);      
         $stmt->bindValue(2, $user->id, PDO::PARAM_INT);   
         $stmt->execute();
         return $user;
      }


     public function findByUsername($username)
     {
         $query = "SELECT * FROM user WHERE username = :username;";
         $stmt = $this->dbh->prepare($query);
         $stmt->bindParam(':id', $username);
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
             return $stmt->fetch();
         }
         return null;
     }
}
