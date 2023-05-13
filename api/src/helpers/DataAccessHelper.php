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
        $query = "SELECT 
        m.id,
        m.datetimetag,      
        GROUP_CONCAT(CONCAT(c.cam_name, '@', s.station_name) SEPARATOR ', ') AS StationCam,
        CASE WHEN LOCATE('wrong', e.source_folder) > 0 THEN 1 ELSE 0 END AS SourceBadDetection,
        COUNT(DISTINCT s.station_name) AS NumberOfStations,
        m.track_endlat AS lat,
        m.track_endlong AS lng,
        m.track_startlat AS slat,
        m.track_startlong AS slng,
        m.radiant_ra,
        m.radiant_dec,
        m.radiant_ecl_lat,
        m.radiant_ecl_long,
        m.track_speed,
        m.track_endheight,
        IF(TRIM(REPLACE(REPLACE(radiant_shower, '\n', ''), '=', '')) = '', NULL, TRIM(REPLACE(REPLACE(radiant_shower, '\n', ''), '=', '')))  AS radiant_shower,        
        YEAR(TRIM(m.date)) AS year,
        MONTH(TRIM(m.date)) AS month,      
        TRIM(m.date) AS date,
        CASE WHEN 
            m.radiant_ra IS NOT NULL
            AND m.radiant_dec IS NOT NULL
            AND m.radiant_ecl_lat IS NOT NULL
            AND m.radiant_ecl_long IS NOT NULL
            AND m.track_speed IS NOT NULL
            AND m.track_endheight IS NOT NULL
        THEN 1 ELSE 0 END AS Triangulation,
        CASE WHEN 
            track_speed > 0
            AND track_endheight > 0
            AND track_speed < 1000
            AND track_startheight < 1000
            AND track_startheight > track_endheight
        THEN 1 ELSE 0 END AS ProperTriangulation,
        max(e.summary_meteor_probability) MeteorScoreHighest            
    FROM station s
    INNER JOIN cam c ON s.id = c.station_id
    INNER JOIN observation_cam_data e ON c.id = e.cam_id
    INNER JOIN meteor m ON e.meteor_id = m.id       
    WHERE 1=1
        AND (source_removed = 0 or source_removed is null)         
    ";

        // Filter by date range
        if (!empty($from_date) && !empty($to_date)) {
            $query .= " AND m.date BETWEEN :from_date AND :to_date";
        }

        // Filter by station names
        if (!empty($stations)) {
            $query .= " AND m.id in (  select m.id from meteor m INNER JOIN observation_cam_data e ON m.id = e.meteor_id inner join cam c on e.cam_id = c.id inner join station s on s.id = c.station_id where s.station_name in ( " . implode(',', array_map(function ($station) {
                return "'" . $station . "'";
            }, $stations)) . "))";
        }

        $query .= " GROUP BY 
                    m.id,
                    m.track_endlat,
                    m.track_endlong,
                    m.radiant_ra,
                    m.radiant_dec,
                    m.radiant_ecl_lat,
                    m.radiant_ecl_long,
                    m.track_speed,
                    m.track_endheight,
                    TRIM(REPLACE(radiant_shower, '\n', '')),
                    TRIM(m.date),
                    CASE WHEN LOCATE('wrong', e.source_folder) > 0 THEN 1 ELSE 0 END

                    ORDER BY m.date DESC
        ";

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