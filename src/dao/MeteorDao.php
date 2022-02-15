<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\dao\DaoInterface.php';

class MeteorDao implements DaoInterface
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
        $stmt = $this->dbh->query("SELECT * FROM meteor limit 15");
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Meteor');
        return $result;
    }

    public function insert($meteor)
    {
        $query = "INSERT INTO meteor (datetimetag,location,camera_confirmed,date,track_startheight,
                                      track_endheight, track_groundtrack, track_course, track_incidence, track_speed,
                                       track_speed_source, fit_error, fit_quality, radiant_ra, radiant_dec,
                                       radiant_ecl_long, radiant_ecl_lat,  radiant_shower, radiant_zenith_attractor, timestamp) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)";
        $values = array(
            $meteor->datetimetag,
            $meteor->location, 
            $meteor->cameraconfirmed,
            ($meteor->date instanceof DateTime) ? $meteor->date->format('Y-m-d H:i:s') : null,
            $meteor->track_startheight,
            $meteor->track_endheight,
            $meteor->track_groundtrack,
            $meteor->track_course,
            $meteor->track_incidence,
            $meteor->track_speed,
            $meteor->track_speed_source,
            $meteor->fit_error,
            $meteor->fit_quality,
            $meteor->radiant_ra,
            $meteor->radiant_dec,
            $meteor->radiant_ecl_long,
            $meteor->radiant_ecl_lat,
            $meteor->radiant_shower,
            $meteor->radiant_zenith_attractor,
            $meteor->timestamp 
        );
        $this->dbh->prepare($query)->execute($values);
    }


    public function findByID($id){
        $query = "SELECT * FROM meteor WHERE id = :id;";
		$stmt = $this->dbh->prepare($query);
		$stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new Meteor());
		if ($stmt->execute()) {
			return $stmt->fetch();
		}
		return null;
    }
    
    public function delete($id){
        //TODO - kladd, må nok skrives om.
        $query = "DELETE FROM meteor WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if($stmt->execute()) {
            print 'You deleted ' . $id . ' successfully';
        } else { 
            print 'Failed to delete ' . $id . ' from database';
        }

    }
    public function update($id, $confirmed){
        //TODO - kladd - men hvilke attributter trenger vi egentlig å oppdatere fra frontend? blir det på en 'confirmed' så må vi nok få det inn som egen kolonne i meteor. 
        $query = "UPDATE meteor SET confirmed = :confirmed; WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if($stmt->execute()) {
            print 'You updated ' . $id . '. Confirmed is now set to ' . $confirmed;
        } else { 
            print 'Failed to update ' . $id;
        }
    }



   
}
