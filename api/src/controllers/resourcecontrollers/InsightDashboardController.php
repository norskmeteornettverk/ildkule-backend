<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]).DIRECTORY_SEPARATOR.'api'.DIRECTORY_SEPARATOR.'src'.DIRECTORY_SEPARATOR.'service'.DIRECTORY_SEPARATOR.'MeteorService.php'; 
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'AbstractController.php';

class InsightDashboardController extends AbstractController
{
	protected function get()
	{
		$service = new MeteorService();
		print ($service->getInsight($this->resourceId));
	}


	protected function post()
	{
		http_response_code(403);
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
