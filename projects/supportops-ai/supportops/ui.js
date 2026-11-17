'use strict';
const el = id => document.getElementById(id);
const labels = {received:'Recebido', preparing:'Em preparo', out_for_delivery:'Em entrega', delivered:'Entregue', cancelled:'Cancelado'};
const errors = {order_not_found:'Pedido não encontrado.', order_requires_review_or_is_terminal:'Este estado não permite cancelamento nesta simulação.', proposal_expired:'A proposta expirou. Consulte e prepare outra.', order_changed_since_proposal:'O pedido mudou. Consulte novamente.', proposal_already_confirmed:'Esta proposta já foi confirmada.', idempotency_key_conflict:'Conflito na chave da operação. Consulte o pedido.', simulation_store_unavailable:'A base da simulação está indisponível.'};
let order = null, proposal = null, key = null, busy = false;
function render() {
  el('search').disabled = busy;
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
  const response = await fetch(path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(errors[data.detail] || 'Solicitação recusada. Confira os dados e consulte novamente.');
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
