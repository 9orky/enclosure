<?php
namespace App\Domain\Services;

use App\Domain\Model\User;

final class ActivationPolicy
{
    public function allows(User $user): bool
    {
        return canActivate($user);
    }
}

function canActivate(User $user): bool
{
    return !$user->active;
}
