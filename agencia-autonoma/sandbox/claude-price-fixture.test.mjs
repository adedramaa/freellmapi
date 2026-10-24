import test from 'node:test';
import assert from 'node:assert/strict';
import {formatQuote} from './claude-price-fixture.mjs';
test('converts minor units to actual monetary value',()=>{
  assert.equal(formatQuote(12550,'USD'),'$125.50');
  assert.equal(formatQuote(100,'USD'),'$1.00');
  assert.equal(formatQuote(0,'USD'),'$0.00');
});
test('handles Argentine pesos and euro without changing precision',()=>{
  assert.equal(formatQuote(25000,'ARS'),'ARS 250.00');
  assert.equal(formatQuote(123,'EUR'),'€1.23');
});
test('rejects negative, fractional and unsupported values',()=>{
  assert.throws(()=>formatQuote(-1),/Invalid amount/);
  assert.throws(()=>formatQuote(1.1),/Invalid amount/);
  assert.throws(()=>formatQuote(100,'XYZ'),/Unsupported currency/);
});
