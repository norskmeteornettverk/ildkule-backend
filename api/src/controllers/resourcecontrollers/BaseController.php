<?php
abstract class BaseController
{

    protected $checkAuthentication;
    protected $role;
    protected $level;
    protected $checkJson;

    protected $resourceId;


    function __construct(
        bool $checkAuthentication,
        $role,
        $level,
        bool $checkJson,
        $resourceId = null
        )
    {
        $this->checkAuthentication = $checkAuthentication;
        $this->role = $role;
        $this->level = $level;
        $this->checkJson = $checkJson;
        $this->resourceId = $resourceId;
    }

    public function handleRequest()
    {
        $token = get_bearer_token();
        if ($this->checkAuthentication && !$this->isAuthenticated($token)) {
            http_response_code(401); #401 Unauthorized
            echo json_encode(array('error' => 'Not authenticated', 'message' => 'Ikke autentisert - du må være innlogget'));
            die();
        }
        elseif (isset($this->role) && $this->getRole($token) != $this->role) {
            http_response_code(403); #403 Forbidden
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukerrolle for denne funksjonen'));
            die();
        }
        elseif (isset($this->level) && $this->getLevel($token) != $this->level) {
            http_response_code(403); #403 Forbidden
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukernivå for denne funksjonen'));
            die();
        }
        elseif ($this->checkJson && !$this->isJsonValid()) {
            http_response_code(400); #400 Bad request
            echo json_encode(array('error' => 'Bad request format (json not validated)', 'message' => 'Det er feil i foresporselen'));
            die();
        }
        else {
            $this->getAndRunMethod();
            die();
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

    protected function isJsonValid()
    {
        return true;
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

    abstract protected function get();


    abstract protected function post();


    abstract protected function put();


    abstract protected function patch();


    abstract protected function delete();


}