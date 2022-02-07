<?php
interface DaoInterface
{
    public function findAll();
    public function findByID($id);
    public function insert($entity);
    public function delete($entity);
    public function update($entity);
}
