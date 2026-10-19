/** Component-local ownership. A -> B -> A must never revive an old response. */
export class OperationScope {
  private generation = 0;
  private controller?: AbortController;
  private identity: string;
  constructor(identity: string) { this.identity = identity; }
  reset(identity: string) {
    if (identity !== this.identity) { this.stop(); this.identity = identity; }
  }
  capture() { const generation = this.generation; return () => generation === this.generation; }
  stop() { this.generation++; this.controller?.abort(); this.controller = undefined; }
  begin() {
    this.stop();
    const generation = this.generation;
    const controller = this.controller = new AbortController();
    const current = () => generation === this.generation && !controller.signal.aborted;
    return {signal:controller.signal, current, cancel:() => { if (current()) this.stop(); }};
  }
}
