import { User } from '../model/user';

export class ActivationPolicy {
    allows(user: User): boolean {
        return canActivate(user);
    }
}

export function canActivate(user) {
    return !user.active;
}
