<?php

class Meteor implements JsonSerializable
{
//properties
  protected $id;
  protected $datetimetag;
  protected $location;
  protected $camera_confirmed;
  protected $user_confirmed;
  protected $date;
  protected $track_startheight;
  protected $track_endheight;
  protected $track_groundtrack;
  protected $track_course;
  protected $track_incidence;
  protected $track_speed;
  protected $track_speed_source;
  protected $track_startlat;
  protected $track_startlong;
  protected $track_endlat;
  protected $track_endlong;  
  protected $fit_error;
  protected $fit_quality;
  protected $radiant_ra;
  protected $radiant_dec;
  protected $radiant_ecl_long;
  protected $radiant_ecl_lat;
  protected $radiant_shower;
  protected $radiant_zenith_attractor;
  protected $timestamp;
  protected array $observation_cam_data = array();
  protected array $user_review = array();

  public function __contruct()
  {
    
  }
//magic getters and setters, fixing it for every property.
  public function &__get($property)
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

/* Serializes the object to a value that can be serialized natively by json_encode(). 
Returns data which can be serialized by json_encode(), which is a value of any type other than a resource. */
  public function jsonSerialize()
  {
    return (object) get_object_vars($this);
  }
}
