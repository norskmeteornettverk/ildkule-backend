<?php 
use PHPUnit\Framework\TestCase;


final class UserTest extends TestCase
{
    public function testCanBeCreatedFromValidEmailAddress(): void
    {
        $this->assertInstanceOf(
            User::class,
             new User('user@example.com', 'serfergfrtg')
        );
    }

    public function testCannotBeCreatedFromInvalidEmailAddress(): void
    {
        $this->expectException(InvalidArgumentException::class);

        new User('userexample.com', 'serfergfrtg');
    }

}