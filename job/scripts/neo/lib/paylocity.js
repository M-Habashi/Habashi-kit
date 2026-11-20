import { un } from './core.js';

export async function payPick(p, comboRef, exactText) {
  await p.click(comboRef);
  const point = un(await p.evaluate(exactText => {
    const el = [...document.querySelectorAll('li[role=option].rw-list-option')]
      .find(el => (el.innerText ?? el.textContent).trim() === exactText && el.getBoundingClientRect().width > 0);
    if (!el) throw new Error(`Paylocity option not found: ${exactText}`);
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, exactText));
  await p.clickAt(point.x, point.y);
  await p.waitForTime(600);
  const { text } = await p.snapshot({ mode: 'interactive' });
  const line = text.split('\n').find(line => /\bcombobox\b/.test(line) && line.includes(`[ref=${comboRef}]`));
  const value = line?.match(/\[ref=[^\]]+\]:\s*("(?:\\.|[^"\\])*")\s*$/)?.[1];
  const selected = value ? JSON.parse(value).replace(/^open dropdown /, '') : undefined;
  if (selected !== exactText) throw new Error(`Paylocity selection mismatch: expected ${exactText}, got ${selected}`);
  return selected;
}

export async function payReview(p) {
  return un(await p.evaluate(() => {
    const el = document.querySelector('[data-testid="review-page"], .application-review, #application-review, main, [role=main]') ?? document.body;
    return el.innerText ?? el.textContent;
  }));
}

export async function payReviewCheck(p, expected) {
  const lines = (await payReview(p)).split('\n').map(line => line.trim()).filter(Boolean);
  return Object.entries(expected).flatMap(([label, value]) => {
    const index = lines.indexOf(label), actual = index < 0 ? null : lines[index + 1] ?? null;
    return actual === String(value) ? [] : [{ label, expected: String(value), actual }];
  });
}
