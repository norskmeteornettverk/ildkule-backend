<?php

class Controller
{
    public function loadMeteorsFromFiles()
    {
        $mapper = new FileToObjectMapper('../data/');
        $meteors = $mapper->map();
        $meteorDao = new MeteorDao();
        foreach ($meteors as $meteor) {
            $meteorDao->insert($meteor);
        }
    }

    public function getAllMeteors()
    {
        $meteorDao = new MeteorDao();
        $meteors = $meteorDao->findAll();
        $result = array("totalItems" => 800, "meteors" => $meteors, "totalPages" => 80, "currentPage" => 80);
        return json_encode($result);
    }
}
