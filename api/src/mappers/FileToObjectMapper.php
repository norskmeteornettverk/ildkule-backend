<?php
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'ObservationCamData.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Station.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Cam.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'ImgHelper.php';

/**
 * FileToObjectMapper
 *
 * Extracts files, maps data from the file to objects, saves.
 *
 */
class FileToObjectMapper
{
    private $datadir;
    private $meteors = array();
    private $stations = array();
    private $folder_names_to_intersect = array();

    private $meteorFileMap = [
        "startheight" => "track_startheight",
        "endheight" => "track_endheight",
        "groundtrack" => "track_groundtrack",
        "course" => "track_course",
        "incidence" => "track_incidence",
        "speed" => "track_speed",
        "speed_source" => "track_speed_source",
        "error" => "fit_error",
        "quality" => "fit_quality",
        "ra" => "radiant_ra",
        "dec" => "radiant_dec",
        "ecl_long" => "radiant_ecl_long",
        "ecl_lat" => "radiant_ecl_lat",
        "zenith_attractor" => "radiant_zenith_attractor",
        "timestamp" => "timestamp",
    ];

    private $eventFileMap = [
        'frames' => 'trail_frames',
        'duration' => 'trail_duration',
        'slope' => 'trail_slope',
        'offset' => 'trail_offset',
        'speed' => 'trail_speed',
        'correlation' => 'trail_correlation',
        'positions' => 'trail_positions',
        'timestamps' => 'trail_timestamps',
        'coordinates' => 'trail_coordinates',
        'gnomonic' => 'trail_gnomonic',
        'midpoint' => 'trail_midpoint',
        'arc' => 'trail_arc',
        'brightness' => 'trail_brightness',
        'dct_midpoint' => 'trail_dct_midpoint',
        'dct' =>  'trail_dct',
        'size' => 'trail_size',
        'frame_brightness' => 'trail_frame_brightness',
        'start' => 'video_start',
        'end' => 'video_end',
        'wallclock' => 'video_wallclock',
        'heigth' => 'video_heigth',
        'raw' => 'video_raw',
        'flash' => 'video_flash',
        'swidth' => 'config_swidth',
        'sheight' => 'config_sheight',
        'swdec' => 'config_swdec',
        'downscale_thr' => 'config_downscale_thr',
        'mintrail_sec' => 'config_mintrail_sec',
        'maxtrail_sec' => 'config_maxtrail_sec',
        'mintrail' => 'config_mintrail',
        'maxtrail' => 'config_maxtrail',
        'minspeed' => 'config_minspeed',
        'maxspeed' => 'config_maxspeed',
        'minspeed_kms' => 'config_minspeed_kms',
        'maxspeed_kms' => 'config_maxspeed_kms',
        'leveltest' => 'config_leveltest',
        'numspots' => 'config_numspots',
        'brightness' => 'config_brightness',
        'flash_thr' => 'config_flash_thr',
        'lookahead' => 'config_lookahead',
        'exit' => 'config_exit',
        'peak' => 'config_peak',
        'filter' => 'config_filter',
        'dct_threshold' => 'config_dct_threshold',
        'correlation' => 'config_correlation',
        'spacing_correlation' => 'config_spacing_correlation',
        'gnomonic_correlation' => 'config_gnomonic_correlation',
        'nothreads' => 'config_nothreads',
        'lastreport_ts' => 'config_lastreport_ts',
        'ts_future' => 'config_ts_future',
        'snapshot_interval' => 'config_snapshot_interval',
        'snapshot_integration' => 'config_snapshot_integration',
        'log_file' => 'config_log_file',
        'mask_file' => 'config_mask_file',
        'max_file' => 'config_max_file',
        'save_file' => 'config_save_file',
        'pto_file' => 'config_pto_file',
        'pto_scale' => 'config_pto_scale',
        'pto_width' => 'config_pto_width',
        'pto_height' => 'config_pto_height',
        'execute' => 'config_execute',
        'event_dir' => 'config_event_dir',
        'snapshot_dir' => 'config_snapshot_dir',
        'latitude' => 'summary_latitude',
        'longitude' => 'summary_longitude',
        'elevation' => 'summary_elevation',
        'timestamp' => 'summary_timestamp',
        'startpos' => 'summary_startpos',
        'endpos' => 'summary_endpos',
        'duration' => 'summary_duration',
        'sunalt' => 'summary_sunalt',
        'recalibrated' => 'summary_recalibrated',
        'meteor_probability' => 'summary_meteor_probability'
    ];

    function __construct($datadir = null, $date_from = '19000101', $date_to = '20990101')
    {
        $this->datadir = $datadir;
        $this->$date_from = $date_from;
        $this->$date_to = $date_to;

        $period = new DatePeriod(
            new DateTime($this->$date_from),
            new DateInterval('P1D'),
            new DateTime($this->$date_to)
        );

        foreach ($period as $date) {
            $this->folder_names_to_intersect[] = $date->format('Ymd');
        }
    }

