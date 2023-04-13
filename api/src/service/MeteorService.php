<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
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
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'helpers' . DIRECTORY_SEPARATOR . 'DataAccessHelper.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';


/**
 * Class MeteorService
 * 
 * Provides methods to interact with meteor data.
 * 
 */
class MeteorService
{
    public function loadMeteorsFromFiles($root_folder, $date_from, $date_to)
    {
        if (!$this->validateDate($date_from, 'Ymd') || !$this->validateDate($date_to, 'Ymd'))
            throw new InvalidArgumentException('Provided dates are not valid: ' . $date_from . '-' . $date_to);

        set_time_limit(600);
        $mapper = new FileToObjectMapper($root_folder, $date_from, $date_to);
        $meteors = $mapper->map();
        $meteorDao = new MeteorDao();
        $stationDao = new StationDao();
        $camDao = new CamDao();
        $camDataDao = new ObservationCamDataDao();
        foreach ($meteors as $meteor) {
            $meteorDao->insert($meteor);
            if ($meteor->observation_cam_data) {
                foreach ($meteor->observation_cam_data as $cam_data) {
                    if ($cam_data->cam) {
                        if ($cam_data->cam->station) {
                            $stationDao->insert($cam_data->cam->station);
                        }
                        $camDao->insert($cam_data->cam);
                        $camDataDao->insert($cam_data);
                    }
                }
            }
        }
    }

    private function setMeteorAsMissingInSource($meteor_id)
    {
        $meteorDao = new MeteorDao();
        $meteor = $meteorDao->findByID($meteor_id);

        if ($meteor) {
            $meteor->source_removed = 1;
            $meteorDao->updateByObject($meteor);
        }
    }

    /**
     * Syncs meteors from the source folder to the database.
     *
     * @return array An associative array containing the following keys and their
     *               respective values:
     *               - 'found_in_source': The number of meteors found in the source.
     *               - 'found_in_database': The number of meteors found in the database.
     *               - 'missing_in_database': The number of meteors missing in the database.
     *               - 'missing_in_source': The number of meteors missing in the source.
     */
    public function syncMeteorsFromFiles()
    {
        $cut_off = "2015-01-01 00:00:00"; // Meteors updated after this date will be updated (checks source and database)

        // Retrieve meteor folder names from source
        $m = new FileToObjectMapper(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR, "19000101", "20990101");
        $sourceMeteors = $m->getMeteorFoldersUpdatedAfterDate(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder, $cut_off, [], true);
        $badMeteorFolders = $m->getMeteorFoldersUpdatedAfterDate(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_wrong_folder, $cut_off, [], true);

        $sourceMeteors = array_merge($sourceMeteors, $badMeteorFolders);

        // Retrieve source folders names of meteors in the database
        $date = date("Y-m-d H:i:s", strtotime($cut_off));
        $dataAccessHelper = new DataAccessHelper();
        $conditions = [">=" => ["create_time", $date]];
        $databaseResults = $dataAccessHelper->getMiscData("meteor", array("id", "create_time", "source_folder"), $conditions);

        $databaseMeteors = array();
        foreach ($databaseResults as $row) {
            $row["source_folder"] = str_replace("/", DIRECTORY_SEPARATOR, str_replace("\\", DIRECTORY_SEPARATOR, $row["source_folder"]));
            $databaseMeteors[] = $row["source_folder"];
        }

        $databaseMeteors = array_filter($databaseMeteors); // Remove empty values - some meteors have no source folder due to being manually added

        // Find the meteors in the source array that are not in the database array
        $missingInDatabase = array_diff($sourceMeteors, $databaseMeteors);

        // Find the meteors in the database array that are not in the source array
        $missingInSource = array_diff($databaseMeteors, $sourceMeteors);

        // Count the number of meteors in each category
        $foundInSourceCount = count($sourceMeteors);
        $foundInDatabaseCount = count($databaseMeteors);
        $missingInDatabaseCount = count($missingInDatabase);
        $missingInSourceCount = count($missingInSource);

        // Insert meteors missing in the database
        $slicedMeteorFolderList = array_slice($missingInDatabase, 0, 5000); // Limit to avoid timeouts
        rsort($slicedMeteorFolderList); // Sort in descending order to ensure that the most recent meteors are inserted first
        $this->insertMeteors($slicedMeteorFolderList);

        // Update meteors missing in the source from the database
        $idsOfMeteorsMissingInSource = array();
        foreach ($databaseResults as $row) {
            if (in_array($row['source_folder'], $missingInSource)) {
                $idsOfMeteorsMissingInSource[] = $row['id'];
            }
        }

        foreach ($idsOfMeteorsMissingInSource as $missingInSourceMeteorId) {
            $this->setMeteorAsMissingInSource($missingInSourceMeteorId);
        }

        // Return an array with the counts
        $result = array(
            'found_in_source' => $foundInSourceCount,
            'found_in_database' => $foundInDatabaseCount,
            'missing_in_database' => $missingInDatabaseCount,
            'missing_in_source' => $missingInSourceCount
        );

        return $result;

    }

