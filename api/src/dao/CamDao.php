<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) .DIRECTORY_SEPARATOR. 'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'DaoInterface.php';

class CamDao implements DaoInterface
{

    protected  $db;
    protected  $dbh;
    protected  $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh =  $this->db->getDbh();
    }

    public function findAll()
    {
        $stmt = $this->dbh->query("SELECT * FROM cam");
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Cam');
        return $result;
    }

    public function insert($cam)
    {
        $query = "INSERT INTO cam (cam_name, station_id) VALUES(?,?) ON DUPLICATE KEY UPDATE cam_name = VALUES(cam_name);"; //inserts new records but updates records exists (cam_name and station_id together must be unique in the db)
        $values = array(
            $cam->cam_name, $cam->station->id
        );
        $this->dbh->prepare($query)->execute($values);
        if (!$cam->id) {
            $cam->id = $this->dbh->lastInsertId(); // set the id based on the id generateted in the db
            
            // id will still be missing if update instead of insert - select the id from the db
            if (!$cam->id) { 
                $q = $this->dbh->prepare("SELECT id FROM cam WHERE cam_name=? and station_id = ?");
                $q->execute($values);
                $id = $q->fetchColumn();
                $cam->id = $id;
                print "new cam id" .$cam->id;
            }
        }
     }


    public function findByID($id)
    {
        $query = "SELECT * FROM cam WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new Cam());
        if ($stmt->execute()) {
            return $stmt->fetch();
        }
        return null;
    }

    public function delete($id)
    {
        //TODO - kladd, må nok skrives om.
        $query = "DELETE FROM cam WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if ($stmt->execute()) {
            print 'You deleted ' . $id . ' successfully';
        } else {
            print 'Failed to delete ' . $id . ' from database';
        }
    }
    public function update($id, $confirmed)
    {
        //TODO - kladd - men hvilke attributter trenger vi egentlig å oppdatere fra frontend? blir det på en 'confirmed' så må vi nok få det inn som egen kolonne i meteor. 
        $query = "UPDATE cam SET cam_name = :cam_name; WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if ($stmt->execute()) {
            print 'You updated ' . $id . '. Confirmed is now set to ' . $confirmed;
        } else {
            print 'Failed to update ' . $id;
        }
    }
}