     /**
     *
     *  Get the folders content, and not links to parent folders
     *
     * @return      array()
     *
     */
    private function getFolderContent($path) {
        if (!is_dir($path)) {
            // Dir doesn't exists
            throw new Exception("Directory not found: $path");
        }
    
        $files = scandir($path);
        
        if ($files === false) {
            // If scandir() fails
            throw new Exception("Failed to read directory: $path");
        }
    
        // Filter out the '.' and '..' entries that scandir returns as we only want the content of the folder
        $filteredFiles = array_diff($files, array('.', '..'));
    
        return $filteredFiles;
    }


    private function findResFiles($folderContent)
    {
        // Find .res or .RES files in the folder content.
        return preg_grep("/\b(\.res|\.RES)\b/", $folderContent);
    }

    private function buildStatFilePath($datefolder, $meteorfolder, $matches)
    {
        return $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . array_values($matches)[0];
    }

    private function getLineWords($line)
    {
        $trimmedLine = trim($line);
        return explode('  ', $trimmedLine, 10);
    }

    private function loadMeteorLocation(Meteor $meteor, string $datefolder, string $meteorfolder, array $meteorfoldercontent): void
    {
        //Loading of pre-calculated meteor location, if the file exists (array_search will return True if file exists)     
        if (array_search('location.txt', $meteorfoldercontent)) {
            $meteor->camera_confirmed = 1; // Confirm meteor when location file is created. Location file is created by the meteor servers when meteor is detected on two or several stations.
            $filepath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . '/location.txt';  //the location file contains the location of the meteor if it has been confirmed by several stations
            $line = fgets(fopen($filepath, 'r'));
            if ($line) {
                $meteor->location = trim($line); // set meteor location from content in location.txt (location.txt has only one line of text and can be blank)
            }
        } else {
            $meteor->camera_confirmed = 0; // we can assume that the meteor is not confirmed by other stations if the location file is missing
        }
    }

    /**
     *  Create meteor thumbnail image to improve loading speeds where needed
     */
    private function createMeteorThumbnail($meteorImagePath, $newThumbnailPath)
    {
        $imgHelp = new ImgHelper();
        $imgHelp->createThumbnail($meteorImagePath, $newThumbnailPath, 365);
    }

    /**
     *
     * Description for function
     *
     * @param    array()  $meteorfoldercontent Description
     * @param    string  $datefolder Description
     * @param    string  $meteorfolder Description
     * @param    Meteor  $meteor Description
     *
     */
    private function loadMeteorEventData($meteorfoldercontent, $datefolder, $meteorfolder, $meteor)
    {
        foreach ($meteorfoldercontent as $stationfolder) {
            // Find folders. Folders in this path is stations that have collected data on the meteor. Station name = folder name
            if (is_dir($this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . $stationfolder)) {

                $station = new Station();
                $station->station_name = $stationfolder;
                array_push($this->stations, $station);
                $cams = $this->getFolderContent($this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . $stationfolder);

                foreach ($cams as $camfolder) {

                    if (is_dir($this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . $stationfolder . DIRECTORY_SEPARATOR . $camfolder)) {

                        $cam = new Cam();
                        $cam->cam_name = $camfolder;
                        $cam->station = $station;
                        $eventfilepath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . $stationfolder . DIRECTORY_SEPARATOR . $camfolder . '/event.txt';

                        if (is_file($eventfilepath)) {

                            $data = new ObservationCamData();
                            $data->meteor = $meteor;
                            array_push($meteor->observation_cam_data, $data);
                            $data->cam = $cam;
                            $eventfile = new SplFileObject($eventfilepath);

                            // Continue reading the file until it's finished
                            while (!$eventfile->eof()) {
                                // Get a line from the file and add a line break
                                $line = $eventfile->fgets() . PHP_EOL;
                                // Split the line into words based on the '=' character
                                $words = explode('=', $line, 10);
                                // Get the key from the first column and trim whitespace
                                $key = trim($words[0]);
                                // Check if the key exists in the propertyMap array
                                if (array_key_exists($key, $this->eventFileMap)) {
                                    // Update the data object's property based on the key and value
                                    $data->{$this->eventFileMap[$key]} = trim(str_replace('\n\r\n', '', $words[1]));
                                }
                            }
                        }
                    }
                }
            }
        }
        ;

    }


    /**
     *
     * Description for function
     *
     * @param    array()  $meteorfoldercontent Description
     * @param    string  $datefolder Description
     * @param    string  $meteorfolder Description
     * @param    Meteor  $meteor Description
     *
     */
    private function loadMeteorStatFile($meteorfoldercontent, $datefolder, $meteorfolder, $meteor)
    {
        // Reads .stat file data if it exists. The .stat file contains properties of the meteor. The data is pre-calculated by the meteor server based on data from more than one station
        if ($matches = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent)) {
            $matches = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent);
            $statfilepath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . array_values($matches)[0];
            $myFile = new SplFileObject($statfilepath);

