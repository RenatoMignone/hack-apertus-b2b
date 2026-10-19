import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
afterEach(() => { cleanup(); vi.clearAllMocks(); });
Object.defineProperty(window, 'matchMedia', {value: () => ({matches:true, addEventListener:vi.fn(), removeEventListener:vi.fn()})});
Element.prototype.scrollIntoView = vi.fn();
window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
