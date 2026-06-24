"""
Genera PNG del stack lean-ctx + Headroom + Honcho para el equipo Nelson.
Uso: python3 render_stack_diagram.py
Output: /tmp/stack-tokens/stack.png
NOTA: emojis no renderizan en el servidor (sin fuente emoji) — se usan simbolos ASCII.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

os.makedirs('/tmp/stack-tokens', exist_ok=True)

fig, ax = plt.subplots(1, 1, figsize=(16, 11))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis('off')

def box(ax, x, y, w, h, color, label, sublabel='', fontsize=13):
    rect = FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.1", linewidth=2,
        edgecolor=color, facecolor=color+'22')
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.35, label,
        ha='center', va='top', fontsize=fontsize,
        fontweight='bold', color=color)
    if sublabel:
        ax.text(x + w/2, y + h - 0.75, sublabel,
            ha='center', va='top', fontsize=9,
            color='#aaaaaa', multialignment='center')

def arrow(ax, x1, y1, x2, y2, color, label=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=2))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.1, my, label, fontsize=8, color=color, va='center')

ax.text(8, 10.5, 'Stack de Ahorro de Tokens - Equipo Nelson / AlegentAI',
    ha='center', va='center', fontsize=16, fontweight='bold', color='#ffffff')

box(ax, 6.5, 9.0, 3, 0.9, '#3498db', '[U] Nelson (WhatsApp)')
box(ax, 6.5, 7.6, 3, 0.9, '#5dade2', '[AI] JARVIS (Hermes Agent)')
arrow(ax, 8, 9.0, 8, 8.5, '#3498db')

# lean-ctx
box(ax, 0.4, 4.5, 4.2, 2.8, '#2ecc71', '(1) lean-ctx', 'In-process / cero latencia', fontsize=12)
for i, t in enumerate([
    'ctx_read -> archivos (10 modos)',
    'ctx_shell -> outputs de terminal',
    'ctx_search -> resultados',
    'Re-reads ~13 tokens (cacheado)',
    'Resuelve: lo que JARVIS LEE',
]):
    ax.text(0.7, 6.8 - i*0.42, t, fontsize=8.5, color='#aaffcc', va='center')

# headroom
box(ax, 5.9, 4.5, 4.2, 2.8, '#f39c12', '(2) Headroom :8787', 'Proxy / 77-85% ahorro', fontsize=12)
for i, t in enumerate([
    'Comprime logs / JSON / code search',
    'JARVIS -> Headroom -> Azure',
    'Agentes hijos tambien pasan aqui',
    'compress_user=true, ratio=0.3',
    'Resuelve: lo que se MANDA al LLM',
]):
    ax.text(6.2, 6.8 - i*0.42, t, fontsize=8.5, color='#fdebd0', va='center')

# honcho
box(ax, 11.4, 4.5, 4.2, 2.8, '#9b59b6', '(3) Honcho :8008', 'Memoria multi-usuario', fontsize=12)
for i, t in enumerate([
    'Workspace: alegent-ai',
    'Peers: nelson, edith, pablo,',
    '  julian, mercedes, jarvis',
    'Contexto aislado por usuario',
    'Resuelve: QUE RECORDAR',
]):
    ax.text(11.7, 6.8 - i*0.42, t, fontsize=8.5, color='#e8daef', va='center')

ax.annotate('', xy=(2.5, 7.3), xytext=(6.8, 7.6),
    arrowprops=dict(arrowstyle='->', color='#2ecc71', lw=2, connectionstyle='arc3,rad=0.2'))
ax.text(3.8, 7.7, 'lee archivos/shell/search', fontsize=8, color='#2ecc71')
arrow(ax, 8, 7.6, 8, 7.3, '#f39c12', 'mensajes al LLM')
ax.annotate('', xy=(13.5, 7.3), xytext=(9.2, 7.6),
    arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2, connectionstyle='arc3,rad=-0.2'))
ax.text(10.5, 7.7, 'consulta/guarda contexto', fontsize=8, color='#9b59b6')

box(ax, 5.9, 2.8, 4.2, 1.1, '#e74c3c', 'Azure Anthropic', 'claude-sonnet-4-6', fontsize=12)
arrow(ax, 8, 4.5, 8, 3.9, '#e74c3c', 'comprimido 77-85%')

savings = FancyBboxPatch((3.5, 1.2), 9, 1.2,
    boxstyle="round,pad=0.1", linewidth=2,
    edgecolor='#e74c3c', facecolor='#1a0505')
ax.add_patch(savings)
ax.text(8, 2.05, 'Ahorro estimado: ~$411 USD/mes',
    ha='center', va='center', fontsize=13, fontweight='bold', color='#e74c3c')
ax.text(8, 1.6, '500 calls/dia  x  77% compresion  x  $3/MTok = $411/mes ahorrado',
    ha='center', va='center', fontsize=10, color='#ffaaaa')

ax.text(0.4, 1.0,
    'FLUJO: Honcho trae contexto  ->  lean-ctx lo comprime  ->  Headroom comprime mensaje  ->  Azure responde',
    fontsize=8.5, color='#888888', va='center')

plt.tight_layout(pad=0.5)
plt.savefig('/tmp/stack-tokens/stack.png', dpi=150, bbox_inches='tight', facecolor='#0d1117')
print("PNG generado: /tmp/stack-tokens/stack.png")