    /**
     * Insert meteors to the database based on list of meteor folders
     *  
     * @param array $meteorFolderList
     */
    private function insertMeteors($meteorFolderList)
    {
        $m = new FileToObjectMapper(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder, "190101", "20990101");

        $meteors = $m->mapSpecifiedMeteorFolders($meteorFolderList); // Load files from the only the specified meteor folder into objects

        $meteorInsertedCount = 0;

        $meteorDao = new MeteorDao();
        $stationDao = new StationDao();
        $camDao = new CamDao();
        $camDataDao = new ObservationCamDataDao();
        foreach ($meteors as $meteor) {
            $meteorDao->insert($meteor);
            $meteorInsertedCount++;
            if ($meteor->observation_cam_data) {
                foreach ($meteor->observation_cam_data as $cam_data) {
                    if ($cam_data->cam) {
                        if ($cam_data->cam->station) {
                            $stationDao->insert($cam_data->cam->station);
                        }
                        $camDao->insert($cam_data->cam);
                        $camDataDao->insert($cam_data);
                    }
                }
            }
        }
    }

    private function validateDate($date, $format = 'Y-m-d')
    {
        $d = DateTime::createFromFormat($format, $date);
        // The Y ( 4 digits year ) returns TRUE for any integer with any number of digits so changing the comparison from == to === fixes the issue.
        return $d && $d->format($format) === $date;
    }



