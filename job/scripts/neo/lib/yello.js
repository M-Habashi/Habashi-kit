import { un } from './core.js';

export async function yelloPick(p, comboLabel, query, exact) {
  const { text } = await p.snapshot({ mode: 'interactive' });
  const matches = text.split('\n').map(line => line.match(/\bcombobox "((?:\\.|[^"\\])*)"[^\n]*\[ref=([^\]]+)\]/)).filter(m => m && JSON.parse(`"${m[1]}"`) === comboLabel);
  if (matches.length !== 1) throw new Error(`Expected one combobox for ${comboLabel}, found ${matches.length}`);
  const ref = matches[0][2];
  await p.click(ref);
  await p.evaluate(() => {
    const input = document.activeElement;
    if (!(input instanceof HTMLInputElement)) throw new Error('Yello focused input not found');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, '');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await p.insertText(query);
  await p.waitForTime(1200);
  const option = un(await p.evaluate(exact => {
    const input = document.activeElement;
    const list = document.getElementById(input?.getAttribute('aria-controls'));
    const match = el => (el.innerText ?? el.textContent).trim() === exact;
    const el = [...(list?.querySelectorAll('[role=option]') ?? [])].find(match) ??
      [...(list?.querySelectorAll('div') ?? [])].find(el => !el.children.length && match(el));
    if (!el) throw new Error(`Yello option not found: ${exact}`);
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2, inputId: input.id };
  }, exact));
  await p.clickAt(option.x, option.y);
  await p.waitForTime(600);
  const selected = un(await p.evaluate(inputId => {
    const input = document.getElementById(inputId);
    const control = input?.closest('[class*=control]') ?? input?.parentElement;
    return control?.querySelector('[class*=singleValue]')?.textContent.trim();
  }, option.inputId));
  if (selected !== exact) throw new Error(`Yello selection mismatch: expected ${exact}, got ${selected}`);
  return selected;
}
