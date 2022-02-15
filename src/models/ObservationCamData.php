<?php

class ObservationCamData implements JsonSerializable
{
    protected Meteor $meteor;
    protected Cam $cam;
    protected $created;
    protected $trail_frames;
    protected $trail_duration;
    protected $trail_slope;
    protected $trail_offset;
    protected $trail_speed;
    protected $trail_correlation;
    protected $trail_positions;
    protected $trail_timestamps;
    protected $trail_coordinates;
    protected $trail_gnomonic;
    protected $trail_midpoint;
    protected $trail_arc;
    protected $trail_brightness;
    protected $trail_size;
    protected $trail_frame_brightness;
    protected $video_start;
    protected $video_end;
    protected $video_wallclock;
    protected $video_heigth;
    protected $video_raw;
    protected $video_flash;
    protected $config_swidth;
    protected $config_sheight;
    protected $config_swdec;
    protected $config_downscale_thr;
    protected $config_mintrail_sec;
    protected $config_maxtrail_sec;
    protected $config_mintrail;
    protected $config_maxtrail;
    protected $config_minspeed;
    protected $config_maxspeed;
    protected $config_minspeed_kms;
    protected $config_maxspeed_kms;
    protected $config_leveltest;
    protected $config_numspots;
    protected $config_brightness;
    protected $config_flash_thr;
    protected $config_lookahead;
    protected $config_exit;
    protected $config_peak;
    protected $config_filter;
    protected $config_dct_threshold;
    protected $config_correlation;
    protected $config_spacing_correlation;
    protected $config_gnomonic_correlation;
    protected $config_nothreads;
    protected $config_lastreport_ts;
    protected $config_ts_future;
    protected $config_snapshot_interval;
    protected $config_snapshot_integration;
    protected $config_log_file;
    protected $config_mask_file;
    protected $config_max_file;
    protected $config_save_file;
    protected $config_pto_file;
    protected $config_pto_scale;
    protected $config_pto_width;
    protected $config_pto_height;
    protected $config_execute;
    protected $config_event_dir;
    protected $config_snapshot_dir;
    protected $summary_latitude;
    protected $summary_longitude;
    protected $summary_elevation;
    protected $summary_timestamp;
    protected $summary_startpos;
    protected $summary_endpos;
    protected $summary_duration;
    protected $summary_sunalt;
    protected $summary_recalibrated;
    protected $summary_meteor_probability;

    public function __get($property)
    {
        if (property_exists($this, $property)) {
            return $this->$property;
        }
    }

    public function __set($property, $value)
    {
        if (property_exists($this, $property)) {
            $this->$property = $value;
        }
        return $this;
    }

    public function jsonSerialize()
    {
        return (object) get_object_vars($this);
    }
}
