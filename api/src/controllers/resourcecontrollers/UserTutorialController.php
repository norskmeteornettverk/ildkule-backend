<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'service'.DIRECTORY_SEPARATOR.'UserService.php'; 


if ($_SERVER['REQUEST_METHOD'] === 'PUT') {

    $bearer_token = get_bearer_token();
    $json = "";

    if (is_jwt_valid($bearer_token)) {
        $data = json_decode(file_get_contents("php://input", true));
        $userService = new UserService();
        $userService->tutorialPerformed($id, $data->tutorialComplete);
        echo json_encode(array('msg' => 'Successfully updated'));
    }
    else {
        http_response_code(401); #401 Unauthorized
		echo json_encode(array('error' => 'Unauthorized'));
    }
    if ($json === false or !isset($json)) {
        // Avoid echo of empty string (which is invalid JSON), and
        // JSONify the error message instead:
        $json = json_encode(["jsonError" => json_last_error_msg()]);
        if ($json === false) {
            // This should not happen, but we go all the way now:
            $json = '{"jsonError":"unknown"}';
        }
        // Set HTTP response status code to: 500 - Internal Server Error
        http_response_code(500);
    }
    echo $json;
}
