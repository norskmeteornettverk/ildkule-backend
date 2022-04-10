<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DaoInterface.php';

class ObservationCamDataDao implements DaoInterface
{

    protected  $db;
    protected  $dbh;
    protected  $reflection;

    function __construct()
    {
        $this->db = new DatabaseConnection(Config::host, Config::port, Config::database, Config::user, Config::password);
        $this->dbh =  $this->db->getDbh();
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
        (meteor_id,
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
        summary_meteor_probability)
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
        )";
        
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
            $camData->summary_recalibrated,
            $camData->summary_meteor_probability
            
        );
        $this->dbh->prepare($query)->execute($values);
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
