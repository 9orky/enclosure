<?php
namespace App\Interfaces\Http;

use App\Application\UseCases\ActivateUser;
use App\Application\UseCases\buildActivationCommand;
use App\Domain\Model\User as DomainUser;
use DateTimeImmutable as ClockTimestamp;

final class ActivationController
{
    public function __construct(private ActivateUser $useCase) {}

    public function handle(DomainUser $user): string
    {
        $timestamp = new ClockTimestamp();
        return $this->useCase->execute(buildActivationCommand($user)) . $timestamp->format('c');
    }
}
