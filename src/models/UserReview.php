<?php

class UserReview implements JsonSerializable
{
  protected $user;
  protected $confirmed;
  protected $meteor;

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
