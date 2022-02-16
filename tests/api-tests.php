<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\controllers\Controller.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\models\Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\models\Station.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\models\Cam.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\models\ObservationCamData.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\dao\MeteorDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\dao\CamDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\dao\StationDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\dao\DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . '\src\mappers\FileToObjectMapper.php';

$controller = new Controller();
$controller->loadMeteorsFromFiles();

