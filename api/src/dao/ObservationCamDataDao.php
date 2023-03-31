<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';

class ObservationCamDataDao implements DaoInterface
{

    protected $db;
    protected $dbh;
    protected $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh = $this->db->getDbh();
    }

    public function findAll()
    {
        $stmt = $this->dbh->query("SELECT * FROM observation_cam_data");
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'ObservationCamData');
        return $result;
    }

    public function insert($camData)
    {
        $query = "INSERT INTO observation_cam_data
        (
        meteor_id,
        cam_id,        
        trail_frames,
        trail_duration,
        trail_slope,
        trail_offset,
        trail_speed,
        trail_correlation,
        trail_positions,
        trail_timestamps,
        trail_coordinates,
        trail_gnomonic,
        trail_midpoint,
        trail_arc,
        trail_brightness,
        trail_dct_midpoint,
        trail_dct,
        trail_size,
        trail_frame_brightness,
        video_start,
        video_end,
        video_wallclock,
        video_heigth,
        video_raw,
        video_flash,
        config_swidth,
        config_sheight,
        config_swdec,
        config_downscale_thr,
        config_mintrail_sec,
        config_maxtrail_sec,
        config_mintrail,
        config_maxtrail,
        config_minspeed,
        config_maxspeed,
        config_minspeed_kms,
        config_maxspeed_kms,
        config_leveltest,
        config_numspots,
        config_brightness,
        config_flash_thr,
        config_lookahead,
        config_exit,
        config_peak,
        config_filter,
        config_dct_threshold,
        config_correlation,
        config_spacing_correlation,
        config_gnomonic_correlation,
        config_nothreads,
        config_lastreport_ts,
        config_ts_future,
        config_snapshot_interval,
        config_snapshot_integration,
        config_log_file,
        config_mask_file,
        config_max_file,
        config_save_file,
        config_pto_file,
        config_pto_scale,
        config_pto_width,
        config_pto_height,
        config_execute,
        config_event_dir,
        config_snapshot_dir,
        summary_latitude,
        summary_longitude,
        summary_elevation,
        summary_timestamp,
        summary_startpos,
        summary_endpos,
        summary_duration,
        summary_sunalt,
        summary_recalibrated,
        summary_meteor_probability,
        source_folder
        )
        VALUES
        (?
        ,?        
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        ,?
        )
        ON DUPLICATE KEY UPDATE 
        trail_frames = values( trail_frames ) 
         ,trail_duration =values(         trail_duration ) 
         ,trail_slope =values(         trail_slope ) 
         ,trail_offset =values(         trail_offset ) 
         ,trail_speed =values(         trail_speed ) 
         ,trail_correlation =values(         trail_correlation ) 
         ,trail_positions =values(         trail_positions ) 
         ,trail_timestamps =values(         trail_timestamps ) 
         ,trail_coordinates =values(         trail_coordinates ) 
         ,trail_gnomonic =values(         trail_gnomonic ) 
         ,trail_midpoint =values(         trail_midpoint ) 
         ,trail_arc =values(         trail_arc ) 
         ,trail_brightness =values(         trail_brightness ) 
         ,trail_dct_midpoint =values(         trail_dct_midpoint ) 
         ,trail_dct =values(         trail_dct ) 
         ,trail_size =values(         trail_size ) 
         ,trail_frame_brightness =values(         trail_frame_brightness ) 
         ,video_start =values(         video_start ) 
         ,video_end =values(         video_end ) 
         ,video_wallclock =values(         video_wallclock ) 
         ,video_heigth =values(         video_heigth ) 
         ,video_raw =values(         video_raw ) 
         ,video_flash =values(         video_flash ) 
         ,config_swidth =values(         config_swidth ) 
         ,config_sheight =values(         config_sheight ) 
         ,config_swdec =values(         config_swdec ) 
         ,config_downscale_thr =values(         config_downscale_thr ) 
         ,config_mintrail_sec =values(         config_mintrail_sec ) 
         ,config_maxtrail_sec =values(         config_maxtrail_sec ) 
         ,config_mintrail =values(         config_mintrail ) 
         ,config_maxtrail =values(         config_maxtrail ) 
         ,config_minspeed =values(         config_minspeed ) 
         ,config_maxspeed =values(         config_maxspeed ) 
         ,config_minspeed_kms =values(         config_minspeed_kms ) 
         ,config_maxspeed_kms =values(         config_maxspeed_kms ) 
         ,config_leveltest =values(         config_leveltest ) 
         ,config_numspots =values(         config_numspots ) 
         ,config_brightness =values(         config_brightness ) 
         ,config_flash_thr =values(         config_flash_thr ) 
         ,config_lookahead =values(         config_lookahead ) 
         ,config_exit =values(         config_exit ) 
         ,config_peak =values(         config_peak ) 
         ,config_filter =values(         config_filter ) 
         ,config_dct_threshold =values(         config_dct_threshold ) 
         ,config_correlation =values(         config_correlation ) 
         ,config_spacing_correlation =values(         config_spacing_correlation ) 
         ,config_gnomonic_correlation =values(         config_gnomonic_correlation ) 
         ,config_nothreads =values(         config_nothreads ) 
         ,config_lastreport_ts =values(         config_lastreport_ts ) 
         ,config_ts_future =values(         config_ts_future ) 
         ,config_snapshot_interval =values(         config_snapshot_interval ) 
         ,config_snapshot_integration =values(         config_snapshot_integration ) 
         ,config_log_file =values(         config_log_file ) 
         ,config_mask_file =values(         config_mask_file ) 
         ,config_max_file =values(         config_max_file ) 
         ,config_save_file =values(         config_save_file ) 
         ,config_pto_file =values(         config_pto_file ) 
         ,config_pto_scale =values(         config_pto_scale ) 
         ,config_pto_width =values(         config_pto_width ) 
         ,config_pto_height =values(         config_pto_height ) 
         ,config_execute =values(         config_execute ) 
         ,config_event_dir =values(         config_event_dir ) 
         ,config_snapshot_dir =values(         config_snapshot_dir ) 
         ,summary_latitude =values(         summary_latitude ) 
         ,summary_longitude =values(         summary_longitude ) 
         ,summary_elevation =values(         summary_elevation ) 
         ,summary_timestamp =values(         summary_timestamp ) 
         ,summary_startpos =values(         summary_startpos ) 
         ,summary_endpos =values(         summary_endpos ) 
         ,summary_duration =values(         summary_duration ) 
         ,summary_sunalt =values(         summary_sunalt ) 
         ,summary_recalibrated =values(         summary_recalibrated ) 
         ,summary_meteor_probability=values(         summary_meteor_probability)
         ,source_folder=values(         source_folder)
        ;

            
        
        
        ";

        $values = array(
            $camData->meteor->id,
            $camData->cam->id,
            $camData->trail_frames,
            $camData->trail_duration,
            $camData->trail_slope,
            $camData->trail_offset,
            $camData->trail_speed,
            $camData->trail_correlation,
            $camData->trail_positions,
            $camData->trail_timestamps,
            $camData->trail_coordinates,
            $camData->trail_gnomonic,
            $camData->trail_midpoint,
            $camData->trail_arc,
            $camData->trail_brightness,
            $camData->trail_dct_midpoint,
            $camData->trail_dct,
            $camData->trail_size,
            $camData->trail_frame_brightness,
            $camData->video_start,
            $camData->video_end,
            $camData->video_wallclock,
            $camData->video_heigth,
            $camData->video_raw,
            $camData->video_flash,
            $camData->config_swidth,
            $camData->config_sheight,
            $camData->config_swdec,
            $camData->config_downscale_thr,
            $camData->config_mintrail_sec,
            $camData->config_maxtrail_sec,
            $camData->config_mintrail,
            $camData->config_maxtrail,
            $camData->config_minspeed,
            $camData->config_maxspeed,
            $camData->config_minspeed_kms,
            $camData->config_maxspeed_kms,
            $camData->config_leveltest,
            $camData->config_numspots,
            $camData->config_brightness,
            $camData->config_flash_thr,
            $camData->config_lookahead,
            $camData->config_exit,
            $camData->config_peak,
            $camData->config_filter,
            $camData->config_dct_threshold,
            $camData->config_correlation,
            $camData->config_spacing_correlation,
            $camData->config_gnomonic_correlation,
            $camData->config_nothreads,
            $camData->config_lastreport_ts,
            $camData->config_ts_future,
            $camData->config_snapshot_interval,
            $camData->config_snapshot_integration,
            $camData->config_log_file,
            $camData->config_mask_file,
            $camData->config_max_file,
            $camData->config_save_file,
            $camData->config_pto_file,
            $camData->config_pto_scale,
            $camData->config_pto_width,
            $camData->config_pto_height,
            $camData->config_execute,
            $camData->config_event_dir,
            $camData->config_snapshot_dir,
            $camData->summary_latitude,
            $camData->summary_longitude,
            $camData->summary_elevation,
            $camData->summary_timestamp,
            $camData->summary_startpos,
            $camData->summary_endpos,
            $camData->summary_duration,
            $camData->summary_sunalt,
            $camData->summary_recalibrated,
            $camData->summary_meteor_probability,
            $camData->source_folder


        );
        $this->dbh->prepare($query)->execute($values);


        if (!$camData->id) {
            $camData->id = $this->dbh->lastInsertId(); // set the id based on the id generateted in the db

            // id will still be missing if update instead of insert - select the id from the db
            if (!$camData->id) {
                $q = $this->dbh->prepare("SELECT id FROM observation_cam_data WHERE meteor_id=? and cam_id = ?");
                $q->execute(array($camData->meteor->id, $camData->cam->id));
                $id = $q->fetchColumn();
                $camData->id = $id;
            }
        }

    }


    public function findByID($id)
    {
        $query = "SELECT * FROM meteor WHERE id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $id);
        $stmt->setFetchMode(PDO::FETCH_INTO, new Meteor());
        if ($stmt->execute()) {
            return $stmt->fetch();
        }
        return null;
    }

    public function findByMeteorID($meteorId)
    {
        $query = "SELECT * FROM observation_cam_data WHERE meteor_id = :id;";
        $stmt = $this->dbh->prepare($query);
        $stmt->bindParam(':id', $meteorId);
        $stmt->execute();
        $result = $stmt->fetchAll(PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE, 'ObservationCamData');
        return $result;
    }


    public function delete($id)
    {
        throw new Exception('Not implemented');

    }



    public function update($id, $confirmed)
    {
        //TODO - kladd - men hvilke attributter trenger vi egentlig å oppdatere fra frontend? blir det på en 'confirmed' så må vi nok få det inn som egen kolonne i meteor. 
        $query = "UPDATE meteor SET confirmed = :confirmed; WHERE id = :id;";
        $stmt = $this->dbh->execute($query);
        if ($stmt->execute()) {
            print 'You updated ' . $id . '. Confirmed is now set to ' . $confirmed;
        } else {
            print 'Failed to update ' . $id;
        }
    }
}