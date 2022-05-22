<?php

require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'config.php';
require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'db.php';



header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET");


require_once realpath($_SERVER["DOCUMENT_ROOT"]) . DIRECTORY_SEPARATOR . 'api' . DIRECTORY_SEPARATOR . 'src' . DIRECTORY_SEPARATOR . 'controllers' . DIRECTORY_SEPARATOR . 'resourcecontrollers' . DIRECTORY_SEPARATOR . 'BaseController.php';


header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST");

class InsightDashboardController extends BaseController
{
	protected function get()
	{

		if ($this->resourceId == "cam") {
			$sql = "select  CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)) as Stasjonsnavn, 
c.cam_name as Kameranavn, 
min(m.date) ForsteObservasjonsTidspunkt, 
max(m.date) SisteObervasjonsTidspunkt, 
count(distinct date(m.date)) DagerMedObservasjoner,
DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
count(*) as Kameraopptak, 
count(distinct m.id) as Meteorer, 
count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
from station as s
left outer join cam as c on s.id = c.station_id
left outer join observation_cam_data as d on c.id = d.cam_id
left outer join meteor as m on d.meteor_id = m.id
group by   CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)), c.cam_name
order by  CONCAT(UCASE(LEFT( s.station_name, 1)), 
		SUBSTRING( s.station_name, 2)),c.cam_name";
			$results = dbQuery($sql);
			$rows = array();
			while ($row = dbFetchAssoc($results)) {
				$rows[] = $row;
			}
			echo json_encode($rows);
		}

		if ($this->resourceId == "station") {
			$sql = "select 
		CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2)) as Stasjonsnavn,
	   min(m.date) ForsteObservasjonsTidspunkt, 
	   max(m.date) SisteObervasjonsTidspunkt, 
	   count(distinct date(m.date)) DagerMedObservasjoner,
	   DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
	   count(*) as Kameraopptak, 
	   count(distinct m.id) as Meteorer, 
	   count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
	   COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
	   from station as s
	   left outer join cam as c on s.id = c.station_id
	   left outer join observation_cam_data as d on c.id = d.cam_id
	   left outer join meteor as m on d.meteor_id = m.id
	   group by   CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2))
	   order by  CONCAT(UCASE(LEFT( s.station_name, 1)), 
									SUBSTRING( s.station_name, 2))";
			$results = dbQuery($sql);
			$rows = array();
			while ($row = dbFetchAssoc($results)) {
				$rows[] = $row;
			}
			echo json_encode($rows);
		}


		if ($this->resourceId == "total") {
			$sql = "select  
		min(m.date) ForsteObservasjonsTidspunkt, 
		max(m.date) SisteObervasjonsTidspunkt, 
		count(distinct date(m.date)) DagerMedObservasjoner,
		DATEDIFF(now(),max(m.date)) as DagerSidenSisteObservasjon,
		count(*) as Kameraopptak, 
		count(distinct m.id) as Meteorer, 
		count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
		COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
		from station as s
		left outer join cam as c on s.id = c.station_id
		left outer join observation_cam_data as d on c.id = d.cam_id
		left outer join meteor as m on d.meteor_id = m.id";
			$results = dbQuery($sql);
			$rows = array();
			while ($row = dbFetchAssoc($results)) {
				$rows[] = $row;
			}
			echo json_encode($rows[0]);
		}

		if ($this->resourceId == "coordinates") {
			$sql = "SELECT track_endlat lat, track_endlong lng FROM 153413_ildkule_dev.meteor where track_endlat is not null";
			$results = dbQuery($sql);
			$rows = array();
			while ($row = dbFetchAssoc($results)) {
				$rows[] = $row;
			}
			echo json_encode($rows);
		}
		;


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
