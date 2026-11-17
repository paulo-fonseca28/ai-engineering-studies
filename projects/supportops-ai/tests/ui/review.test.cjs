const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

test('explicit consent, retry with same key, successful rendering and input invalidation', async () => {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id, {value:'DEMO-1001', checked:false, handlers:{}, addEventListener(event, fn){this.handlers[event] = fn;}});
    return elements.get(id);
  };
  const requests = [];
  let failures = 1;
  const context = vm.createContext({document:{getElementById:element}, crypto:{randomUUID:()=> 'stable-key-0001'}, fetch:async (url, options) => {
    const body = options?.body ? JSON.parse(options.body) : undefined;
    requests.push({url,body});
    let data;
    if (url.includes('/confirmations')) {
      if (failures--) throw new Error('network lost');
      data = {order_id:'DEMO-1001',status:'cancelled',version:2,message:'Cancelamento simulado.',execution_id:'exec-1'};
    } else if (url.includes('/proposals')) data = {proposal_id:'a'.repeat(32),order_id:'DEMO-1001',current_status:'received',proposed_status:'cancelled',expires_at:'2030-01-01T00:00:00Z'};
    else data = {order_id:'DEMO-1001',status:'received',version:1};
    return {ok:true,json:async()=>data};
  }});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../../supportops/ui.js'),'utf8'), context);
  const trigger = async (id,event='click') => { element(id).handlers[event]({preventDefault(){}}); await new Promise(resolve=>setImmediate(resolve)); };
  await trigger('lookup','submit');
  assert.equal(element('propose').hidden,false);
  await trigger('propose');
  assert.equal(element('confirm').disabled,true);
  await trigger('confirm');
  assert.equal(requests.filter(r=>r.url.includes('/confirmations')).length,0);
  element('consent').checked = true;
  await trigger('consent','change');
  await trigger('confirm');
  assert.equal(element('review').hidden,false);
  assert.match(element('notice').textContent,/mesma proposta/);
  await trigger('confirm');
  const confirms = requests.filter(r=>r.url.includes('/confirmations'));
  assert.deepEqual(confirms[0].body,confirms[1].body);
  assert.equal(element('review').hidden,true);
  assert.match(element('status').textContent,/Cancelado/);
  assert.equal(element('propose').hidden,true);
  await trigger('order','input');
  assert.equal(element('status').textContent,'');
});
