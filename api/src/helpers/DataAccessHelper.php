<?php

class DataAccessHelper
{
    private $connection;

    public function __construct()
    {
        $dsn = 'mysql:host=' . Config::host . ';port=' . Config::port . ';dbname=' . Config::database;
        $this->connection = new PDO($dsn, Config::user, Config::password);
    }

    public function getMiscData($table, $columns, $conditions = [])
    {
        // Build the SELECT part of the query
        $select = "SELECT " . implode(", ", $columns);

        // Build the FROM part of the query
        $from = " FROM " . $table;

        // Build the WHERE part of the query, if there are conditions
        $where = "";
        $conditionStrings = [];
        if (!empty($conditions)) {
            $where = " WHERE ";
            foreach ($conditions as $operator => $condition) {
                if ($operator == "between") {
                    $column = $condition[0];
                    $value1 = $condition[1];
                    $value2 = $condition[2];
                    $conditionStrings[] = "$column BETWEEN '$value1' AND '$value2'";
                } else {
                    $column = $condition[0];
                    $value = $condition[1];
                    $conditionStrings[] = "$column $operator '$value'";
                }
            }
            $where .= implode(" AND ", $conditionStrings);
        }

        // Prepare the query
        $query = $select . $from . $where;
        $stmt = $this->connection->prepare($query);

        // Execute the query and fetch results
        $stmt->execute();
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // Close the statement and return the data
        $stmt->closeCursor();
        return $data;
    }

    public function getMeteorCoordinateData($from_date, $to_date, $stations)
    {
        // Base query
        $query = "SELECT DISTINCT track_endlat lat, track_endlong lng, radiant_ra, radiant_dec, radiant_ecl_lat, radiant_ecl_long, track_speed, track_endheight, 
              REPLACE(TRIM(radiant_shower), '\n', '') AS radiant_shower, 
              REPLACE(TRIM( m.date ), '\n', '') AS date    
              FROM station s
              INNER JOIN cam c ON s.id = c.station_id
              INNER JOIN observation_cam_data e ON c.id = e.cam_id
              INNER JOIN meteor m ON e.meteor_id = m.id
              WHERE track_speed > 0 
                AND track_endheight > 0
                AND track_speed < 1000
                AND track_startheight < 1000
                AND track_startheight > track_endheight ";

        // Filter by date range
        if (!empty($from_date) && !empty($to_date)) {
            $query .= " AND m.date BETWEEN :from_date AND :to_date";
        }

        // Filter by station names
        if (!empty($stations)) {
            $query .= " AND s.station_name IN (" . implode(',', array_map(function ($station) {
                return "'" . $station . "'";
            }, $stations)) . ")";
        }

        $stmt = $this->connection->prepare($query);

        // Bind date parameters if set
        if (!empty($from_date) && !empty($to_date)) {
            $stmt->bindParam(':from_date', $from_date);
            $stmt->bindParam(':to_date', $to_date);
        }

     
        $stmt->execute();
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $stmt->closeCursor();
        return $data;
    }






}