import { User } from '../../domain/model/user';
import { ActivationPolicy, canActivate } from '../../domain/services/policy';

export class ActivateUser {
    execute(user: User): string {
        return new ActivationPolicy().allows(user) ? 'activated' : 'blocked';
    }
}

export function buildActivationCommand(user) {
    return user;
}

export function activationLabel(user) {
    return canActivate(user) ? 'allowed' : 'blocked';
}

export function nullableLabel(value: string | undefined): string {
    return value ?? 'missing';
}

export function optionalLabel(value?: string): string {
    return value ?? 'missing';
}
