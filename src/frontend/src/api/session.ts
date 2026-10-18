// Operator access token only. Provider/database credentials never enter this app.
// Deliberately memory-only: refresh requires reconnecting, server jobs keep running.
let token = '';
export const accessToken = () => token;
export const setAccessToken = (value: string) => { token = value; };
