<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'UserReview.php'; 

class UserReviewDao 
{

    protected  $db;
    protected  $dbh;
    protected  $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh =  $this->db->getDbh();
    }

    

    public function findByMeteorID($id)
    {
    

        $stmt = $this->dbh->prepare("SELECT * FROM user_review WHERE meteor_id = :id;");
        $stmt->bindParam(':id', $id);
        $stmt->execute();
        $result = array();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'UserReview');
        if (isset($result)){
            return $result;
        } else {
            return array();
        }        
    }
}
