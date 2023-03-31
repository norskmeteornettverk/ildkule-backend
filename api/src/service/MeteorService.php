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

    public function syncMeteorsFromFiles($root_folder)
    {
    
        set_time_limit(600);

        $m = new FileToObjectMapper(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR, '20230314', '20230318');
        $meteors = $m->mapSpecifiedMeteorFolders(["wrongs" . DIRECTORY_SEPARATOR . "001910"]);       

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
        }
        else {
            return null;
        }
    }

    public function reviewMeteor($meteorId, $userId, $rating)
    {

        $sql = "INSERT INTO user_review (user_id, confirmed, meteor_id) VALUES (" .  strval($userId) . ", " . strval($rating) . ", " . strval($meteorId) . ")  ON DUPLICATE KEY UPDATE confirmed = VALUES(confirmed); ";
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

        if ($reportName == "coordinates") {
            $sql = "SELECT track_endlat lat, track_endlong lng FROM 153413_ildkule_dev.meteor where track_endlat is not null";
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