    public function getAllMeteors($page = -1, $limit = 10, $orderBy = null, $order = null)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->findAll($page, $limit, $orderBy, $order);
        $count = $meteorDao->getCount();
        $pages = ceil($count / $limit);
        $result = array("totalItems" => $count, "meteors" => $meteors, "totalPages" => $pages, "currentPage" => 1);
        return json_encode($result);
    }

    public function getMeteorByID($id)
    {
        $meteorDao = new MeteorDao();
        $meteor = $meteorDao->findByID($id);

        if ($meteor) {

            $camDataDao = new ObservationCamDataDao();
            $meteorId = $meteor->id;
            $camDataFound = $camDataDao->findByMeteorID($meteorId);
            $reviewDao = new UserReviewDao();
            $reviewsFound = $reviewDao->findByMeteorID($meteorId);
            $meteor->user_review = $reviewsFound;
            $meteor->observation_cam_data = $camDataFound;
            $camDao = new CamDao();
            $stationDao = new StationDao();
            $cams = [];
            foreach ($meteor->observation_cam_data as $camData) {
                $id = $camData->id;
                $result = $camDao->findByCamDataID($id);
                if ($result) {
                    array_push($cams, $result);
                    $camData->cam = $result;
                    $camData->cam->station = $stationDao->findByCamID($camData->cam->id);
                }
            }
            $result = $meteor;
            return json_encode($result);
        } else {
            return null;
        }
    }

    public function reviewMeteor($meteorId, $userId, $rating)
    {

        $sql = "INSERT INTO user_review (user_id, confirmed, meteor_id) VALUES (" . strval($userId) . ", " . strval($rating) . ", " . strval($meteorId) . ")  ON DUPLICATE KEY UPDATE confirmed = VALUES(confirmed); ";
        return dbQuery($sql);
    }

    public function updateClassification($meteorId, $classification)
    {
        throw new Exception('Not implemented');
    }

    public function search($searchString)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->search($searchString);
        $result = array("totalItems" => 800, "meteors" => $meteors, "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }

    public function filter($stationName, $year, $meteorClass)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->filter($stationName, $year, $meteorClass);
        $result = array("totalItems" => 800, "meteors" => $meteors, "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }

    public function getMeteorCoordinateData($fromDate, $toDate, $stations)
    {
        $dataAccess = new DataAccessHelper();
        $meteors = $dataAccess->getMeteorCoordinateData($fromDate, $toDate, $stations);
                return $meteors;
    }
    

    public function getInsight($reportName)
    {
        if ($reportName == "cam") {
            $sql = "select  CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)) as Stasjonsnavn, 
c.cam_name as Kameranavn, 
min(m.date) ForsteObservasjonsTidspunkt, 
max(m.date) SisteObervasjonsTidspunkt, 
count(distinct date(m.date)) DagerMedObservasjoner,
DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
count(*) as Kameraopptak, 
count(distinct m.id) as Meteorer, 
count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
from station as s
left outer join cam as c on s.id = c.station_id
left outer join observation_cam_data as d on c.id = d.cam_id
left outer join meteor as m on d.meteor_id = m.id
group by   CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)), c.cam_name
order by  CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)),c.cam_name";
            $results = dbQuery($sql);
            $rows = array();
            while ($row = dbFetchAssoc($results)) {
                $rows[] = $row;
            }
            echo json_encode($rows);
        }
        ;

        if ($reportName == "station") {
            $sql = "select 
		CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2)) as Stasjonsnavn,
	   min(m.date) ForsteObservasjonsTidspunkt, 
	   max(m.date) SisteObervasjonsTidspunkt, 
	   count(distinct date(m.date)) DagerMedObservasjoner,
	   DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
	   count(*) as Kameraopptak, 
	   count(distinct m.id) as Meteorer, 
	   count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
	   COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
	   from station as s
	   left outer join cam as c on s.id = c.station_id
	   left outer join observation_cam_data as d on c.id = d.cam_id
	   left outer join meteor as m on d.meteor_id = m.id
	   group by   CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2))
	   order by  CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2))";
            $results = dbQuery($sql);
            $rows = array();
            while ($row = dbFetchAssoc($results)) {
                $rows[] = $row;
            }
            echo json_encode($rows);
        }
        ;


        if ($reportName == "total") {
            $sql = "select  
		min(m.date) ForsteObservasjonsTidspunkt, 
		max(m.date) SisteObervasjonsTidspunkt, 
		count(distinct date(m.date)) DagerMedObservasjoner,
		DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
		count(*) as Kameraopptak, 
		count(distinct m.id) as Meteorer, 
		count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
		COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
		from station as s
		left outer join cam as c on s.id = c.station_id
		left outer join observation_cam_data as d on c.id = d.cam_id
		left outer join meteor as m on d.meteor_id = m.id";
            $results = dbQuery($sql);
            $rows = array();
            while ($row = dbFetchAssoc($results)) {
                $rows[] = $row;
            }
            echo json_encode($rows[0]);
        }
        ;

        if ($reportName == "coordinates") {
            $sql = "SELECT 
            track_endlat lat, 
            track_endlong lng, 
            radiant_ra, 
            radiant_dec, 
            radiant_ecl_lat, 
            radiant_ecl_long, 
            track_speed, 
            track_endheight, 
            REPLACE(TRIM(radiant_shower), '\n', '') AS radiant_shower, 
            REPLACE(TRIM( meteor.date ), '\n', '') AS date        
          FROM 
            meteor 
          WHERE  1=1
            and track_speed > 0
            and track_endheight > 0
            and track_speed < 1000
            and track_startheight < 1000
            and track_startheight > track_endheight
            AND date >= DATE_SUB(NOW(), INTERVAL 2 YEAR) 
          ORDER BY 
            date DESC 
          LIMIT 300
          ";
            $results = dbQuery($sql);
            $rows = array();
            while ($row = dbFetchAssoc($results)) {
                $rows[] = $row;
            }

            echo json_encode($rows);
        }
        ;
    }
}