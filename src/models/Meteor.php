<?php

class Meteor implements JsonSerializable {

    protected $id;    
    protected $datetimetag;
    protected $location;
    protected $cameraconfirmed;    
    protected $date;
    protected $track_startheight;
    protected $track_endheight;
    protected $track_groundtrack;
    protected $track_course;
    protected $track_incidence;
    protected $track_speed;
    protected $track_speed_source;
    protected $fit_error;
    protected $fit_quality;
    protected $radiant_ra;
    protected $radiant_dec;
    protected $radiant_ecl_long;
    protected $radiant_ecl_lat;
    protected $radiant_shower;
    protected $radiant_zenith_attractor;
    protected $timestamp;

    public function __get($property) {
        if (property_exists($this, $property)) {
          return $this->$property;
        }
      }
    
    public function __set($property, $value) {
        if (property_exists($this, $property)) {
          $this->$property = $value;
        }    
        return $this;
      }

      public function jsonSerialize() {
        return (object) get_object_vars($this);
    }

}