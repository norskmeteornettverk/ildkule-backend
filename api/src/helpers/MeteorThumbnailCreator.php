<?php

class MeteorThumbnailCreator
{
    private $meteorDataFolder;
    private $imageFolder;

    public function __construct($meteorDataFolder, $imageFolder)
    {
        $this->meteorDataFolder = $meteorDataFolder;
        $this->imageFolder = $imageFolder;
    }

    /**
     * Creates thumbnails for meteor image files in the specified directories.
     *
     * This function searches for "image.jpg" files in subdirectories of the
     * $meteorDataFolder directory and creates a thumbnail for each
     * image file in the $imageFolder directory. Thumbnails are only created if
     * they do not already exist.
     *
     * @return array An array containing the following counts:
     *               - image_count: The number of "image.jpg" files found.
     *               - thumbnail_created_count: The number of thumbnails that were created.
     *               - thumbnail_not_created_count: The number of thumbnails that were not created because they already existed.
     */
    public function createMeteorThumbnails()
    {
        $subfolders = glob($this->meteorDataFolder . DIRECTORY_SEPARATOR . '*', GLOB_ONLYDIR);

        $image_count = 0;
        $thumbnail_created_count = 0;

        foreach ($subfolders as $subfolder) {
            $subsubfolders = glob($subfolder . DIRECTORY_SEPARATOR . '*', GLOB_ONLYDIR);

            foreach ($subsubfolders as $subsubfolder) {
                $image_files = glob($subsubfolder . DIRECTORY_SEPARATOR . 'image.jpg');

                foreach ($image_files as $image_file) {
                    $thumbnail_path = $this->imageFolder . DIRECTORY_SEPARATOR . basename($subfolder) . basename($subsubfolder) . '_thumbnail.jpg';

                    if (!file_exists($thumbnail_path)) {
                        $imgHelp = new ImgHelper();
                        // Create a thumbnail 365 pixels wide aligned with the specs of the front-end application
                        $imgHelp->createThumbnail($image_file, $thumbnail_path, 365);
                        $thumbnail_created_count++;
                    }

                    $image_count++;
                }
            }
        }

        return array(
            'image_count' => $image_count,
            'thumbnail_created_count' => $thumbnail_created_count,
        );
    }
}