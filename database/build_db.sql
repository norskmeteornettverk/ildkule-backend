-- -----------------------------------------------------
-- Drop legacy tables after the event rename
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS meteor_res_entry ;
DROP TABLE IF EXISTS meteor ;

-- -----------------------------------------------------
-- Table user
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS user ;

CREATE TABLE IF NOT EXISTS user (
  id INT(11) NOT NULL AUTO_INCREMENT,
  username VARCHAR(255) NULL DEFAULT NULL UNIQUE,
  password VARCHAR(255) NULL DEFAULT NULL,
  role VARCHAR(255)  DEFAULT 'ROLE_USER',
  user_level VARCHAR(255) DEFAULT 0,
  tutorial_completed BOOLEAN DEFAULT false,
  confirmed BOOLEAN DEFAULT false,
  confirm_token VARCHAR (1000),
  password_reset_token VARCHAR (1000),
  password_reset_request_time TIMESTAMP NULL,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP NULL,
  PRIMARY KEY (id))
  ;

-- -----------------------------------------------------
-- Table manual_input_observation
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS manual_input_observation ;

CREATE TABLE IF NOT EXISTS manual_input_observation (
  id INT NOT NULL,
  latitude FLOAT NULL,
  longitude FLOAT NULL,
  date_time DATETIME NULL,
  first_recorded_direction VARCHAR(45) NULL,
  first_recorded_altitude VARCHAR(45) NULL,
  last_recorded_direction VARCHAR(45) NULL,
  last_recorded_altitude VARCHAR(45) NULL,
  duration FLOAT NULL,
  color VARCHAR(45) NULL,
  brightness VARCHAR(45) NULL,
  description VARCHAR(280) NULL,
  image_file VARCHAR(45) NULL,
  users_id INT(11) NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_manual_input_observation_users_idx (users_id ASC),
  CONSTRAINT fk_manual_input_observation_users
    FOREIGN KEY (users_id)
    REFERENCES user (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
    
-- -----------------------------------------------------
-- Station
-- -----------------------------------------------------     
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS station ;

CREATE TABLE IF NOT EXISTS station (
  id INT(9) UNSIGNED NOT NULL AUTO_INCREMENT,
  station_name VARCHAR(100) NOT NULL UNIQUE,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  PRIMARY KEY (id));


-- -----------------------------------------------------
-- Table cam
-- -----------------------------------------------------    
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS cam ;

CREATE TABLE IF NOT EXISTS cam (
  id INT(6) UNSIGNED NOT NULL AUTO_INCREMENT,
  station_id INT(6) UNSIGNED NOT NULL,
  cam_name VARCHAR(100) NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  PRIMARY KEY (id),
  INDEX station_id (station_id ASC),
  CONSTRAINT unique_cam_cam_name_station_id UNIQUE(cam_name, station_id)  ,
  CONSTRAINT cam_ibfk_1
    FOREIGN KEY (station_id)
    REFERENCES station (id));


-- -----------------------------------------------------
-- Table event
-- -----------------------------------------------------    
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS event ;

CREATE TABLE IF NOT EXISTS event (
  id INT(9) UNSIGNED NOT NULL AUTO_INCREMENT,
  datetimetag VARCHAR(32) NOT NULL,
  location VARCHAR(100) NULL DEFAULT NULL,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  track_startheight FLOAT NULL DEFAULT NULL,
  track_endheight FLOAT NULL DEFAULT NULL,
  track_groundtrack FLOAT NULL DEFAULT NULL,
  track_course FLOAT NULL DEFAULT NULL,
  track_incidence FLOAT NULL DEFAULT NULL,
  track_speed FLOAT NULL DEFAULT NULL,
  track_speed_source VARCHAR(100) NULL DEFAULT NULL,
  track_startlat FLOAT NULL DEFAULT NULL,
  track_startlong FLOAT NULL DEFAULT NULL,
  track_endlat FLOAT NULL DEFAULT NULL,
  track_endlong FLOAT NULL DEFAULT NULL,
  fit_error FLOAT NULL DEFAULT NULL,
  fit_quality FLOAT NULL DEFAULT NULL,
  radiant_ra FLOAT NULL DEFAULT NULL,
  radiant_dec FLOAT NULL DEFAULT NULL,
  radiant_ecl_long FLOAT NULL DEFAULT NULL,
  radiant_ecl_lat FLOAT NULL DEFAULT NULL,
  radiant_shower VARCHAR(100) NULL DEFAULT NULL,
  radiant_zenith_attractor VARCHAR(100) NULL DEFAULT NULL,
  timestamp VARCHAR(100) NULL DEFAULT NULL,
  date DATETIME NULL DEFAULT NULL,
  camera_confirmed tinyint(1) default null,
  user_confirmed tinyint(1) default null,
  first_seen_at DATETIME NOT NULL,
  last_seen_at DATETIME NULL DEFAULT NULL,
  deleted_at DATETIME NULL DEFAULT NULL,
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  deletion_reason VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (id),
  CONSTRAINT unique_event_datetimetag UNIQUE(datetimetag),
  INDEX event_date_idx (date ASC, id ASC),
  INDEX event_public_list_idx (is_deleted ASC, date DESC, id DESC)
  );


-- -----------------------------------------------------
-- Table observation_cam_data
-- -----------------------------------------------------  
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS observation_cam_data ;

CREATE TABLE IF NOT EXISTS observation_cam_data (
  id INT(9) UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id INT(6) UNSIGNED NOT NULL,
  cam_id INT(6) UNSIGNED NOT NULL,
  observation_key VARCHAR(255) NOT NULL,
  source_hash CHAR(64) NOT NULL,
  event_start_utc DATETIME NULL DEFAULT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  first_seen_at DATETIME NOT NULL,
  last_seen_at DATETIME NULL DEFAULT NULL,
  deleted_at DATETIME NULL DEFAULT NULL,
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  deletion_reason VARCHAR(50) NULL DEFAULT NULL,
  trail_frames INT(11) NULL DEFAULT NULL,
  trail_duration FLOAT NULL DEFAULT NULL,
  trail_slope FLOAT NULL DEFAULT NULL,
  trail_offset FLOAT NULL DEFAULT NULL,
  trail_speed FLOAT NULL DEFAULT NULL,
  trail_correlation FLOAT NULL DEFAULT NULL,
  trail_positions TEXT NULL DEFAULT NULL,
  trail_timestamps TEXT NULL DEFAULT NULL,
  trail_coordinates TEXT NULL DEFAULT NULL,
  trail_ams_coords TEXT NULL DEFAULT NULL,
  trail_centroid TEXT NULL DEFAULT NULL,
  trail_centroid2 TEXT NULL DEFAULT NULL,
  trail_gnomonic TEXT NULL DEFAULT NULL,
  trail_midpoint VARCHAR(1000) NULL DEFAULT NULL,
  trail_arc FLOAT NULL DEFAULT NULL,
  trail_brightness TEXT NULL DEFAULT NULL,
  trail_dct_midpoint INT(9) NULL DEFAULT NULL,
  trail_dct TEXT NULL DEFAULT NULL,
  trail_size TEXT NULL DEFAULT NULL,
  trail_frame_brightness TEXT NULL DEFAULT NULL,
  video_start DATETIME NULL DEFAULT NULL,
  video_end DATETIME NULL DEFAULT NULL,
  video_wallclock DATETIME NULL DEFAULT NULL,
  video_heigth INT(11) NULL DEFAULT NULL,
  video_raw INT(11) NULL DEFAULT NULL,
  video_flash INT(11) NULL DEFAULT NULL,
  config_swidth INT(11) NULL DEFAULT NULL,
  config_sheight INT(11) NULL DEFAULT NULL,
  config_swdec INT(11) NULL DEFAULT NULL,
  config_downscale_thr INT(11) NULL DEFAULT NULL,
  config_mintrail_sec FLOAT NULL DEFAULT NULL,
  config_maxtrail_sec FLOAT NULL DEFAULT NULL,
  config_mintrail FLOAT NULL DEFAULT NULL,
  config_maxtrail FLOAT NULL DEFAULT NULL,
  config_minspeed FLOAT NULL DEFAULT NULL,
  config_maxspeed FLOAT NULL DEFAULT NULL,
  config_minspeed_kms FLOAT NULL DEFAULT NULL,
  config_maxspeed_kms FLOAT NULL DEFAULT NULL,
  config_leveltest INT(11) NULL DEFAULT NULL,
  config_numspots INT(11) NULL DEFAULT NULL,
  config_brightness INT(11) NULL DEFAULT NULL,
  config_flash_thr FLOAT NULL DEFAULT NULL,
  config_lookahead INT(11) NULL DEFAULT NULL,
  config_exit INT(11) NULL DEFAULT NULL,
  config_peak FLOAT NULL DEFAULT NULL,
  config_filter INT(11) NULL DEFAULT NULL,
  config_dct_threshold FLOAT NULL DEFAULT NULL,
  config_correlation FLOAT NULL DEFAULT NULL,
  config_spacing_correlation FLOAT NULL DEFAULT NULL,
  config_gnomonic_correlation FLOAT NULL DEFAULT NULL,
  config_nothreads INT(11) NULL DEFAULT NULL,
  config_lastreport_ts BIGINT(20) NULL DEFAULT NULL,
  config_ts_future INT(11) NULL DEFAULT NULL,
  config_snapshot_interval INT(11) NULL DEFAULT NULL,
  config_snapshot_integration INT(11) NULL DEFAULT NULL,
  config_log_file VARCHAR(45) NULL DEFAULT NULL,
  config_mask_file VARCHAR(45) NULL DEFAULT NULL,
  config_max_file VARCHAR(45) NULL DEFAULT NULL,
  config_save_file VARCHAR(45) NULL DEFAULT NULL,
  config_pto_file VARCHAR(45) NULL DEFAULT NULL,
  config_pto_scale FLOAT NULL DEFAULT NULL,
  config_pto_width FLOAT NULL DEFAULT NULL,
  config_pto_height FLOAT NULL DEFAULT NULL,
  config_execute VARCHAR(45) NULL DEFAULT NULL,
  config_event_dir VARCHAR(45) NULL DEFAULT NULL,
  config_snapshot_dir VARCHAR(45) NULL DEFAULT NULL,
  summary_latitude FLOAT NULL DEFAULT NULL,
  summary_longitude FLOAT NULL DEFAULT NULL,
  summary_elevation INT(11) NULL DEFAULT NULL,
  summary_timestamp DATETIME NULL DEFAULT NULL,
  summary_startpos FLOAT NULL DEFAULT NULL,
  summary_endpos FLOAT NULL DEFAULT NULL,
  summary_duration FLOAT NULL DEFAULT NULL,
  summary_sunalt FLOAT NULL DEFAULT NULL,
  summary_recalibrated INT(11) NULL DEFAULT NULL,
  summary_meteor_probability FLOAT NULL DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX event_id (event_id ASC) ,
  INDEX cam_id (cam_id ASC) ,
  INDEX observation_cam_data_observation_key_idx (observation_key ASC),
  CONSTRAINT uq_observation_key UNIQUE(observation_key),
  CONSTRAINT observation_cam_data_ibfk_1
    FOREIGN KEY (event_id)
    REFERENCES event (id),
  CONSTRAINT observation_cam_data_ibfk_2
    FOREIGN KEY (cam_id)
    REFERENCES cam (id))
;


-- -----------------------------------------------------
-- Table event_res_entry
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS event_res_entry ;

CREATE TABLE IF NOT EXISTS event_res_entry (
  id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  event_id INT(9) UNSIGNED NOT NULL,
  line_no INT(11) NOT NULL,
  entry_type VARCHAR(20) NOT NULL,
  label VARCHAR(20) NULL DEFAULT NULL,
  long1 FLOAT NULL DEFAULT NULL,
  lat1 FLOAT NULL DEFAULT NULL,
  long2 FLOAT NULL DEFAULT NULL,
  lat2 FLOAT NULL DEFAULT NULL,
  height FLOAT NULL DEFAULT NULL,
  raw_line VARCHAR(500) NOT NULL,
  PRIMARY KEY (id),
  INDEX event_res_entry_event_id_idx (event_id ASC),
  CONSTRAINT uq_event_res_entry_line UNIQUE(event_id, line_no),
  CONSTRAINT event_res_entry_ibfk_1
    FOREIGN KEY (event_id)
    REFERENCES event (id)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
;


-- -----------------------------------------------------
-- Table observation_trail_point
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS observation_trail_point ;

CREATE TABLE IF NOT EXISTS observation_trail_point (
  id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  observation_id INT(9) UNSIGNED NOT NULL,
  frame_index INT(11) NOT NULL,
  pixel_x FLOAT NULL DEFAULT NULL,
  pixel_y FLOAT NULL DEFAULT NULL,
  event_timestamp_us BIGINT(20) NULL DEFAULT NULL,
  coord_long FLOAT NULL DEFAULT NULL,
  coord_lat FLOAT NULL DEFAULT NULL,
  ams_coord_long FLOAT NULL DEFAULT NULL,
  ams_coord_lat FLOAT NULL DEFAULT NULL,
  centroid_coord_long FLOAT NULL DEFAULT NULL,
  centroid_coord_lat FLOAT NULL DEFAULT NULL,
  centroid2_coord_long FLOAT NULL DEFAULT NULL,
  centroid2_coord_lat FLOAT NULL DEFAULT NULL,
  gnomonic_x FLOAT NULL DEFAULT NULL,
  gnomonic_y FLOAT NULL DEFAULT NULL,
  brightness FLOAT NULL DEFAULT NULL,
  dct FLOAT NULL DEFAULT NULL,
  size FLOAT NULL DEFAULT NULL,
  frame_brightness FLOAT NULL DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX observation_trail_point_observation_id_idx (observation_id ASC),
  CONSTRAINT uq_observation_trail_point_frame UNIQUE(observation_id, frame_index),
  CONSTRAINT observation_trail_point_ibfk_1
    FOREIGN KEY (observation_id)
    REFERENCES observation_cam_data (id)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
;


-- -----------------------------------------------------
-- Table log_station
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS log_station ;

CREATE TABLE IF NOT EXISTS log_station (
  id INT(11) NOT NULL AUTO_INCREMENT,
  station_name VARCHAR(255) NOT NULL,
  code VARCHAR(255) NOT NULL,
  log_time DATETIME NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id))
;


-- -----------------------------------------------------
-- Table user_review
-- -----------------------------------------------------
DROP TABLE IF EXISTS user_review ;

CREATE TABLE IF NOT EXISTS user_review (
  user_id INT(11) NOT NULL,
  confirmed TINYINT NULL,
  event_id INT(9) UNSIGNED NOT NULL,
  PRIMARY KEY (user_id, event_id),
  INDEX fk_users_has_observation_cam_data_users1_idx (user_id ASC),
  INDEX fk_user_review_event1_idx (event_id ASC),
  
  CONSTRAINT fk_users_has_observation_cam_data_users1
    FOREIGN KEY (user_id)
    REFERENCES user (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_user_review_event1
    FOREIGN KEY (event_id)
    REFERENCES event (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
