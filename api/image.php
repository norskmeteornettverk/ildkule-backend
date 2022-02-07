<?php
  header('Content-Type: image/png');
  readfile("../data/" . $_GET['img']);
?>