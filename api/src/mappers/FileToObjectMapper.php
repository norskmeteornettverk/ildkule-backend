<?php

class FileToObjectMapper
{

    protected $datadir;
    protected $meteors = array();
    protected $stations = array();

    function __construct($datadir = null)
    {
        $this->datadir = $datadir;
    }



    protected function getFolderContent($folderpath)
    {
        return array_diff(scandir($folderpath), array('.', '..'));    // get only content in folder
    }

    /**
     * Reads files from folder structure and loads the data into objects
     * 
     * @return array Array with meteors and their data
     */
    public function map(): array
    {

        $datefolders = $this->getFolderContent($this->datadir); // folder with collection of meteors grouped by date in folders (in the format of [yyyyMMdd])

        // Loop goes through each meteor folder
        foreach ($datefolders as $datefolder) {

            // Get content of meteor (files, folder, etc)
            $meteorfolders =  $this->getFolderContent($this->datadir . $datefolder); //

            // Loop through date folder (get files and folder related to several meteors)
            foreach ($meteorfolders as $meteorfolder) {
                $meteor = new Meteor();
              

                $meteor->datetimetag = $datefolder . $meteorfolder; // set "tag" on meteor based on date and time - date and time from folder names                
                $meteor->date = date_create($datefolder . $meteorfolder); // bases on the date and time from the name of the foldes -> create a php date

                array_push($this->meteors, $meteor);

                $meteorfoldercontent =  $this->getFolderContent($this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder);  // foldername of each meteor is in the time format of [hhmmss]

                //Loading of pre-calculated meteor location, if the file exists (array_search will return True if file exists) 
                if (array_search('location.txt', $meteorfoldercontent)) {
                    $meteor->cameraconfirmed = 1; // Confirm meteor when location file is created. Location file is created by the meteor servers when meteor is detected on two or several stations.
                    $filepath =  $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . '/location.txt'; //the location file contains the location of the meteor if it has been confirmed by several stations
                    $line = fgets(fopen($filepath, 'r'));
                    if ($line) {
                        $meteor->location = trim($line); // set meteor location from content in location.txt (location.txt has only one line of text and can be blank)
                    };
                } else {
                    $meteor->cameraconfirmed = 0; // we can assume that the meteor is not confirmed by other stations if the location file is missing
                }

                // Reads .stat file data if it exists. The .stat file contains properties of the meteor. The data is pre-calculated by the meteor server based on data from more than one station
                if ($matches  = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent)) {
                    $matches  = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent);
                    $statfilepath = $this->datadir . $datefolder . DIRECTORY_SEPARATOR . $meteorfolder . DIRECTORY_SEPARATOR . array_values($matches)[0];
                    $myFile = new SplFileObject($statfilepath);
                    while (!$myFile->eof()) {
                        $line =  $myFile->fgets() . PHP_EOL;
                        $words = explode(' ',  $line, 10);
                        switch ($words[0]) {
                            case "startheight":
                                $meteor->track_startheight =  str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "endheight":
                                $meteor->track_endheight = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "groundtrack":
                                $meteor->track_groundtrack = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "course":
                                $meteor->track_course = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "incidence":
                                $meteor->track_incidence = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "speed":
                                $meteor->track_speed = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "speed_source":
                                $meteor->track_speed_source = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "error":
                                $meteor->fit_error = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "quality":
                                $meteor->fit_quality = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "ra":
                                $meteor->radiant_ra = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "dec":
                                $meteor->radiant_dec = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "ecl_long":
                                $meteor->radiant_ecl_long = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "ecl_lat":
                                $meteor->radiant_ecl_lat = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "shower":
                                $meteor->radiant_shower = str_replace("\n\r\n", "",  $words[2]) . (array_key_exists(3, $words) ? " " . $words[3] : "") . (array_key_exists(4, $words) ? " " . $words[4] : "");
                                break;
                            case "zenith_attractor":
                                $meteor->radiant_zenith_attractor = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "timestamp":
                                $meteor->timestamp = str_replace("\n\r\n", "", $words[2]); //file contains timestamp in epoch format 
                                break;
                            case "date":
                                // date already set
                                break;
                        };
                    };
                };

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
                                    while (!$eventfile->eof()) {
                                        $line =  $eventfile->fgets() . PHP_EOL;
                                        $words = explode('=',  $line, 10);
                                        switch (trim($words[0])) {
                                            case 'frames':
                                                $data->trail_frames = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'duration':
                                                $data->trail_duration = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'slope':
                                                $data->trail_slope = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'offset':
                                                $data->trail_offset = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'speed':
                                                $data->trail_speed = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'correlation':
                                                $data->trail_correlation = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'positions':
                                                $data->trail_positions = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'timestamps':
                                                $data->trail_timestamps = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'coordinates':
                                                $data->trail_coordinates = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'gnomonic':
                                                $data->trail_gnomonic = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'midpoint':
                                                $data->trail_midpoint = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'arc':
                                                $data->trail_arc = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'brightness':
                                                $data->trail_brightness = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'size':
                                                $data->trail_size = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'frame_brightness':
                                                $data->trail_frame_brightness = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'start':
                                                $data->video_start = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'end':
                                                $data->video_end = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'wallclock':
                                                $data->video_wallclock = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'heigth':
                                                $data->video_heigth = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'raw':
                                                $data->video_raw = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'flash':
                                                $data->video_flash = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'swidth':
                                                $data->config_swidth = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'sheight':
                                                $data->config_sheight = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'swdec':
                                                $data->config_swdec = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'downscale_thr':
                                                $data->config_downscale_thr = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'mintrail_sec':
                                                $data->config_mintrail_sec = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'maxtrail_sec':
                                                $data->config_maxtrail_sec = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'mintrail':
                                                $data->config_mintrail = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'maxtrail':
                                                $data->config_maxtrail = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'minspeed':
                                                $data->config_minspeed = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'maxspeed':
                                                $data->config_maxspeed = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'minspeed_kms':
                                                $data->config_minspeed_kms = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'maxspeed_kms':
                                                $data->config_maxspeed_kms = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'leveltest':
                                                $data->config_leveltest = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'numspots':
                                                $data->config_numspots = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'brightness':
                                                $data->config_brightness = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'flash_thr':
                                                $data->config_flash_thr = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'lookahead':
                                                $data->config_lookahead = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'exit':
                                                $data->config_exit = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'peak':
                                                $data->config_peak = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'filter':
                                                $data->config_filter = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'dct_threshold':
                                                $data->config_dct_threshold = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'correlation':
                                                $data->config_correlation = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'spacing_correlation':
                                                $data->config_spacing_correlation = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'gnomonic_correlation':
                                                $data->config_gnomonic_correlation = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'nothreads':
                                                $data->config_nothreads = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'lastreport_ts':
                                                $data->config_lastreport_ts = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'ts_future':
                                                $data->config_ts_future = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'snapshot_interval':
                                                $data->config_snapshot_interval = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'snapshot_integration':
                                                $data->config_snapshot_integration = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'log_file':
                                                $data->config_log_file = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'mask_file':
                                                $data->config_mask_file = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'max_file':
                                                $data->config_max_file = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'save_file':
                                                $data->config_save_file = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'pto_file':
                                                $data->config_pto_file = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'pto_scale':
                                                $data->config_pto_scale = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'pto_width':
                                                $data->config_pto_width = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'pto_height':
                                                $data->config_pto_height = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'execute':
                                                $data->config_execute = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'event_dir':
                                                $data->config_event_dir = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'snapshot_dir':
                                                $data->config_snapshot_dir = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'latitude':
                                                $data->summary_latitude = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'longitude':
                                                $data->summary_longitude = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'elevation':
                                                $data->summary_elevation = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'timestamp':
                                                $data->summary_timestamp = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'startpos':
                                                $data->summary_startpos = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'endpos':
                                                $data->summary_endpos = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'duration':
                                                $data->summary_duration = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'sunalt':
                                                $data->summary_sunalt = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'recalibrated':
                                                $data->summary_recalibrated = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'meteor_probability':
                                                $data->summary_meteor_probability = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'recalibrated':
                                                $data->summary_recalibrated = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                            case 'meteor_probability':
                                                $data->summary_meteor_probability = trim(str_replace('\n\r\n', '', $words[1]));
                                                break;
                                        };
                                    };                                 
                                                  
                                }
                            }
                        }
                    }
                };
            };
        };
        return $this->meteors;
    }
}
