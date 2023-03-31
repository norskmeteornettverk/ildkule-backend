<?php


require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'ObservationCamData.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Meteor.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Station.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'Cam.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'mappers' . DIRECTORY_SEPARATOR . 'ImgHelper.php';



/**
 * Class FileToObjectMapper
 *
 * map() function extracts files, maps data from the file to objects.
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
        "date" => "date",
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
        'dct' => 'trail_dct',
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
    private function getFolderContent($path)
    {
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

    private function buildStatFilePath($meteorPath, $matches)
    {
        return $meteorPath . DIRECTORY_SEPARATOR . array_values($matches)[0];
    }

    private function getLineWords($line)
    {
        $trimmedLine = trim($line);
        return explode('  ', $trimmedLine, 10);
    }

    private function loadMeteorLocation(Meteor $meteor, $meteorPath, array $meteorfoldercontent): void
    {
        //Loading of pre-calculated meteor location, if the file exists (array_search will return True if file exists)     
        if (array_search('location.txt', $meteorfoldercontent)) {
            $meteor->camera_confirmed = 1; // Confirm meteor when location file is created. Location file is created by the meteor servers when meteor is detected on two or several stations.
            $filepath = $meteorPath . '/location.txt'; //the location file contains the location of the meteor if it has been confirmed by several stations
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
     * Loading of event detection data from individual cameras
     *
     * @param    array()  $meteorfoldercontent
     * @param    string  $datefolder
     * @param    string  $meteorfolder
     * @param    Meteor  $meteor
     *
     */
    private function loadMeteorEventData($meteorfoldercontent, $meteorPath, $meteor)
    {
        foreach ($meteorfoldercontent as $stationfolder) {
            // Find folders. Folders in this path is stations that have collected data on the meteor. Station name = folder name
            if (is_dir($meteorPath . DIRECTORY_SEPARATOR . $stationfolder)) {

                $station = new Station();
                $station->station_name = $stationfolder;
                array_push($this->stations, $station);
                $cams = $this->getFolderContent($meteorPath . DIRECTORY_SEPARATOR . $stationfolder);

                foreach ($cams as $camfolder) {

                    if (is_dir($meteorPath . DIRECTORY_SEPARATOR . $stationfolder . DIRECTORY_SEPARATOR . $camfolder)) {

                        $cam = new Cam();
                        $cam->cam_name = $camfolder;
                        $cam->station = $station;
                        $eventfilepath = $meteorPath . DIRECTORY_SEPARATOR . $stationfolder . DIRECTORY_SEPARATOR . $camfolder . '/event.txt';

                        if (is_file($eventfilepath)) {

                            $data = new ObservationCamData();
                            $data->meteor = $meteor;
                            array_push($meteor->observation_cam_data, $data);
                            $data->cam = $cam;
                            $data->source_folder = $meteorPath . DIRECTORY_SEPARATOR . $stationfolder . DIRECTORY_SEPARATOR . $camfolder;

                            $eventfile = new SplFileObject($eventfilepath);

                            while (!$eventfile->eof()) {
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
     * Loading of estimated meteor shower for meteor found in "stat" file
     *
     * @param    array()  $meteorfoldercontent
     * @param    string  $datefolder
     * @param    string  $meteorfolder
     * @param    Meteor  $meteor
     *
     */
    private function loadMeteorStatFile($meteorfoldercontent, $meteorPath, $meteor)
    {
        // Reads .stat file data if it exists. The .stat file contains properties of the meteor. The data is pre-calculated by the meteor server based on data from more than one station
        if ($matches = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent)) {
            $matches = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent);
            $statfilepath = $meteorPath . DIRECTORY_SEPARATOR . array_values($matches)[0];
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
                } elseif ($key === "shower" or $key === "SHOWER") {
                    // Since meteor shower names can have spaces, and spaces is also used as a split between key and value in file, special handling is needed
                    $shower = str_replace("\n\r\n", "", $words[2]);
                    for ($i = 3; $i <= 6; $i++) {
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
     * Load content of RES file that include coordinate data of start and end point of meteor trail
     *
     * @param    array()  $meteorfoldercontent
     * @param    string  $datefolder
     * @param    string  $meteorfolder
     * @param    Meteor  $meteor
     *
     */
    private function loadResFileData($meteorfoldercontent, $meteorPath, $meteor)
    {
        // If a .res file exists, read its data. The .stat file contains meteor positions.
        // The data is pre-calculated by the meteor server based on data from multiple stations.
        if ($matches = $this->findResFiles($meteorfoldercontent)) {
            $statfilepath = $this->buildStatFilePath($meteorPath, $matches);
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

    private function hasFiles($dir)
    {
        if (!is_dir($dir)) {
            return false;
        }

        $files = scandir($dir);
        foreach ($files as $file) {
            if ($file == '.' || $file == '..') {
                continue;
            }

            $path = $dir . '/' . $file;
            if (is_file($path)) {
                return true;
            }
        }

        return false;
    }


    /**
     *
     * Load data from a meteor folder. 
     * The meteor folder contains data from one meteor.
     * Folder parameters are stripped for slashed and backslashes and replaced with DIRECTORY_SEPARATOR to make sure we have a valid path.
     * 
     * @param    string  $datefolder
     * @param    string  $meteorfolder
     * @param    int  $badMetorFlag When loading meteors already identified as bad, set this variable = 1 else 0
     *
     */
    private function processMeteorFolder($baseFolder, $relativeMeteorPath, $tag, $badMeteorFlag)
    {

        // replace all slashes with DIRECTORY_SEPARATOR, to make sure we have a valid path
        $baseFolder = str_replace('/', DIRECTORY_SEPARATOR, $baseFolder);
        $baseFolder = str_replace('\\', DIRECTORY_SEPARATOR, $baseFolder);
        $relativeMeteorPath = str_replace('/', DIRECTORY_SEPARATOR, $relativeMeteorPath);
        $relativeMeteorPath = str_replace('\\', DIRECTORY_SEPARATOR, $relativeMeteorPath);

        // build the full path to the meteor folder
        $meteorPath = $baseFolder . DIRECTORY_SEPARATOR . $relativeMeteorPath;

        //skip meteors that don't have files generated on it        
        if (!$this->hasFiles($meteorPath))
            return;

        $meteorImagePath = $meteorPath . DIRECTORY_SEPARATOR . 'image.jpg';

        if (file_exists($meteorImagePath)) {
            $newThumbnailPath = $meteorPath . DIRECTORY_SEPARATOR . 'thumbnail.jpg';
            $this->createMeteorThumbnail($meteorImagePath, $newThumbnailPath);
        }

        // Create new meteor with basic info
        $meteor = new Meteor();
        $meteor->source_incorrect_detection = $badMeteorFlag;
        $meteor->source_folder = $relativeMeteorPath;
        $meteor->datetimetag = $tag; // set "tag" on meteor based on date and time - date and time from folder names              

        $meteorfoldercontent = $this->getFolderContent($meteorPath);

        // Load data from files located in the meteors folder
        $this->loadMeteorLocation($meteor, $meteorPath, $meteorfoldercontent);
        $this->loadMeteorStatFile($meteorfoldercontent, $meteorPath, $meteor);
        $this->loadResFileData($meteorfoldercontent, $meteorPath, $meteor);

        // Load data from the individual observations of the meteor from different stations and cameras
        $this->loadMeteorEventData($meteorfoldercontent, $meteorPath, $meteor);

        // Extracts the date and time from the file name of the obs..txt file name and sets it on the meteor

        $folderPath = str_replace('/', DIRECTORY_SEPARATOR, $meteorPath);
        // Find the first obs_*.txt file in the folder
        $files = glob($folderPath . DIRECTORY_SEPARATOR . 'obs_*.txt');
        if (count($files) > 0) {
            $filename = $files[0];
            $filename = str_replace('/', DIRECTORY_SEPARATOR, $filename);
            $filename = rawurldecode($filename); // Decode percent-encoded characters (swithcing between linux and windows)
            //print("Found obs file: " . $filename);
            preg_match('/obs_(\d{4}-\d{2}-\d{2}_\d{2}[:\d{2}]*?)\.txt/', $filename, $matches);
            if (count($matches) > 1) {
                $datetimeString = $matches[1];
                $datetime = DateTime::createFromFormat('Y-m-d_H:i:s', $datetimeString);
                $meteor->date = $datetime;
                //echo "Found obs file with datetime: " . $datetime->format('Y-m-d H:i:s.u');
            } else {
                //echo "Found obs file, but couldn't extract datetime from filename.";
            }
        } else {
            //echo "No obs files found in folder.";
        }

        array_push($this->meteors, $meteor);
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
     *
     *  Lists out all meteor folder paths
     *
     * @return  array()
     *
     */
    public function getMeteorFolders()
    {
        $result = array();
        $subfolders = glob($this->datadir . '/*', GLOB_ONLYDIR); // get the folders in the datadir, typically with date names

        foreach ($subfolders as $subfolder) {

            $subfolderName = basename($subfolder);

            // get the meteor folders  of the current date folder and add their names together into the result array
            $subSubFolders = glob($subfolder . '/*', GLOB_ONLYDIR);
            foreach ($subSubFolders as $subSubFolder) {
                $subSubFolderName = basename($subSubFolder);
                $result[] = $subfolderName . DIRECTORY_SEPARATOR . $subSubFolderName;
            }
        }

        return $result;
    }

    /**
     *
     *  Lists out all folders that has been updated after the specified date
     *
     * @return  array()
     *
     */

    public function getMeteorFoldersUpdatedAfterDate($basePath, $cutoffDate, $filesToSkip = array(), $excludeFolders = true)
    {
        $level2Folders = array();

        $level1Iterator = new DirectoryIterator($basePath);

        foreach ($level1Iterator as $level1Info) {
            if ($level1Info->isDir() && !$level1Info->isDot()) {
                $level1Path = $level1Info->getPathname();

                $level2Iterator = new DirectoryIterator($level1Path);

                foreach ($level2Iterator as $level2Info) {
                    if ($level2Info->isDir() && !$level2Info->isDot()) {
                        $level2Path = $level2Info->getPathname();
                        $foundUpdatedFile = false;

                        $recursiveIterator = new RecursiveIteratorIterator(
                            new RecursiveDirectoryIterator($level2Path, RecursiveDirectoryIterator::SKIP_DOTS),
                            RecursiveIteratorIterator::SELF_FIRST
                        );

                        foreach ($recursiveIterator as $fileInfo) {
                            if ($fileInfo->isFile() && !in_array($fileInfo->getFilename(), $filesToSkip)) {
                                $fileMtime = $fileInfo->getMTime();

                                if (!$excludeFolders || ($excludeFolders && $fileMtime != $fileInfo->getPathInfo()->getMTime())) {
                                    if ($fileMtime > strtotime($cutoffDate)) {
                                        $foundUpdatedFile = true;
                                        break;
                                    }
                                }
                            }
                        }
                        if ($foundUpdatedFile) {
                            $level2Folders[] = str_replace($basePath . DIRECTORY_SEPARATOR, '', $level2Path);
                        }
                    }
                }
            }
        }

        return $level2Folders;

    }











    /**
     * Reads files from folder structure and loads the data into objects. 
     * Maps folders in specified range.
     * 
     * @return array Array with meteors and their data
     */
    public function map(): array
    {
        // The meteors are grouped in date folders
        $datefolders = $this->getFoldersInRange();

        // Load meteors from regular meteor folder, and not from those that have been identified as bad already before loading
        $badMeteorFlag = 0;

        // Loop goes through each date and then each meteor folder for loading of data
        foreach ($datefolders as $datefolder) {

            // Get all meteor folder in a date folder
            $meteorfolders = $this->getFolderContent($this->datadir . $datefolder);

            // Loop though each meteor folder within a date and load their data
            foreach ($meteorfolders as $meteorfolder) {
                $meteorPath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder;
                $this->processMeteorFolder($meteorPath, $datefolder . $meteorfolder, $this->createMeteorTag($meteorPath), $badMeteorFlag);
            }
            ;
        }
        ;
        return $this->meteors;
    }



    /**
     * Takes a relative path to a meteor, strips is from slashes to make a tag
     * 
     * @param string $meteorPath
     * 
     * @return string
     */
    private function createMeteorTag($meteorPath)
    {
        $noForwardSlashes = str_replace('/', '', $meteorPath);
        $noSlashes = str_replace('\\', '', $noForwardSlashes);
        $tag = $noSlashes;
        return $tag;
    }


    /**
     * Reads files from folder structure and loads the data into objects
     * 
     * @param    array()  $meteorFolders
     * 
     * @return array Array with meteors and their data
     */
    public function mapSpecifiedMeteorFolders($meteorFolders): array
    {
        // Loop though each meteor folder within a date and load their data
        foreach ($meteorFolders as $relativeMeteorPath) {
            $tag = $this->createMeteorTag($relativeMeteorPath); // create tag witout slashes 
            $badMeteorFlag = 0;

            // if relative meteor path contains 'wrong' then it's a bad meteor and we set the flag to 1
            if (strpos($relativeMeteorPath, 'wrong') !== false) {
                $badMeteorFlag = 1;
            }
            $baseFolder = $this->datadir;
            $this->processMeteorFolder($baseFolder, $relativeMeteorPath, $tag, $badMeteorFlag);
        }
        ;
        return $this->meteors;
    }

}