<?php

class User implements JsonSerializable
{ //properties
  protected $id;
  protected $username;
  protected $password;
  protected $role;
  protected $user_level;
  protected $create_time;
  protected $update_time;
  protected $tutorial_completed;
  protected $confirm_token;
  protected $password_reset_token;
  protected $password_reset_request_time;
  protected $confirmed;

  function __construct($username = null, $password = null)
  {
    if (isset($username) && isset($password)) {
      $this->username = $username;
      $this->password = $password;
    }
  }

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

  public function __isset($name)
  {
    $getter = 'get' . ucfirst($name);
    if (method_exists($this, $getter)) {
      return !is_null($this->$getter());
    }
    else {
      return isset($this->$name);
    }
  }

  /* Serializes the object to a value that can be serialized natively by json_encode().    Returns data which can be serialized by json_encode(), which is a value of any type other than a resource. */
  public function jsonSerialize()
  {
    return (object)get_object_vars($this);
  }
}
