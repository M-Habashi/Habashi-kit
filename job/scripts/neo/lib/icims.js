import { un } from './core.js';

export async function icimsPick(p, name, query, exact) {
  const anchor = un(await p.evaluate(name => {
    const f = document.querySelector('iframe[src*="icims.com"]') ?? document.querySelector('iframe');
    const el = f?.contentDocument?.getElementById(`${name}_icimsDropdown`);
    if (!el) throw new Error(`iCIMS dropdown not found: ${name}`);
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect(), o = f.getBoundingClientRect();
    return { x: o.x + f.clientLeft + r.x + r.width / 2, y: o.y + f.clientTop + r.y + r.height / 2 };
  }, name));
  await p.clickAt(anchor.x, anchor.y);
  await p.type(query);
  await p.waitForTime(1800);
  const option = un(await p.evaluate(({ name, exact }) => {
    const f = document.querySelector('iframe[src*="icims.com"]') ?? document.querySelector('iframe');
    const el = [...(f?.contentDocument?.getElementById(`${name}_dropdown-results`)?.querySelectorAll('li') ?? [])]
      .find(el => (el.innerText ?? el.textContent).trim() === exact);
    if (!el) throw new Error(`iCIMS option not found: ${exact}`);
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect(), o = f.getBoundingClientRect();
    return { x: o.x + f.clientLeft + r.x + r.width / 2, y: o.y + f.clientTop + r.y + r.height / 2 };
  }, { name, exact }));
  await p.clickAt(option.x, option.y);
  await p.waitForTime(800);
  const selected = un(await p.evaluate(name => {
    const f = document.querySelector('iframe[src*="icims.com"]') ?? document.querySelector('iframe');
    const d = f?.contentDocument;
    const el = d?.getElementsByName(name)[0] ?? d?.getElementById(name);
    return el?.selectedOptions?.[0]?.textContent.trim();
  }, name));
  if (selected !== exact) {
    await p.press('Escape');
    throw new Error(`iCIMS selection mismatch: expected ${exact}, got ${selected}`);
  }
  return selected;
}

export async function icimsPickMany(p, triples) {
  const start = Date.now(), done = [];
  let longest = 2600, elapsed = 0;
  for (const triple of triples) {
    if (Math.max(Date.now() - start, elapsed) + longest >= 24000) break;
    const before = Date.now();
    done.push(await icimsPick(p, ...triple));
    const duration = Math.max(2600, Date.now() - before);
    longest = Math.max(longest, duration);
    elapsed += duration;
  }
  return { done, remaining: triples.slice(done.length) };
}

export async function icimsSetNative(p, values) {
  return un(await p.evaluate(values => {
    const f = document.querySelector('iframe[src*="icims.com"]') ?? document.querySelector('iframe');
    const d = f?.contentDocument;
    if (!d) throw new Error('iCIMS frame unavailable');
    return Object.entries(values).map(([name, value]) => {
      const el = d.getElementsByName(name)[0];
      if (!el) throw new Error(`iCIMS field not found: ${name}`);
      if (el.type === 'checkbox' || el.type === 'radio') el.checked = Boolean(value);
      else if (el.multiple) for (const option of el.options) option.selected = [].concat(value).includes(option.value);
      else el.value = value;
      for (const type of ['input', 'change']) el.dispatchEvent(new d.defaultView.Event(type, { bubbles: true }));
      return { name, value: el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value };
    });
  }, values));
}

export async function icimsDump(p) {
  return un(await p.evaluate(() => {
    const f = document.querySelector('iframe[src*="icims.com"]') ?? document.querySelector('iframe');
    const d = f?.contentDocument;
    if (!d) throw new Error('iCIMS frame unavailable');
    return [...d.querySelectorAll('input, select, textarea')].filter(el => el.type !== 'hidden' && el.getBoundingClientRect().width > 0)
      .map(el => ({ name: el.name, label: [...(el.labels ?? [])].map(l => l.textContent.trim()).join(' '),
        value: el.type === 'checkbox' || el.type === 'radio' ? el.checked : el.value,
        ...(el.options && el.options.length < 20 ? { options: [...el.options].map(o => ({ value: o.value, text: o.textContent.trim() })) } : {}) }));
  }));
}
