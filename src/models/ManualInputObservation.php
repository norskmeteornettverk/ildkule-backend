<?php

class ManuaInputObservation implements JsonSerializable
{

  protected $id;
  protected $latitude;
  protected $longitude;
  protected $date_time;
  protected $first_recorded_direction;
  protected $first_recorded_altitude;
  protected $last_recorded_direction;
  protected $last_recorded_altitude;
  protected $duration;
  protected $color;
  protected $brightness;
  protected $description; 
  protected $image_file;
  protected $user;


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