           // Read the and load data from the file, line by line
            while (!$myFile->eof()) {                
                $line = $myFile->fgets() . PHP_EOL;                
                $words = explode(' ', $line, 10);
                
                // Keyword from the first column after splitting up the line in the file
                $key = $words[0];

                // Map the values from the file to the object where keyword in the file and name of the object attribute is the same
                if (array_key_exists($key, $this->meteorFileMap)) {                    
                    $meteor->{$this->meteorFileMap[$key]} = str_replace("\n\r\n", "", $words[2]);
                } elseif ($key === "shower") {
                    // Since meteor shower names can have spaces, and spaces is also used as a split between key and value in file, special handling is needed
                    $shower = str_replace("\n\r\n", "", $words[2]);                   
                    for ($i = 3; $i <= 4; $i++) {
                        if (array_key_exists($i, $words)) {
                            $shower .= " " . $words[$i];
                        }
                    }                    
                    $meteor->radiant_shower = $shower;
                }
            }
            ;
        }
        ;

    }


    /**
     *
     * Description for function
     *
     * @param    array()  $meteorfoldercontent Description
     * @param    string  $datefolder Description
     * @param    string  $meteorfolder Description
     * @param    Meteor  $meteor Description
     *
     */
    private function loadResFileData($meteorfoldercontent, $datefolder, $meteorfolder, $meteor)
    {
        // If a .res file exists, read its data. The .stat file contains meteor positions.
        // The data is pre-calculated by the meteor server based on data from multiple stations.
        if ($matches = $this->findResFiles($meteorfoldercontent)) {
            $statfilepath = $this->buildStatFilePath($datefolder, $meteorfolder, $matches);
            $myFile = new SplFileObject($statfilepath);

            // Read the first two lines of the file to get start and end positions.
            for ($lineno = 1; $lineno <= 2; $lineno++) {
                $line = $myFile->fgets();
                $words = $this->getLineWords($line);

                if ($lineno === 1) {
                    $meteor->track_startlong = $words[0];
                    $meteor->track_startlat = $words[1];

                } elseif ($lineno === 2) {
                    $meteor->track_endlong = $words[0];
                    $meteor->track_endlat = $words[1];
                }
            }
        }

    }

    /**
     *
     * Description for function
     *
     * @param    string  $datefolder Description
     * @param    string  $meteorfolder Description
     *
     */
    private function processMeteorFolder($datefolder, $meteorfolder)
    {
        $meteorImagePath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . 'image.jpg';
        $newThumbnailPath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . 'thumbnail.jpg';
        $this->createMeteorThumbnail($meteorImagePath, $newThumbnailPath);

        // Create new meteor with basic info
        $meteor = new Meteor();
        $meteor->datetimetag = $datefolder . $meteorfolder; // set "tag" on meteor based on date and time - date and time from folder names                
        $meteor->date = date_create($datefolder . $meteorfolder); // bases on the date and time from the name of the foldes -> create a php date
        array_push($this->meteors, $meteor);

        $meteorfoldercontent = $this->getFolderContent($this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder); // foldername of each meteor is in the time format of [hhmmss]

        // Load data from files located in the meteors folder
        $this->loadMeteorLocation($meteor, $datefolder, $meteorfolder, $meteorfoldercontent);
        $this->loadMeteorStatFile($meteorfoldercontent, $datefolder, $meteorfolder, $meteor);
        $this->loadResFileData($meteorfoldercontent, $datefolder, $meteorfolder, $meteor);

        // Load data from the individual observations of the meteor from different stations and cameras
        $this->loadMeteorEventData($meteorfoldercontent, $datefolder, $meteorfolder, $meteor);

    }



    /**
     *
     *  Get the folders that is in the specified range (limits the data loaded)
     *
     * @return      array()
     *
     */
    private function getFoldersInRange()
    {       
        $all_folders = $this->getFolderContent($this->datadir); // folder with collection of meteors grouped by date in folders (in the format of [yyyyMMdd])        
        $datefolders = array_intersect($this->folder_names_to_intersect, $all_folders); // pick out the folders that's our specified range
        return $datefolders;
    }


    /**
     * Reads files from folder structure and loads the data into objects
     * 
     * @return array Array with meteors and their data
     */
    public function map(): array
    {
        // The meteors are grouped in date folders
        $datefolders = $this->getFoldersInRange();     

        // Loop goes through each date and then each meteor folder for loading of data
        foreach ($datefolders as $datefolder) {            

            // Get all meteor folder in a date folder
            $meteorfolders = $this->getFolderContent($this->datadir . $datefolder);

            // Loop though each meteor folder within a date and load their data
            foreach ($meteorfolders as $meteorfolder) {
                $this->processMeteorFolder($datefolder, $meteorfolder);
            }
            ;
        }
        ;
        return $this->meteors;
    }
}