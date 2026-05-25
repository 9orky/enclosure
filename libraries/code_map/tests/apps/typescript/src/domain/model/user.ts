import crypto from 'node:crypto';

export class User {
    nickname?: string;

    constructor(public readonly id: string, public readonly active: boolean = false) {}

    fingerprint(): string {
        return crypto.createHash('sha1').update(this.id).digest('hex');
    }
}
