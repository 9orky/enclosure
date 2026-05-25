<?php
namespace App\Application\UseCases;

use App\Domain\Model\User;
use App\Domain\Services\ActivationPolicy;

final class ActivateUser
{
    public function execute(User $user): string
    {
        return (new ActivationPolicy())->allows($user) ? 'activated' : 'blocked';
    }
}

function buildActivationCommand(User $user): User
{
    return $user;
}

function activationLabel(User $user): string
{
    return $user->active ? 'blocked' : 'allowed';
}

function nullableLabel(?string $value): string
{
    return $value ?? 'missing';
}
