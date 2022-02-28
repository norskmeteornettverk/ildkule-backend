<?php

class ManuaInputObservation implements JsonSerializable
{
//properties
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

//magic getters and setters, fixing it for every property.
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

  /* Serializes the object to a value that can be serialized natively by json_encode(). 
Returns data which can be serialized by json_encode(), which is a value of any type other than a resource. */
  public function jsonSerialize()
  {
    return (object) get_object_vars($this);
  }
}
