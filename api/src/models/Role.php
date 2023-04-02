<?php

class Role implements JsonSerializable
{
// properties
  protected $id;
  protected $role_name;
 
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
  public function jsonSerialize(): Mixed
  {
    return (object) get_object_vars($this);
  }
}
