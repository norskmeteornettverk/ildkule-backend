<?php

class FileToObjectMapper
{

    protected $datadir;

    function __construct($datadir = null)
    {
        $this->datadir = $datadir;
    }

    protected $meteors = array();

    public function map(): array
    {

        $datefolders = array_diff(scandir($this->datadir), array('.', '..')); // folder with collection of meteors grouped by data in folders (in the format of [yyyyMMdd])

        foreach ($datefolders as $datefolder) {

            $meteorfolders = array_diff(scandir($this->datadir . $datefolder), array('.', '..'));

            foreach ($meteorfolders as $meteorfolder) {
                $meteor = new Meteor($datefolder . $meteorfolder,  date_create($datefolder . $meteorfolder));

                $meteor->datetimetag = $datefolder . $meteorfolder;
                $meteor->date = date_create($datefolder . $meteorfolder);


                $meteorfoldercontent = array_diff(scandir($this->datadir . $datefolder . '/' . $meteorfolder), array('.', '..'));  // foldername of each meteor is in the time format of [hhmmss]

                //Loading of pre-calculated meteor location
                if (array_search('location.txt', $meteorfoldercontent)) {
                    $meteor->cameraconfirmed = 1; // Confirm meteor when location file is created. Location file is created by the meteor servers when meteor is detected on two or several stations.
                    $filepath =  $this->datadir . $datefolder . '/' . $meteorfolder . '/location.txt';
                    $line = fgets(fopen($filepath, 'r'));
                    if ($line) {
                        $meteor->location = trim($line);
                    };
                } else {
                    $meteor->cameraconfirmed = 0; 
                }

                if ( $matches  = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent)) {
                    $matches  = preg_grep("/\b(\.stat|\.STAT)\b/", $meteorfoldercontent);
                    $statfilepath = $this->datadir . $datefolder . '/' . $meteorfolder . '/' . array_values($matches)[0];
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
                                $meteor->radiant_shower = str_replace("\n\r\n", "",  $words[2]);
                                break;
                            case "zenith_attractor":
                                $meteor->radiant_zenith_attractor = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "timestamp":
                                $meteor->timestamp = str_replace("\n\r\n", "", $words[2]);
                                break;
                            case "date":
                                // date already set
                                break;
                        };
                    };
                };

                array_push($this->meteors, $meteor);
            };
        };

        return $this->meteors;
    }
}
