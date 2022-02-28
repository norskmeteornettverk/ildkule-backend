<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) .DIRECTORY_SEPARATOR. 'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'DaoInterface.php';

class StationDao implements DaoInterface
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
        $stmt = $this->dbh->query("SELECT * FROM station");
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Station');
        return $result;
    }

    public function insert($station)
    {
        $query = "INSERT INTO station (station_name) VALUES(?) ON DUPLICATE KEY UPDATE station_name = VALUES(station_name);"; //inserts new records but updates records exists (station_name is unique)
        $values = array(
            $station->station_name
        );
        $this->dbh->prepare($query)->execute($values);
        
        if (!$station->id) {
            $station->id = $this->dbh->lastInsertId();  // set the id based on the id generateted in the db

            // id will still be missing if update instead of insert - select the id from the db
            if (!$station->id) {
                $q = $this->dbh->prepare("SELECT id FROM station WHERE station_name=?");
                $q->execute($values);
                $id = $q->fetchColumn();
                $station->id = $id;
            }
        }
    }


    public function findByID($id)
    {
        $query = "SELECT * FROM station WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new Station());
        if ($stmt->execute()) {
            return $stmt->fetch();
        }
        return null;
    }

    public function delete($id)
    {
        //TODO - kladd, må nok skrives om.
        $query = "DELETE FROM station WHERE id = :id;";
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
        $query = "UPDATE station SET station_name = :station_name; WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if ($stmt->execute()) {
            print 'You updated ' . $id . '. Confirmed is now set to ' . $confirmed;
        } else {
            print 'Failed to update ' . $id;
        }
    }
}
