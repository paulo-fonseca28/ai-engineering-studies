'use strict';
const el = id => document.getElementById(id);
const labels = {received:'Recebido', preparing:'Em preparo', out_for_delivery:'Em entrega', delivered:'Entregue', cancelled:'Cancelado'};
const errors = {order_not_found:'Pedido não encontrado.', order_requires_review_or_is_terminal:'Este estado não permite cancelamento nesta simulação.', proposal_expired:'A proposta expirou. Consulte e prepare outra.', order_changed_since_proposal:'O pedido mudou. Consulte novamente.', proposal_already_confirmed:'Esta proposta já foi confirmada.', idempotency_key_conflict:'Conflito na chave da operação. Consulte o pedido.', simulation_store_unavailable:'A base da simulação está indisponível.'};
let order = null, proposal = null, key = null, busy = false;
let ticket = null, handoffKey = null;
function render() {
  el('search').disabled = busy;
  el('ask').disabled = busy;
  el('refresh-queue').disabled = busy;
  el('handoff').disabled = busy || !ticket || !el('handoff-consent').checked;
  el('order').disabled = busy;
  el('propose').hidden = !order || order.status !== 'received' || !!proposal;
  el('propose').disabled = busy;
  el('review').hidden = !proposal;
  el('confirm').disabled = busy || !proposal || !el('consent').checked;
  el('dismiss').disabled = busy;
  el('consent').disabled = busy;
}
function clearProposal() { proposal = null; key = null; el('consent').checked = false; }
async function api(path, body) {
  const headers = {'Content-Type':'application/json'};
  if (el('token').value.trim()) headers.Authorization = 'Bearer ' + el('token').value.trim();
  const response = await fetch(path, body ? {method:'POST',headers,body:JSON.stringify(body)} : {headers});
  const data = await response.json();
  if (!response.ok) {
    const error = new Error((data.detail === 'authentication_required' ? 'Informe um token válido em Acesso ao ambiente.' : errors[data.detail]) || 'Solicitação recusada. Confira os dados e consulte novamente.');
    error.status = response.status;
    throw error;
  }
  return data;
}
async function run(task) {
  if (busy) return;
  busy = true; el('notice').textContent = 'Processando…'; render();
  try { await task(); } catch(error) { el('notice').textContent = error.message; }
  finally { busy = false; render(); }
}
el('lookup').addEventListener('submit', event => {
  event.preventDefault();
  run(async () => {
    order = null; clearProposal(); el('status').textContent = '';
    order = await api('/simulation/orders/' + encodeURIComponent(el('order').value));
    el('status').textContent = `${order.order_id}: ${labels[order.status]} · versão ${order.version}`;
    el('notice').textContent = order.status === 'received' ? 'Pedido disponível para proposta de cancelamento.' : 'Este estado exige revisão ou já é terminal; não há cancelamento disponível.';
  });
});
el('order').addEventListener('input', () => { order = null; clearProposal(); el('status').textContent = ''; render(); });
el('propose').addEventListener('click', () => run(async () => {
  proposal = await api('/simulation/cancellations/proposals', {order_id:order.order_id});
  key = crypto.randomUUID();
  el('consent').checked = false;
  el('summary').textContent = `${proposal.order_id}: ${labels[proposal.current_status]} → ${labels[proposal.proposed_status]}. Nenhum reembolso será executado.`;
  el('expires').textContent = 'Válida até ' + new Date(proposal.expires_at).toLocaleString('pt-BR');
  el('notice').textContent = 'Revise a proposta antes de confirmar.';
}));
el('consent').addEventListener('change', render);
el('dismiss').addEventListener('click', () => { clearProposal(); el('notice').textContent = 'Proposta descartada nesta tela. Nenhum pedido foi alterado.'; render(); });
el('confirm').addEventListener('click', () => {
  if (!proposal || !el('consent').checked) return;
  run(async () => {
    let result;
    try {
      result = await api('/simulation/cancellations/confirmations', {proposal_id:proposal.proposal_id, confirmed:true, idempotency_key:key});
    } catch(error) {
      if (error.status && error.status < 500) clearProposal();
      else error.message = 'Não foi possível confirmar o resultado. Tente confirmar novamente com esta mesma proposta; a chave da operação será preservada.';
      throw error;
    }
    order = {order_id:result.order_id,status:result.status,version:result.version};
    clearProposal();
    el('status').textContent = `${order.order_id}: ${labels[order.status]} · versão ${order.version}`;
    el('notice').textContent = result.message + '\nExecução: ' + result.execution_id;
  });
});
render();

