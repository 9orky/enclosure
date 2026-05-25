<?php
namespace App\Domain\Model;

use Stringable;

final class User implements Stringable
{
    public ?string $nickname = null;

    public function __construct(public string $id, public bool $active = false) {}

    public function __toString(): string
    {
        return $this->id;
    }
}
