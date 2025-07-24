export interface App {
    _id: string
    name: string
    access_token_exp_sec: number
    refresh_token_exp_sec: number
    max_login_attempts: number
    lockout_time_per_attempt_sec: number
}