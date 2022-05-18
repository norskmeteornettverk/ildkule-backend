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
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'service'.DIRECTORY_SEPARATOR.'MeteorService.php'; 

class MeteorController
{
    public function loadMeteorsFromFiles($root_folder,$date_from, $date_to)
    {
        $meteorService = new MeteorService();
        $meteorService->loadMeteorsFromFiles($root_folder,$date_from, $date_to);
    }

    public function getAllMeteors($page = -1)
    {
        $meteorService = new MeteorService();
        return $meteorService->getAllMeteors($page);
    }

    public function getMeteorByID($id)
    {
        $meteorService = new MeteorService();
        return $meteorService->getMeteorByID($id);
    }

    public function search($searchString)
    {
        $meteorService = new MeteorService();
        return $meteorService->search($searchString);
    }

    public function filter($stationName,$year,$meteorClass)
    {
        $meteorService = new MeteorService();
        return $meteorService->filter($stationName,$year,$meteorClass);
    }
}
