import * as path from 'node:path';

import { ActivateUser, buildActivationCommand } from '../../application/use_cases/activate';
import type { User as DomainUser } from '../../domain/model/user';

export class ActivationController {
    constructor(private readonly useCase: ActivateUser) {}

    handle(user: DomainUser): string {
        const command = buildActivationCommand(user);
        return path.join(this.useCase.execute(command), user.id);
    }
}
