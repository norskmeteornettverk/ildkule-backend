<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';

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

    public function getCount()
    {
        $stmt = $this->dbh->query("SELECT count(id) as num FROM meteor");
        $stmt->execute();
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row['num'];
    }

    public function findAll($page = -1, $lim = 10)
    {
        $stmt = null;
        if ($page <= -1){            
            $query = "SELECT * FROM meteor  order by meteor.date desc LIMIT ? OFFSET ? ";
            $stmt = $this->dbh->prepare( $query);
            $stmt->bindValue(1, $lim, PDO::PARAM_INT);        
            $stmt->bindValue(2, 0, PDO::PARAM_INT);                           
        } else {              
            $query = "SELECT * FROM meteor  order by meteor.date desc LIMIT ? OFFSET ? ";
            $stmt = $this->dbh->prepare( $query);
            $stmt->bindValue(1, $lim, PDO::PARAM_INT);        
            $stmt->bindValue(2, ($page-1)*((int)$lim), PDO::PARAM_INT);                          
        }        
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Meteor');
        return $result;
    }

    public function insert($meteor)
    {
        $query = "INSERT INTO meteor (
            datetimetag,
            location,
            camera_confirmed,
            date,
            track_startheight,
            track_endheight, 
            track_groundtrack, 
            track_course, 
            track_incidence, 
            track_speed,
            track_speed_source, 
            track_startlat, 
            track_startlong, 
            track_endlat, 
            track_endlong, 
            fit_error, 
            fit_quality, 
            radiant_ra, 
            radiant_dec,
            radiant_ecl_long, 
            radiant_ecl_lat,  
            radiant_shower, 
            radiant_zenith_attractor, 
            timestamp)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON DUPLICATE 
            KEY UPDATE 
            
            datetimetag                     = VALUES(datetimetag                )
            ,location                       = VALUES(location                   )           
            ,camera_confirmed               = VALUES(camera_confirmed           )        
            ,date                           = VALUES(date                       )      
            ,track_startheight              = VALUES(track_startheight          )    
            ,track_endheight                = VALUES(track_endheight            )  
            ,track_groundtrack              = VALUES(track_groundtrack          )
            ,track_course                   = VALUES(track_course               )
            ,track_incidence                = VALUES(track_incidence            )
            ,track_speed                    = VALUES(track_speed                )
            ,track_speed_source             = VALUES(track_speed_source         )
            ,track_startlat                 = VALUES(track_startlat             )
            ,track_startlong                = VALUES(track_startlong            )
            ,track_endlat                   = VALUES(track_endlat               )
            ,track_endlong                  = VALUES(track_endlong              )
            ,fit_error                      = VALUES(fit_error                  )
            ,fit_quality                    = VALUES(fit_quality                )
            ,radiant_ra                     = VALUES(radiant_ra                 )
            ,radiant_dec                    = VALUES(radiant_dec                )
            ,radiant_ecl_long               = VALUES(radiant_ecl_long           )
            ,radiant_ecl_lat                = VALUES(radiant_ecl_lat            )
            ,radiant_shower                 = VALUES(radiant_shower             )
            ,radiant_zenith_attractor       = VALUES(radiant_zenith_attractor   )
            ,timestamp                      = VALUES(timestamp                  )


            ;                                      
                                      ";
        $values = array(
            $meteor->datetimetag,
            $meteor->location,
            $meteor->camera_confirmed,
            ($meteor->date instanceof DateTime) ? $meteor->date->format('Y-m-d H:i:s') : null,
            $meteor->track_startheight,
            $meteor->track_endheight,
            $meteor->track_groundtrack,
            $meteor->track_course,
            $meteor->track_incidence,
            $meteor->track_speed,
            $meteor->track_speed_source,
            $meteor->track_startlat,
            $meteor->track_startlong,
            $meteor->track_endlat,
            $meteor->track_endlong,
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

        if (!$meteor->id) {
            $meteor->id = $this->dbh->lastInsertId(); // set the id based on the id generateted in the db
            
            // id will still be missing if update instead of insert - select the id from the db
            if (!$meteor->id) { 
                $q = $this->dbh->prepare("SELECT id FROM meteor WHERE meteor.datetimetag  = ?");
                $q->execute(array( $meteor->datetimetag));
                $id = $q->fetchColumn();
                $meteor->id = $id;                
            }
        }       
    }


    public function findByID($id)
    {
        $query = "SELECT * FROM meteor WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new Meteor());
        if ($stmt->execute()) {
            return $stmt->fetch();
        }
        return null;
    }

    public function search($search)
    {
        $stmt  = $this->dbh->prepare("SELECT * FROM meteor WHERE location like ? or datetimetag like ?  order by meteor.date desc");
        $stmt->execute(array('%' . $search . '%','%' . $search . '%'));
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Meteor');
        return $result;
    }

    public function filter($stationName, $year, $meteorClass)
    {      
        $stationNameFilterList = [];
        $yearFilterList = [];
        $meteorClassFilterList = [];

        $query = "select meteor.* from meteor where 1=1";

        $where = [];       

        if (!empty($stationName)) {
            $stationNameFilterList = explode(",", $stationName, 10);
            $query = $query . " and meteor.id in (  SELECT d.meteor_id from  observation_cam_data d inner join cam c on d.cam_id = c.id inner join station s on c.station_id = s.id where s.station_name in (";
            foreach ($stationNameFilterList as $index => $stationName) {
                $query = $query . "?";
                array_push($where, array($stationName, "string"));
                if ($index !== array_key_last($stationNameFilterList))
                    $query = $query . ",";
            }
            $query = $query .  ") )";
        }

        if (!empty($year)) {
            $yearFilterList = explode(",", $year, 10);
            $query = $query . " AND   year(date) in (";
            foreach ($yearFilterList as $index => $year) {  
                $query = $query .  "?";
                array_push($where, array( $year, "int"));              
                if ($index !== array_key_last($yearFilterList))
                    $query = $query . ",";
            }
            $query = $query .  ")";
        }

        if (!empty($meteorClass)) {
            $meteorClassFilterList = explode(",", $meteorClass, 10);
            $query = $query . " AND   (case when track_endheight < 40 and track_endheight is not null then 'Meteorittkandidat' when track_endheight is not null then 'Krysspeilet' else 'Upeilet' end   in (  ";
            foreach ($meteorClassFilterList as $index => $meteorClass) {  
                $query = $query . "?";
                array_push($where, array($meteorClass, "string"));             
                if ($index !== array_key_last($meteorClassFilterList))
                    $query = $query . ",";
            }
            $query = $query .  "))";        
        }

        $query = $query . " order by meteor.datetimetag desc limit 100"; 

        $sth = $this->dbh->prepare($query);

        for ($i = 0; $i < count($where); $i++)  {
            if ($where[$i][1] == "string" ){               
                $sth->bindParam($i+1,$where[$i][0], PDO::PARAM_STR);                
            }

            if ($where[$i][1] == "int" ){               
                $sth->bindParam($i+1,$where[$i][0], PDO::PARAM_INT);                
            }                     


        }  

        $sth->execute();

        $data  = $sth->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'Meteor');

        return $data;
    }

    public function delete($id)
    {
        //TODO - kladd, må nok skrives om.
        $query = "DELETE FROM meteor WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        if ($stmt->execute()) {
            print 'You deleted ' . $id . ' successfully';
        } else {
            print 'Failed to delete ' . $id . ' from database';
        }
    }
    public function update($id, $confirmed)
    {
        //TODO - kladd - men hvilke attributter trenger vi egentlig å oppdatere fra frontend? blir det på en 'confirmed' så må vi nok få det inn som egen kolonne i meteor. 
        $query = "UPDATE meteor SET confirmed = :confirmed; WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        if ($stmt->execute()) {
            print 'You updated ' . $id . '. Confirmed is now set to ' . $confirmed;
        } else {
            print 'Failed to update ' . $id;
        }
    }
}
