<?php

class Cam implements JsonSerializable
{
  protected $id;
  protected $cam_name;
  protected $created;

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
