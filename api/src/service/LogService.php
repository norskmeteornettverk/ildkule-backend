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

    public function lastSeen()
    {
        $cameraStations = [
            ["tag" => "sorreisa", "name" => "Sørreisa", "cameras" => ["cam1", "cam2", "cam3", "cam4"]],
            ["tag" => "voksenlia", "name" => "Voksenlia", "cameras" => ["cam1", "cam2", "cam3"]],
            ["tag" => "orsta", "name" => "Ørsta", "cameras" => ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6", "cam7"]],
            ["tag" => "trondheim", "name" => "Trondheim", "cameras" => ["cam1", "cam2", "cam3"]],
            ["tag" => "harestua", "name" => "Harestua", "cameras" => ["cam1", "cam2", "cam3", "cam4"]],
            ["tag" => "kristiansand", "name" => "Kristiansand", "cameras" => ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6", "cam7"]],
            ["tag" => "larvik", "name" => "Larvik", "cameras" => ["cam1", "cam2", "cam3", "cam4"]],
            ["tag" => "gran", "name" => "Gran", "cameras" => ["cam1", "cam2"]],
            ["tag" => "skibotn", "name" => "Skibotn", "cameras" => ["cam1", "cam2", "cam3", "cam4"]],
            ["tag" => "gaustatoppen", "name" => "Gaustatoppen", "cameras" => ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6", "cam7"]],
            ["tag" => "eiscat", "name" => "EISCAT", "cameras" => ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6", "cam7"]],
            ["tag" => "tromso", "name" => "Tromsø", "cameras" => ["cam1", "cam2", "cam3", "cam4", "cam5", "cam6", "cam7"]]
        ];

        $results = [];

        foreach ($cameraStations as $station) {
            $stationResult = [
                'stationName' => $station['name'],
                'station' => $station['tag'],
                'cameras' => []
            ];

            foreach ($station['cameras'] as $camera) {
                $imageUrl = "http://norskmeteornettverk.no/cam/" . strtolower($station['tag']) . "/$camera/snapshot.jpg";

                $ch = curl_init($imageUrl);
                curl_setopt($ch, CURLOPT_NOBODY, true);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($ch, CURLOPT_HEADER, true);
                $response = curl_exec($ch);
                $statusCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                curl_close($ch);

                if ($statusCode == 200) {
                    preg_match('/^Last-Modified: *([^\r\n]+)/m', $response, $matches);
                    $lastModified = isset($matches[1]) ? $matches[1] : null;
                    $cameraResult = [
                        'name' => $camera,
                        'imgService' => $imageUrl,
                        'lastSeen' => $lastModified,
                        'connected' => true
                    ];
                } else {
                    $cameraResult = [
                        'name' => $camera,
                        'imgService' => $imageUrl,
                        'lastSeen' => null,
                        'connected' => false
                    ];
                }

                array_push($stationResult['cameras'], $cameraResult);
            }

            array_push($results, $stationResult);
        }

        return $results;

    }
}