function showTicket(result) {
  ticket = result; handoffKey = crypto.randomUUID();
  el('handoff-consent').checked = false;
  el('handoff-result').textContent = '';
  el('answer-empty').hidden = true;
  el('answer-content').hidden = false;
  el('answer').textContent = result.answer;
  el('answer-meta').textContent = `Modo ${result.mode} · ${result.inference_status} · revisão necessária`;
  el('trace').textContent = JSON.stringify({trace_id:result.trace_id, duration_ms:result.duration_ms, usage:result.usage, order_source:result.order_source, simulation_order:result.simulation_order, trace:result.trace}, null, 2);
  el('sources').replaceChildren();
  for (const source of result.sources) {
    const li = document.createElement('li');
    for (const [className, text] of [['source-title', source.title + (result.citations.includes(source.id) ? ' · citada' : ' · recuperada')], ['source-text', source.text], ['source-id', source.id]]) {
      const span = document.createElement('span'); span.className = className; span.textContent = text; li.appendChild(span);
    }
    el('sources').appendChild(li);
  }
  if (!result.sources.length) { const li = document.createElement('li'); li.textContent = 'Nenhuma fonte documental nesta resposta.'; el('sources').appendChild(li); }
}
el('ticket-form').addEventListener('submit', event => {
  event.preventDefault();
  run(async () => {
    const requestType = el('request-type').value;
    const body = {question:el('question').value, request_type:requestType};
    if (requestType !== 'policy') { body.order_id = el('order').value; body.order_source = 'simulation'; }
    showTicket(await api('/tickets', body));
    el('notice').textContent = 'Resposta preparada. Confira as fontes e o rastro antes de orientar o atendimento.';
  });
});
el('handoff-consent').addEventListener('change', render);
el('handoff').addEventListener('click', () => {
  if (!ticket || !el('handoff-consent').checked) return;
  run(async () => {
    const result = await api('/handoffs', {trace_id:ticket.trace_id, reason:el('reason').value, confirmed:true, idempotency_key:handoffKey});
    el('handoff-result').textContent = result.message + ' Registro: ' + result.handoff_id;
    el('handoff-consent').checked = false;
    el('notice').textContent = 'Encaminhamento salvo na fila local de revisão.';
  });
});
el('refresh-queue').addEventListener('click', () => run(async () => {
  const entries = await api('/handoffs'); el('queue').replaceChildren();
  for (const entry of entries) {
    const li = document.createElement('li'); li.textContent = entry.reason + ' · ';
    const button = document.createElement('button'); button.className = 'secondary'; button.textContent = 'Inspecionar atendimento';
    button.addEventListener('click', () => run(async () => { showTicket(await api('/tickets/' + entry.trace_id)); el('notice').textContent = 'Atendimento recuperado do histórico.'; }));
    li.appendChild(button); el('queue').appendChild(li);
  }
  if (!entries.length) { const li = document.createElement('li'); li.textContent = 'Nenhum encaminhamento registrado.'; el('queue').appendChild(li); }
  el('notice').textContent = `${entries.length} encaminhamento(s) na fila local (até 100 mais recentes).`;
}));
api('/health').then(health => { el('runtime').textContent = `Modo: ${health.mode}\nBusca: ${health.retrieval}`; }).catch(() => { el('runtime').textContent = 'API indisponível'; });
