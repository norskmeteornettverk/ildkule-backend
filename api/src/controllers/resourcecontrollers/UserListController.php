<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'UserService.php';

$bearer_token = get_bearer_token();

if (is_jwt_valid($bearer_token)) {

	$page = isset($_GET['page']) ? $_GET['page'] : -1;
	$limit = isset($_GET['limit']) ? $_GET['limit'] : 20;
	$orderby = isset($_GET['orderby']) ? $_GET['orderby'] : "date";
	$order = isset($_GET['order']) ? $_GET['order'] : "desc";
	$userService = new UserService();
	$users = $userService->listUsers($page, $limit, $orderby, $order);

	/*
	 * Mapping the user object over to a "data transfer object"
	 * so that we prevent sending over information such as the password hash
	 */
	if ($users) {
		$userDTOList = [];
		foreach ($users as $user) {
			$dto = array('id' => $user->id, 'username' => $user->username, 'role' => $user->role, 'user_level' => $user->user_level, 'tutorial_completed' => $user->tutorial_completed, 'confirmed' => $user->confirmed);
			array_push($userDTOList,$dto);			
		}
		echo json_encode(array('message' => 'User list created', 'users' => $userDTOList));
	}
	else {
		http_response_code(404); #404 Not found
		echo json_encode(array('error' => 'No users found'));
	}
}
else {
	http_response_code(401); #401 Unauthorized
	echo json_encode(array('error' => 'Unauthorized'));
}
