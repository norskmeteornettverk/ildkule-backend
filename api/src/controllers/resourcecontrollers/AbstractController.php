<?php
abstract class AbstractController
{

    protected $checkAuthentication;
    protected $role;
    protected $level;
    protected $checkJson;
    protected $resourceId;


    // Following constants are used to help setting the parameters in the constructor so that the developer doesn't need to rember the values
    public const AUTHENTICATION_PERFORM_CONTROL = true;
    public const AUTHENTICATION_IGNORE = false;
    public const REQUEST_PERFORM_CONTROL = true;
    public const REQUEST_IGNORE = false;
    public const USER_LEVEL_HIGH = 3;
    public const USER_LEVEL_MEDIUM = 2;
    public const USER_LEVEL_LOW = 1;
    public const USER_LEVEL_IGNORE = 0;
    public const USER_ROLE_ADMIN = 'ROLE_ADMIN';
    public const USER_ROLE_MODERATOR = 'ROLE_MOD';
    public const USER_ROLE_USER = 'ROLE_USER';
    public const USER_ROLE_IGNORE = 'IGNORE';


    
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
    
    
   /**
    * Handles requests by orchestrating auth before mapping application logic to each method (get, post, put, patch, delete)
    *
    * @return void
    */
    public function handleRequest()
    {
       /*
        $token = get_bearer_token();
        if ($this->checkAuthentication && !$this->isAuthenticated($token)) {
            //If is not logged in or is having incorrect token
            http_response_code(401); #401 Unauthorized
            echo json_encode(array('error' => 'Not authenticated', 'message' => 'Ikke autentisert - du må være innlogget'));
            die();
        }
        elseif (isset($this->role) && $this->role <> 0  && $this->getRole($token) != $this->role) {
            //If the user have insufficiant role
            http_response_code(403); #403 Forbidden
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukerrolle for denne funksjonen'));
            die();
        }
        elseif (isset($this->level) && $this->level <> 0 && $this->getLevel($token) != $this->level) {
            //If the user have insufficiant level
            http_response_code(403); #403 Forbidden
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukernivå for denne funksjonen'));
            die();
        }
        elseif ($this->checkJson && !$this->isJsonValid()) {
            //Check if the format on the payload is correct. It should be validated in the json format
            http_response_code(400); #400 Bad request
            echo json_encode(array('error' => 'Bad request format (json not validated)', 'message' => 'Det er feil i foresporselen'));
            die();
        }
        else {
            // if everything is ok, run the application logic
            $this->getAndRunMethod();
            die();
        }

        */
        $this->getAndRunMethod();

    }

    protected function controlRequest(bool $checkAuthentication, string $role, int $level, bool $checkJson)
    {
        $token = get_bearer_token();

        if (!isset($token) && $checkAuthentication){
            //If user is not logged (not having a token)
            http_response_code(401); #401 Unauthorized
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(array('error' => 'Not authenticated', 'message' => 'Ikke autentisert - du må være innlogget'));
            die();
        } elseif (isset($token) && $checkAuthentication && !$this->isAuthenticated($token)) {
            //If user is having a incorrect token
            http_response_code(401); #401 Unauthorized
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(array('error' => 'Not authenticated', 'message' => 'Ikke autentisert - du må være innlogget'));
            die();
        }
        elseif (isset($role) && $role <> 'IGNORE'  && $this->getRole($token) != $role) {
            //If the user have insufficiant role
            http_response_code(403); #403 Forbidden
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukerrolle for denne funksjonen'));
            die();
        }
        elseif (isset($level) && $level <> 0 && $this->getLevel($token) != $level) {
            //If the user have insufficiant level
            http_response_code(403); #403 Forbidden
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(array('error' => 'Not authorized', 'message' => 'Du har ikke gyldig brukernivå for denne funksjonen'));
            die();
        }
        elseif (isset($checkJson) && !$this->isJsonValid()) {
            //Check if the format on the payload is correct. It should be validated in the json format
            http_response_code(400); #400 Bad request
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(array('error' => 'Bad request format (json not validated)', 'message' => 'Det er feil i foresporselen'));
            die();
        }
        else {
            return true;
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