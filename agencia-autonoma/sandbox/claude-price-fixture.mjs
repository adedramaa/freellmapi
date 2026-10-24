/**
 * FICTIONAL QA FIXTURE for a controlled Claude Code edit. No client data.
 * Bug is intentional: amountMinor must be converted to major currency units.
 */
export function formatQuote(amountMinor,currency='USD'){
  if(!['ARS','USD','EUR'].includes(currency))throw new Error('Unsupported currency');
  if(!Number.isSafeInteger(amountMinor)||amountMinor<0)throw new Error('Invalid amount');
  return new Intl.NumberFormat('en-US',{style:'currency',currency}).format(amountMinor);
}
