
#Folder structure:
#Date->Time->Station->Cam
#Example values inline!!

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS observation CASCADE;
SET FOREIGN_KEY_CHECKS = 1;


CREATE TABLE user (
  id int NOT NULL AUTO_INCREMENT,
  username varchar(255) DEFAULT NULL,
  password varchar(255) DEFAULT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE observation (
	 id int(9) unsigned NOT NULL AUTO_INCREMENT,
     datetimetag CHAR(14) NOT NULL,
     place varchar(100) null,
     created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     
track_startheight float null, # 78.7 km
track_endheight float null, # 51.6 km
track_groundtrack float null,# 67.7 km
track_course float null, # 358.1 deg
track_incidence float null,# 21.9 deg
track_speed float null,# 12.6 km/s
track_speed_source varchar(100), # average
fit_error float null, #0.1
fit_quality float null,# 0.84
radiant_ra float null, #319.27 deg
radiant_dec float null, #-8.57 deg
radiant_ecl_long float null, #319.01 deg
radiant_ecl_lat float null, #6.89 deg
radiant_shower varchar(100), # 
radiant_zenith_attractor varchar(100), # uncorrected
timestamp float null, # 1636563790.998572 # hva slags format er dette?
date DATETIME, # Wed Nov 10 17:03:10 2021 # merkelig format, men må parses
   
     PRIMARY KEY (id)
);

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS station CASCADE;
SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE station (
	 id int(9) unsigned NOT NULL AUTO_INCREMENT,
     station_name varchar(100) NOT NULL,     
     created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     PRIMARY KEY (id)
);

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS cam CASCADE;
SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE cam (
    id INT(6) UNSIGNED NOT NULL AUTO_INCREMENT,
    station_id INT(6) UNSIGNED NOT NULL,
    cam_name VARCHAR(100) NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (station_id)
        REFERENCES station (id)
);

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS cam_data CASCADE;
SET FOREIGN_KEY_CHECKS = 1;
CREATE TABLE cam_data (
	 id int(9) unsigned NOT NULL AUTO_INCREMENT,  
     observation_id int(6) unsigned NOT NULL, 
     cam_id int(6) unsigned NOT NULL, 
     created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     PRIMARY KEY (id),
     FOREIGN KEY (observation_id) REFERENCES observation(id),
     FOREIGN KEY (cam_id) REFERENCES cam(id) 
);


insert into user(username, password) value('meteoroide', 'meteoritt');
