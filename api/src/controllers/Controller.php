<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'config.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'DatabaseConnection.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'ObservationCamData.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'Meteor.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'MeteorDao.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'Station.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'StationDao.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'models'.DIRECTORY_SEPARATOR.'Cam.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'CamDao.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'dao'.DIRECTORY_SEPARATOR.'ObservationCamDataDao.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'mappers'.DIRECTORY_SEPARATOR.'FileToObjectMapper.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'controllers'.DIRECTORY_SEPARATOR.'Controller.php'; 

class Controller
{
    public function loadMeteorsFromFiles()
    {
        set_time_limit(600);
        $mapper = new FileToObjectMapper('..' . DIRECTORY_SEPARATOR . 'data' . DIRECTORY_SEPARATOR);
        $meteors = $mapper->map();
        $meteorDao = new MeteorDao();
        $stationDao = new StationDao();
        $camDao = new CamDao();
        $camDataDao = new ObservationCamDataDao();
        foreach ($meteors as $meteor) {
            $meteorDao->insert($meteor);
            print "meteor found  </br>";
            if ($meteor->observation_cam_data) {
                print "cam data not empty </br>";
                foreach ($meteor->observation_cam_data as $cam_data) {
                    print "cam data as data  </br>";
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

    public function getAllMeteors()
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->findAll();
        $result = array("totalItems" => 800, "meteors" => $meteors, "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }

    public function getMeteorByID($id)
    {
        $meteorDao = new MeteorDao();
        $meteor = $meteorDao->findByID($id);
        $result = $meteor;
        return json_encode($result);
    }

    public function search($searchString)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->search($searchString);
        $result =  array("totalItems" => 800,  "meteors" => $meteors,  "totalPages" => 80, "currentPage" => 80);
        return json_encode( $result);
    }

    public function filter($stationName,$year,$meteorClass)
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->filter($stationName,$year,$meteorClass);
        $result =  array("totalItems" => 800,  "meteors" => $meteors,  "totalPages" => 80, "currentPage" => 80);
        return json_encode( $result);
    }
}
