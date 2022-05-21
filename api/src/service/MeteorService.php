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

    private function validateDate($date, $format = 'Y-m-d')
    {
        $d = DateTime::createFromFormat($format, $date);
        // The Y ( 4 digits year ) returns TRUE for any integer with any number of digits so changing the comparison from == to === fixes the issue.
        return $d && $d->format($format) === $date;
    }



    public function getAllMeteors($page = -1, $limit = 10)
    {
        $meteorDao = new MeteorDao();     
        $meteors = $meteorDao->findAll($page,  $limit);
        $count =  $meteorDao->getCount();
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
            $meteor->user_review =  $reviewsFound;
            $meteor->observation_cam_data = $camDataFound;
            $camDao = new CamDao();
            $stationDao = new StationDao();
            $cams  = [];           
            foreach ($meteor->observation_cam_data as $camData) {
                $id = $camData->id;
                $result = $camDao->findByCamDataID($id);
                if ($result) {
                    array_push($cams, $result);
                    $camData->cam = $result;
                    $camData->cam->station =  $stationDao->findByCamID($camData->cam->id);
                }
            }
            $result = $meteor;
            return json_encode($result);
        } else {
            return null;
        }
    }

    public function search($searchString)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->search($searchString);
        $result =  array("totalItems" => 800,  "meteors" => $meteors,  "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }

    public function filter($stationName, $year, $meteorClass)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->filter($stationName, $year, $meteorClass);
        $result =  array("totalItems" => 800,  "meteors" => $meteors,  "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }
}
