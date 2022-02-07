<?php

class User implements JsonSerializable
{

  protected $id;
  protected $username;
  protected $password;
  protected $role;
  protected $user_level;
  protected $create_time;
  protected $update_time;


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
