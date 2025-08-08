<?php
$data = file_get_contents("php://input");
if (!$data) {
  http_response_code(400);
  echo "No data received";
  exit;
}

file_put_contents("../json/red-beers.json", $data);
echo "Saved successfully";
?>