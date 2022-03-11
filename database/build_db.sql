-- -----------------------------------------------------
-- Table user
-- -----------------------------------------------------
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS user ;

CREATE TABLE IF NOT EXISTS user (
  id INT(11) NOT NULL AUTO_INCREMENT,
  username VARCHAR(255) NULL DEFAULT NULL UNIQUE,
  password VARCHAR(255) NULL DEFAULT NULL,
  role VARCHAR(255) NULL,
  user_level SMALLINT NULL,
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
-- Table meteor
-- -----------------------------------------------------    
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS meteor ;

CREATE TABLE IF NOT EXISTS meteor (
  id INT(9) UNSIGNED NOT NULL AUTO_INCREMENT,
  datetimetag CHAR(14) NOT NULL,
  location VARCHAR(100) NULL DEFAULT NULL,
  create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  track_startheight FLOAT NULL DEFAULT NULL,
  track_endheight FLOAT NULL DEFAULT NULL,
  track_groundtrack FLOAT NULL DEFAULT NULL,
  track_course FLOAT NULL DEFAULT NULL,
  track_incidence FLOAT NULL DEFAULT NULL,
  track_speed FLOAT NULL DEFAULT NULL,
  track_speed_source VARCHAR(100) NULL DEFAULT NULL,
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
  camera_confirmed bit default null,
  PRIMARY KEY (id));


-- -----------------------------------------------------
-- Table observation_cam_data
-- -----------------------------------------------------  
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS observation_cam_data ;

CREATE TABLE IF NOT EXISTS observation_cam_data (
  id INT(9) UNSIGNED NOT NULL AUTO_INCREMENT,
  meteor_id INT(6) UNSIGNED NOT NULL,
  cam_id INT(6) UNSIGNED NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP() ON UPDATE CURRENT_TIMESTAMP(),
  trail_frames INT(11) NULL DEFAULT NULL,
  trail_duration FLOAT NULL DEFAULT NULL,
  trail_slope FLOAT NULL DEFAULT NULL,
  trail_offset FLOAT NULL DEFAULT NULL,
  trail_speed FLOAT NULL DEFAULT NULL,
  trail_correlation FLOAT NULL DEFAULT NULL,
  trail_positions VARCHAR(1000) NULL DEFAULT NULL,
  trail_timestamps VARCHAR(1000) NULL DEFAULT NULL,
  trail_coordinates VARCHAR(1000) NULL DEFAULT NULL,
  trail_gnomonic VARCHAR(1000) NULL DEFAULT NULL,
  trail_midpoint VARCHAR(1000) NULL DEFAULT NULL,
  trail_arc FLOAT NULL DEFAULT NULL,
  trail_brightness VARCHAR(1000) NULL DEFAULT NULL,
  trail_dct_midpoint INT(9) NULL DEFAULT NULL,
  trail_dct VARCHAR(1000) NULL DEFAULT NULL,
  trail_size VARCHAR(1000) NULL DEFAULT NULL,
  trail_frame_brightness VARCHAR(1000) NULL DEFAULT NULL,
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
  INDEX meteor_id (meteor_id DESC) ,
  INDEX cam_id (cam_id ASC) ,
  CONSTRAINT observation_cam_data_ibfk_1
    FOREIGN KEY (meteor_id)
    REFERENCES meteor (id),
  CONSTRAINT observation_cam_data_ibfk_2
    FOREIGN KEY (cam_id)
    REFERENCES cam (id))
;


-- -----------------------------------------------------
-- Table user_review
-- -----------------------------------------------------
DROP TABLE IF EXISTS user_review ;

CREATE TABLE IF NOT EXISTS user_review (
  users_id INT(11) NOT NULL,
  confirmed TINYINT NULL,
  meteor_id INT(9) UNSIGNED NOT NULL,
  PRIMARY KEY (users_id, meteor_id),
  INDEX fk_users_has_observation_cam_data_users1_idx (users_id ASC),
  INDEX fk_user_review_meteor1_idx (meteor_id ASC),
  CONSTRAINT fk_users_has_observation_cam_data_users1
    FOREIGN KEY (users_id)
    REFERENCES user (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_user_review_meteor1
    FOREIGN KEY (meteor_id)
    REFERENCES meteor (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
-- -----------------------------------------------------
-- Table test data
-- -----------------------------------------------------
insert into user (username, password) values ('test', 'test')