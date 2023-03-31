<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';



class LogService
{

    public function log($log)
    {
        $dbConn = mysqli_connect(Config::host, Config::user, Config::password, Config::database);
        $sql = "insert into log_station (station_name, code, log_time) values ('" .
            strval(mysqli_real_escape_string($dbConn, $log->station->name)) . "' ,  '"
            . strval(mysqli_real_escape_string($dbConn, $log->station->code)) . "' ,  '"
            . strval(mysqli_real_escape_string($dbConn, $log->station->log_time)) . "')";
        $result = dbQuery($sql);
        return $result;
    }

    public function listLog()
    {

        $sql = "select * from log_station order by id desc limit 200";
        $results = dbQuery($sql);
        $rows = array();
        while ($row = dbFetchAssoc($results)) {
            $rows[] = $row;
        }
        return $rows;
    }
}
