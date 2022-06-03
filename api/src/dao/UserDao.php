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
        $query = "update user set tutorial_completed = ?, user_level = ? where id = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->tutorial_completed, PDO::PARAM_BOOL);
        $stmt->bindValue(2, $user->user_level, PDO::PARAM_INT);
        $stmt->bindValue(3, $user->id, PDO::PARAM_INT);
        $stmt->execute();
        return $user;
    }

    public function  updateRole($user)
    {
        $query = "update user set role = ? where id = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->role, PDO::PARAM_STR);
        $stmt->bindValue(2, $user->id, PDO::PARAM_INT);        
        $stmt->execute();
        return $user;
    }

    public function  updateLevel($user)
    {
        $query = "update user set user_level = ? where id = ? ;";
        $dbh = $this->db->getDbh();
        $stmt = $dbh->prepare($query);
        $stmt->bindValue(1, $user->user_level, PDO::PARAM_INT);
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


    public function findAll($page = -1, $lim = 10, $orderBy = null, $order = null)
    {
        
        $stmt = null;        
        $query = "
        SELECT 
        user.*
        ,COALESCE(ratings.ratings, 0) ratings
        ,COALESCE(ratings.positive_ratings, 0) as positive_ratings
        ,COALESCE(ratings.negative_ratings, 0) as negative_ratings   
        FROM user 
        left outer join 
        (
            select user_review.user_id, 
            sum(case when user_review.confirmed = 1 then 1 else 0 end) as positive_ratings,
            sum(case when user_review.confirmed = 0 then 1 else 0 end) as negative_ratings,
            count(*) ratings 
            from user_review 
            group by user_review.user_id
        ) as ratings on user.id  = ratings.user_id ";

        $orderSQL = "order by ";

        if (!is_null($orderBy) && !is_null($order)) {            

            switch ($orderBy) {
                case "username":
                    $orderSQL = $orderSQL . " user.username ";
                    break;
                case "role":
                    $orderSQL = $orderSQL . " user.role ";
                    break;
                case "user_level":
                    $orderSQL = $orderSQL . " user.user_level ";
                    break;
                case "tutorial_completed":
                    $orderSQL = $orderSQL . " user.tutorial_completed ";
                    break;
                case "confirmed":
                    $orderSQL = $orderSQL . " user.confirmed ";
                    break;
                case "ratings":
                    $orderSQL = $orderSQL . " COALESCE(ratings.ratings, 0)  ";
                    break;               
                default:
                    $orderSQL = $orderSQL . " user.create_time ";
                }
            switch ($order) {
                case "asc":
                    $orderSQL = $orderSQL . " asc ";
                    break;
                case "desc":
                    $orderSQL = $orderSQL . " desc ";
                    break;
                default:
                    $orderSQL = $orderSQL . " desc ";
                }
        }                     

        $query = $query . $orderSQL;
        $query = $query . " LIMIT ? OFFSET ? ";

        $stmt = $this->dbh->prepare($query);
        $stmt->bindValue(1, $lim, PDO::PARAM_INT);
        $stmt->bindValue(2, 0, PDO::PARAM_INT);    

        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'User');

        return $result;
    }
}
