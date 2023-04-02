<?php
ini_set('display_errors', 1);

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'User.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'UserDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'UserService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'MeteorDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'MeteorService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'FileToObjectMapper.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'helpers' . DIRECTORY_SEPARATOR . 'DataAccessHelper.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'ObservationCamData.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Station.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Cam.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'ImgHelper.php';


function testMeteorService()
{
    $meteorService = new MeteorService();
    $meteorList = $meteorService->getAllMeteors();
    print_r($meteorList);
}


function testUserService()
{
    $userService = new UserService();
    $usersList = $userService->listUsers(-1, 10, "username", "asc");
    print_r($usersList);
}



function testFileToObjectMapper()
{
    $m = new FileToObjectMapper(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR, '20230314', '20230315');
    $meteors = $m->mapSpecifiedMeteorFolders(["20230316" . DIRECTORY_SEPARATOR . "210947"]);

    //insert with meteorDao
    $meteorDao = new MeteorDao();

    //loop through meteors and insert
    foreach ($meteors as $meteor) {
        $meteorDao->insert($meteor);
    }

}


function testMeteorServiceLoad()
{
    $meteorService = new MeteorService();
    $meteorService->loadMeteorsFromFiles(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR, '20230314', '20230315');
}

function testMeteorServiceSync()
{
    $meteorService = new MeteorService();
    $meteorService->syncMeteorsFromFiles(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder);

}

function findMeteorsToUpdate()
{

    $cut_off = "2023-01-01 00:00:00"; // Meteors updated after this date will be updated (checks source and database)

    // Retrieve meteors from source
    $m = new FileToObjectMapper(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder . DIRECTORY_SEPARATOR, "190101", "20990101");
    $sourceMeteors = $m->getMeteorFoldersUpdatedAfterDate(realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . Config::data_folder, $cut_off, ["thumbnail.jpg"], true);

    // Retrieve source folders names of meteors in the database
    $date = date("Y-m-d H:i:s", strtotime($cut_off));
    $dataAccessHelper = new DataAccessHelper();
    $conditions = [">=" => ["create_time", $date]];
    $databaseResults = $dataAccessHelper->getMiscData("meteor", array("id", "create_time", "source_folder"), $conditions);

    $databaseMeteors = array();
    foreach ($databaseResults as $row) {
        $databaseMeteors[] = $row["source_folder"];
    }

    $databaseMeteors = array_filter($databaseMeteors); // Remove empty values - some meteors have no source folder due to being manually added

    // Print the results
    echo "Source meteors: " . implode(", ", $sourceMeteors) . "\n";
    echo "Database meteors: " . implode(", ", $databaseMeteors) . "\n";

    // Find the meteors in the source array that are not in the database array
    $missingInDatabase = array_diff($sourceMeteors, $databaseMeteors);

    // Find the meteors in the database array that are not in the source array
    $missingInSource = array_diff($databaseMeteors, $sourceMeteors);

    // Print the results
    echo "Missing in database: " . implode(", ", $missingInDatabase) . "\n";
    echo "Missing in source: " . implode(", ", $missingInSource) . "\n";

    // Insert meteors missing in the database
    $meteors = $m->mapSpecifiedMeteorFolders($missingInDatabase);
    $meteorDao = new MeteorDao();
    $stationDao = new StationDao();
    $camDao = new CamDao();
    $camDataDao = new ObservationCamDataDao();
    foreach ($meteors as $meteor) {
        $meteorDao->insert($meteor);
        if ($meteor->observation_cam_data) {
            foreach ($meteor->observation_cam_data as $cam_data) {
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

    // Update meteors missing in the source from the database
    $idsOfMeteorsMissingInSource = array();
    
    foreach ($databaseResults as $row) {
        if (in_array($row['source_folder'], $missingInSource)) {
            $idsOfMeteorsMissingInSource[] = $row['id'];
        }
    }

    echo "Ids of meteors missing in source: " . implode(", ", $idsOfMeteorsMissingInSource) . "\n";
    
    $meteorService = new MeteorService();
    foreach ($idsOfMeteorsMissingInSource as $missingInSourceMeteorId) {
        $meteorService->setMeteorAsMissingInSource($missingInSourceMeteorId);
    }


}

findMeteorsToUpdate();