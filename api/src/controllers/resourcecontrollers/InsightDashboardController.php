<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'service' . DIRECTORY_SEPARATOR . 'MeteorService.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';

class InsightDashboardController extends AbstractController
{
	protected function get()
	{
		$service = new MeteorService();
		print($service->getInsight($this->resourceId));
	}

	private function utf8ize($mixed)
	{
		if (is_array($mixed)) {
			foreach ($mixed as $key => $value) {
				$mixed[$key] = $this->utf8ize($value);
			}
		} elseif (is_string($mixed)) {
			return mb_convert_encoding($mixed, 'UTF-8', 'ISO-8859-1');
		}
		return $mixed;
	}



	protected function post()
	{
		$validRequest = $this->controlRequest(AbstractController::AUTHENTICATION_IGNORE, AbstractController::USER_ROLE_IGNORE, AbstractController::USER_LEVEL_IGNORE, AbstractController::REQUEST_PERFORM_CONTROL);
		if (!$validRequest)
			return;

		$data = json_decode(file_get_contents("php://input", true));

		$meteorService = new MeteorService();
		$result = $meteorService->getMeteorCoordinateData($data->from_date, $data->to_date, $data->stations);

		http_response_code(200);
		header('Content-Type: application/json');		

		$data_utf8 = $this->utf8ize($result);
		$json = json_encode($data_utf8);

		if ($json === false) {
			echo "JSON encoding error: " . json_last_error_msg();
		} else {
			echo $json;
		}

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

$controller = new InsightDashboardController(false, null, null, false, $reportname);
$controller->handleRequest();

//End of file
