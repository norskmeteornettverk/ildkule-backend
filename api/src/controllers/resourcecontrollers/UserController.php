<?php



require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'models' . DIRECTORY_SEPARATOR . 'User.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'DatabaseConnection.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'dao' . DIRECTORY_SEPARATOR . 'UserDao.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'UserService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'BaseController.php';


header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST");

class UserController extends BaseController
{
	protected function get()
	{
		// Get user account
		$bearer_token = get_bearer_token();
		if (is_jwt_valid($bearer_token)) {

			$user = null;
			$userService = new UserService();
			$user = $userService->getUserByID($this->resourceId);

			if (isset($user)) {
				echo json_encode(array('id' => $user->id, 'username' => $user->username, 'user_role' => [$user->role], 'user_level' => $user->username, 'tutorial_completed' => $user->tutorial_completed, 'confirmed' => $user->confirmed));
			}
			else {
				http_response_code(404); #404 Not found
				echo json_encode(array('error' => 'User not found'));
			}
		}
		else {
			http_response_code(401); #401 Unauthorized
			echo json_encode(array('error' => 'Unauthorized'));
		}
	}


	protected function post()
	{
		// Create new account 
		$data = json_decode(file_get_contents("php://input", true));
		$userService = new UserService();
		$userService->createNewUser($data->username, $data->password);
	}


	protected function put()
	{
		http_response_code(403);
	}


	protected function patch()
	{
		http_response_code(403);
	}


	protected function delete()
	{
		http_response_code(403);
	}


}

$controller = new UserController(false, null, null, false, (isset($id) ? (int)$id : null));
$controller->handleRequest();
