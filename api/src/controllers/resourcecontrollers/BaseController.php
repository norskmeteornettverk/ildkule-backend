<?php
abstract class BaseController
{

    function __construct()
  {
    $this->getAndRunMethod();    
  }
   protected function getAndRunMethod()
    {
        if ($_SERVER['REQUEST_METHOD'] === 'GET') {
            $this->get();

        }
        elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $this->post();

        }
        elseif ($_SERVER['REQUEST_METHOD'] === 'PUT') {
            $this->put();

        }
        elseif ($_SERVER['REQUEST_METHOD'] === 'PATCH') {
            $this->patch();

        }
        elseif ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
            $this->delete();
        }
        else {
            http_response_code(403); #Method not allowed
        }
    }


    protected function controlRequest($token)
    {

        if (!$this->isAuthenticated($token)) {
        // default handloing
        }
        elseif (!$this->getRole($token) ) {
        // handle missing role
        }
        elseif (!$this->getLevel($token)) {
        // handle missing level
        }
        elseif (!$this->isJsonValid($token)) {
        // handle missing level
        }
        else {
        // handle the request

        }
    }


    
    protected function isAuthenticated($token): bool
    {
        return is_jwt_valid($token);
    }

    protected function getRole($token)
    {
       return getRolesFromToken($token);
    }

    protected function getLevel($token)
    {
        return getLevelFromToken($token);
    }

    protected function isJsonValid($request)
    {
        return true;
    }

    abstract protected function get();
  

    abstract protected function post();
 

    abstract protected function put();
 

    abstract  protected function patch();
  

    abstract  protected function delete();
 
}