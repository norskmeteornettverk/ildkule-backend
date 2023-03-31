<?php


use PHPUnit\Framework\TestCase;

class FileToObjectMapperTest extends TestCase
{
    private $mapper;
    protected function setUp(): void
    {
        $this->mapper = new FileToObjectMapper("data", "20230314", "20230315");
    }

    public function testCanBeCreated(): void
    {
        $this->assertInstanceOf(
            FileToObjectMapper::class,
            new FileToObjectMapper("data", "20230314", "20230315")
        );
    }

    public function testCreateMeteorTag()
    {
        $meteorPath = "2023/03/29/some_meteor";
        $expectedTag = "20230329some_meteor";

        // Using reflection to test private method
        $method = new ReflectionMethod(FileToObjectMapper::class, 'createMeteorTag');   
        $method->setAccessible(true);
        $result = $method->invokeArgs($this->mapper, [$meteorPath]);   

        $this->assertEquals($expectedTag, $result);
    }

    public function testGetLineWords()
    {
        $line = "12.345 67.890";
        $expectedWords = ["12.345", "67.890"];
    
        // Using reflection to test private method
        $method = new ReflectionMethod(FileToObjectMapper::class, 'getLineWords');
        $method->setAccessible(true);
        $result = $method->invokeArgs($this->mapper, [$line]);
    
        $this->assertEquals($expectedWords, $result);
    }
    
    public function testFindResFiles()
    {
        $files = [
            "file1.txt",
            "file2.res",
            "file3.RES",
            "file4.txt",
        ];
        $expectedMatches = [
            1 => "file2.res",
            2 => "file3.RES",
        ];
    
        // Using reflection to test private method
        $method = new ReflectionMethod(FileToObjectMapper::class, 'findResFiles');
        $method->setAccessible(true);
        $result = $method->invokeArgs($this->mapper, [$files]);
    
        $this->assertEquals($expectedMatches, $result);
    }
    

    public function testBuildStatFilePath()
    {
        $meteorPath = "/path/to/meteor";
        $matches = [
            1 => "file2.res",
            2 => "file3.RES",
        ];
        $expectedStatFilePath = "/path/to/meteor/file2.res";
    
        // Using reflection to test private method
        $method = new ReflectionMethod(FileToObjectMapper::class, 'buildStatFilePath');
        $method->setAccessible(true);
        $result = $method->invokeArgs($this->mapper, [$meteorPath, $matches]);
    
        $this->assertEquals($expectedStatFilePath, $result);
    }
    

}