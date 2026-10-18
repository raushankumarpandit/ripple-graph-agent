const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {markdown} = require('../static/format.js');
assert.equal(markdown('# Brief\n\n**Impact**\n- Checkout\n- Payments'), '<h3>Brief</h3><p><strong>Impact</strong></p><ul><li>Checkout</li><li>Payments</li></ul>');
assert.equal(markdown('1. Inspect\n2. Review'), '<ol><li>Inspect</li><li>Review</li></ol>');
assert.equal(markdown('```html\n<script>alert(1)</script>\n```'), '<pre><code>&lt;script&gt;alert(1)&lt;/script&gt;</code></pre>');
for (const input of ['<img src=x onerror=alert(1)>', '**<svg onload=alert(1)>**', '[click](javascript:alert(1))', '`<script>alert(1)</script>`']) {
  const output = markdown(input);
  assert.ok(!/<(?:img|svg|script|a)\b/i.test(output), output);
}
const html = fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
const js = fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
assert.equal(ids.length,new Set(ids).size,'Duplicate HTML IDs');
for (const match of js.matchAll(/\$\('([^']+)'\)/g)) assert.ok(ids.includes(match[1]), 'Missing UI element: '+match[1]);
console.log('Brief formatting, unsafe-input escaping and UI reference checks passed.');
