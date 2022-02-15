<?php

class Station implements JsonSerializable
{
  protected $id;
  protected $station_name;
  protected $created;
  public $cams = array();

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
