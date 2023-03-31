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






}