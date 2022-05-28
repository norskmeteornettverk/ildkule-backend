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

   private function validateEmail($email)
  {
    if (filter_var($email, FILTER_VALIDATE_EMAIL)) {
      return true;
    }
    else {
      return false;
    }
  }

  //validates username as e-mail
  public function setUsername($email)
  {
    if ($this->validateEmail(($email))) {
      $this->username = $email;
    }
    else {
      throw new InvalidArgumentException("Brukernavet er ugyldig");
    }
  }

  //validates username as e-mail
  public function setPassword($password)
  {
    if (strlen($password) >= 8) {
      $hashed_password = password_hash($password, PASSWORD_DEFAULT);
      $this->password = $hashed_password;      
    }
    else {
      throw new InvalidArgumentException("Ugyldig lengde på passord");
    }
  }


  //magic getters and setters, fixing it for every property.
  public function __get($property)
  {
    if (property_exists($this, $property)) {
      if (method_exists($this, $method = 'get' . ucfirst($property))) {
        return $this->$method($property);
      }
      return $this->$property;
    }
  }

  public function __set($property, $value)
  {
    if (property_exists($this, $property)) {
      if (method_exists($this, $method = 'set' . ucfirst($property))) {
        $this->$method($value);
        return $this;
      }
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
