<?php

use PHPUnit\Framework\TestCase;

final class UserTest extends TestCase
{
    public function testCanBeCreated(): void
    {
        $this->assertInstanceOf(
            User::class , new User()
        );
    }

    public function testCantSetInvalidEmail(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $user = new User();
        $user->username = "test.com";
    }

    public function testCantSetPasswordUnder8Chars(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $user = new User();
        $user->password = "1234567";
    }

    public function testCantSetValidEmail(): void
    {        
        $user = new User();
        $user->username = "test@test.com";
        $this->assertEqualsIgnoringCase( $user->username, "test@test.com");
    }
}