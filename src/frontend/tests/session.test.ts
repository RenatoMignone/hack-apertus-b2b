import assert from 'node:assert/strict';
import test from 'node:test';
import { serverFormats, setAccessToken, setCapabilities } from '../src/api/session.ts';

test('capabilities require the supported API and export formats reset on disconnect', () => {
  for (const value of [null, {}, { schema_version: '2', frontend_transport: 'polling', formats: ['pdf'] }]) {
    assert.throws(() => setCapabilities(value), /supported Navigator API/);
  }
  setCapabilities({ schema_version: '1', frontend_transport: 'polling', formats: ['pdf'] });
  setAccessToken('synthetic-session-only');
  assert.deepEqual(serverFormats(), ['pdf']);
  setAccessToken('');
  assert.deepEqual(serverFormats(), []);
});
