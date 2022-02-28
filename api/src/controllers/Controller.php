<?php

class Controller
{
    public function loadMeteorsFromFiles()
    {
        $mapper = new FileToObjectMapper('..'.DIRECTORY_SEPARATOR.'data'.DIRECTORY_SEPARATOR);
        $meteors = $mapper->map();
        $meteorDao = new MeteorDao();
        $stationDao = new StationDao();
        $camDao = new CamDao();
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
}
