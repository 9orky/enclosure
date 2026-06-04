from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Annotated

import typer

import enclosure.shared.ui

from .. import application

app = typer.Typer(
    help="Open the current project architecture as a pannable browser canvas.",
    invoke_without_command=True,
)


@app.callback()
@enclosure.shared.ui.command_error_boundary
def gui_command(
    llm: Annotated[
        bool,
        typer.Option("--llm", help="Print LLM-focused guidance for this command."),
    ],
    docs: Annotated[
        bool,
        typer.Option(
            "--docs",
            help="Print human-focused documentation for this command.",
        ),
    ],
    host: Annotated[
        str,
        typer.Option("--host", help="Host interface for the local GUI server."),
    ],
    port: Annotated[
        int,
        typer.Option("--port", help="Port for the local GUI server."),
    ],
    open_browser: Annotated[
        bool,
        typer.Option("--open/--no-open", help="Open the GUI in a browser tab."),
    ],
) -> None:
    if llm:
        enclosure.shared.ui.render_llm("llm.tmpl")
        return
    if docs:
        enclosure.shared.ui.render_docs("docs.tmpl")
        return

    snapshot = application.build_gui_snapshot()
    page = _page_html(snapshot.to_json_dict())
    _serve(page, host, port, open_browser)


def _serve(page: str, host: str, port: int, open_browser: bool) -> None:
    page_bytes = page.encode("utf-8")

    class GuiRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page_bytes)))
            self.end_headers()
            self.wfile.write(page_bytes)

    server = ThreadingHTTPServer((host, port), GuiRequestHandler)
    address_host, address_port = server.server_address
    url = f"http://{address_host}:{address_port}/"
    typer.echo(f"Enclosure GUI: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        typer.echo("Stopping Enclosure GUI.")
    finally:
        server.server_close()


def _page_html(snapshot: dict[str, object]) -> str:
    snapshot_json = _script_json(snapshot)
    return _PAGE_TEMPLATE.replace("__SNAPSHOT_JSON__", snapshot_json)


def _script_json(snapshot: dict[str, object]) -> str:
    return (
        json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


_PAGE_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enclosure GUI</title>
<style>
:root {
  color-scheme: dark;
  --bg: #171819;
  --panel: #202326;
  --panel-2: #292d31;
  --line: #3b4147;
  --text: #eff2f3;
  --muted: #a5adb5;
  --accent: #58c4dd;
  --green: #75c46b;
  --yellow: #e1b84f;
  --red: #e35d5b;
  --magenta: #c779d8;
}
* { box-sizing: border-box; }
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, input {
  color: inherit;
  font: inherit;
}
#app {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  grid-template-rows: 52px minmax(0, 1fr);
  width: 100%;
  height: 100%;
}
#toolbar {
  grid-column: 1 / 3;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  background: #1b1e20;
}
.brand {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.brand strong {
  font-size: 15px;
  font-weight: 700;
}
.brand span {
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.segments {
  display: inline-flex;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
.segments button {
  min-width: 92px;
  height: 34px;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  cursor: pointer;
}
.segments button:last-child {
  border-right: 0;
}
.segments button.active {
  background: var(--accent);
  color: #081014;
}
.tool-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  cursor: pointer;
}
#canvas-wrap {
  position: relative;
  min-width: 0;
  min-height: 0;
}
#tree {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
}
#tree.dragging {
  cursor: grabbing;
}
#hud {
  position: absolute;
  left: 12px;
  bottom: 12px;
  display: flex;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
  pointer-events: none;
}
#hud span {
  padding: 5px 7px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: rgba(27, 30, 32, 0.86);
}
#side {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  border-left: 1px solid var(--line);
  background: var(--panel);
}
.panel-section {
  padding: 14px;
  border-bottom: 1px solid var(--line);
}
.panel-section h2 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.metric {
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-2);
}
.metric b {
  display: block;
  font-size: 16px;
}
.metric span,
.empty,
.hint {
  color: var(--muted);
  font-size: 12px;
}
.list {
  display: grid;
  gap: 7px;
}
.item {
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-2);
  font-size: 12px;
}
.item b {
  display: block;
  margin-bottom: 3px;
  color: var(--text);
  font-size: 12px;
}
.item code {
  color: var(--muted);
  word-break: break-word;
}
.shape-control {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 64px;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.shape-control label {
  min-width: 0;
  color: var(--muted);
  font-size: 12px;
}
.shape-control input {
  width: 64px;
  height: 28px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #16191b;
  text-align: right;
}
@media (max-width: 860px) {
  #app {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: 92px minmax(0, 1fr) 260px;
  }
  #toolbar {
    grid-column: 1;
    flex-wrap: wrap;
  }
  .brand {
    flex-basis: 100%;
  }
  #side {
    border-left: 0;
    border-top: 1px solid var(--line);
  }
}
</style>
</head>
<body>
<div id="app">
  <header id="toolbar">
    <div class="brand">
      <strong>Enclosure</strong>
      <span id="subtitle"></span>
    </div>
    <div class="segments" role="group" aria-label="View mode">
      <button type="button" data-mode="boundaries" class="active">Boundaries</button>
      <button type="button" data-mode="symbols">Symbols</button>
      <button type="button" data-mode="shape">Shape</button>
    </div>
    <button type="button" id="fit" class="tool-button" title="Fit tree">⌖</button>
  </header>
  <main id="canvas-wrap">
    <canvas id="tree"></canvas>
    <div id="hud">
      <span>↑ fold</span>
      <span>↓ expand</span>
      <span>drag pan</span>
      <span>wheel zoom</span>
    </div>
  </main>
  <aside id="side"></aside>
</div>
<script type="application/json" id="snapshot-data">__SNAPSHOT_JSON__</script>
<script>
const snapshot = JSON.parse(document.getElementById('snapshot-data').textContent);
const canvas = document.getElementById('tree');
const ctx = canvas.getContext('2d');
const side = document.getElementById('side');
const subtitle = document.getElementById('subtitle');
const state = {
  mode: 'boundaries',
  depth: 2,
  zoom: 1,
  panX: 0,
  panY: 0,
  autoFit: true,
  dragging: false,
  dragX: 0,
  dragY: 0,
  hoverId: '',
  shapeLimits: {...snapshot.shape_config},
};
const files = snapshot.files;
const fileById = new Map(files.map(file => [file.source_id, file]));
const dependencyDegree = new Map();
for (const dependency of snapshot.dependencies) {
  dependencyDegree.set(dependency.source, (dependencyDegree.get(dependency.source) || 0) + dependency.count);
  dependencyDegree.set(dependency.target, (dependencyDegree.get(dependency.target) || 0) + dependency.count);
}
const root = buildTree();
const maxDepth = computeMaxDepth(root);
let visibleNodes = [];
let visibleEdges = [];
let nodeBoxes = [];
let bounds = {minX: 0, minY: 0, maxX: 1, maxY: 1};
const layoutMetrics = {
  columnGap: 260,
  rowGap: 58,
  wrapGap: 178,
  maxZoom: 1.5,
  minZoom: 0.02,
  marginRatio: 0.84,
};
subtitle.textContent = `${snapshot.architecture_root} · ${files.length} files · ${snapshot.files_excluded} excluded`;

function buildTree() {
  const rootNode = makeNode('root', snapshot.architecture_root || '.', 'root', '');
  for (const file of files) {
    const parts = file.source_id.split('/').filter(Boolean);
    let current = rootNode;
    let path = '';
    for (let index = 0; index < parts.length; index += 1) {
      path = path ? `${path}/${parts[index]}` : parts[index];
      const isFile = index === parts.length - 1;
      const id = isFile ? file.source_id : `folder:${path}`;
      let child = current.children.find(item => item.id === id);
      if (!child) {
        child = makeNode(id, parts[index], isFile ? 'file' : 'folder', path);
        current.children.push(child);
      }
      if (isFile) {
        child.file = file;
      }
      current = child;
    }
  }
  sortTree(rootNode);
  return rootNode;
}

function makeNode(id, label, kind, path) {
  return {id, label, kind, path, children: [], file: null, x: 0, y: 0, depth: 0};
}

function sortTree(node) {
  node.children.sort((left, right) => {
    if (left.kind !== right.kind) return left.kind === 'folder' ? -1 : 1;
    return left.label.localeCompare(right.label);
  });
  for (const child of node.children) sortTree(child);
}

function computeMaxDepth(node) {
  if (!node.children.length) return node.depth;
  let max = node.depth;
  for (const child of node.children) {
    child.depth = node.depth + 1;
    max = Math.max(max, computeMaxDepth(child));
  }
  return max;
}

function layout() {
  visibleNodes = [];
  visibleEdges = [];
  collect(root, 0, null);
  const candidate = chooseLayoutCandidate([
    buildColumnLayout(),
    buildFanLayout(),
    buildWrappedLayout(),
  ]);
  applyLayoutCandidate(candidate);
  bounds = measureBounds(candidate.positions);
  if (state.autoFit) fitToBounds();
}

function collect(node, depth, parent) {
  node.depth = depth;
  visibleNodes.push(node);
  if (parent) visibleEdges.push([parent, node]);
  if (depth >= state.depth) return;
  for (const child of node.children) collect(child, depth + 1, node);
}

function buildColumnLayout() {
  const positions = new Map();
  const cursor = {value: 0};
  assignColumnPosition(root, cursor, positions);
  return {name: 'column', positions};
}

function assignColumnPosition(node, cursor, positions) {
  const children = visibleChildren(node);
  let y = 0;
  if (!children.length) {
    y = cursor.value * layoutMetrics.rowGap;
    cursor.value += 1;
  } else {
    for (const child of children) assignColumnPosition(child, cursor, positions);
    const childPositions = children.map(child => positions.get(child.id));
    y = average(childPositions.map(position => position.y));
  }
  positions.set(node.id, {x: node.depth * layoutMetrics.columnGap, y});
}

function buildFanLayout() {
  const positions = new Map();
  const cursor = {value: 0};
  assignFanPosition(root, 0, cursor, positions);
  return {name: 'fan', positions};
}

function assignFanPosition(node, x, cursor, positions) {
  const children = visibleChildren(node);
  let y = 0;
  if (!children.length) {
    y = cursor.value * layoutMetrics.rowGap;
    cursor.value += 1;
  } else {
    const laneGap = Math.max(54, Math.min(128, 760 / Math.max(1, children.length)));
    children.forEach((child, index) => {
      const childX = x + layoutMetrics.columnGap + index * laneGap;
      assignFanPosition(child, childX, cursor, positions);
    });
    const childPositions = children.map(child => positions.get(child.id));
    y = average(childPositions.map(position => position.y));
  }
  positions.set(node.id, {x, y});
}

function buildWrappedLayout() {
  const positions = new Map();
  const levels = nodesByDepth();
  const viewportRatio = canvasAspectRatio();
  for (const [depth, nodes] of levels.entries()) {
    const columns = wrappedColumnCount(nodes.length, viewportRatio);
    const rows = Math.ceil(nodes.length / columns);
    nodes.forEach((node, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      positions.set(node.id, {
        x: depth * layoutMetrics.columnGap + column * layoutMetrics.wrapGap,
        y: (row - (rows - 1) / 2) * layoutMetrics.rowGap,
      });
    });
  }
  return {name: 'wrapped', positions};
}

function chooseLayoutCandidate(candidates) {
  const viewportRatio = canvasAspectRatio();
  let best = candidates[0];
  let bestScore = Number.NEGATIVE_INFINITY;
  for (const candidate of candidates) {
    const candidateBounds = measureBounds(candidate.positions);
    const zoom = fittedZoom(candidateBounds);
    const ratio = boundsAspectRatio(candidateBounds);
    const aspectPenalty = Math.abs(Math.log(ratio / viewportRatio));
    const score = zoom * 100 - aspectPenalty;
    if (score > bestScore) {
      best = candidate;
      bestScore = score;
    }
  }
  return best;
}

function applyLayoutCandidate(candidate) {
  for (const node of visibleNodes) {
    const position = candidate.positions.get(node.id);
    node.x = position.x;
    node.y = position.y;
  }
}

function visibleChildren(node) {
  if (node.depth >= state.depth) return [];
  return node.children;
}

function nodesByDepth() {
  const levels = new Map();
  for (const node of visibleNodes) {
    if (!levels.has(node.depth)) levels.set(node.depth, []);
    levels.get(node.depth).push(node);
  }
  return levels;
}

function wrappedColumnCount(count, viewportRatio) {
  if (count <= 1) return 1;
  const targetColumns = Math.ceil(Math.sqrt(count * Math.max(1, viewportRatio)));
  return Math.max(1, Math.min(count, targetColumns));
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function measureBounds(positions) {
  return visibleNodes.reduce((acc, node) => {
    const position = positions.get(node.id);
    const size = nodeVisualSize(node);
    return {
      minX: Math.min(acc.minX, position.x - size.width / 2),
      minY: Math.min(acc.minY, position.y - size.height / 2),
      maxX: Math.max(acc.maxX, position.x + size.width / 2),
      maxY: Math.max(acc.maxY, position.y + size.height / 2),
    };
  }, {minX: 0, minY: 0, maxX: 1, maxY: 1});
}

function fittedZoom(activeBounds) {
  const width = Math.max(1, canvas.clientWidth);
  const height = Math.max(1, canvas.clientHeight);
  const treeWidth = Math.max(1, activeBounds.maxX - activeBounds.minX);
  const treeHeight = Math.max(1, activeBounds.maxY - activeBounds.minY);
  const fit = Math.min(width / treeWidth, height / treeHeight) * layoutMetrics.marginRatio;
  return Math.min(layoutMetrics.maxZoom, Math.max(layoutMetrics.minZoom, fit));
}

function canvasAspectRatio() {
  return Math.max(1, canvas.clientWidth) / Math.max(1, canvas.clientHeight);
}

function boundsAspectRatio(activeBounds) {
  const width = Math.max(1, activeBounds.maxX - activeBounds.minX);
  const height = Math.max(1, activeBounds.maxY - activeBounds.minY);
  return width / height;
}

function fitToBounds() {
  const width = Math.max(1, canvas.clientWidth);
  const height = Math.max(1, canvas.clientHeight);
  state.zoom = fittedZoom(bounds);
  state.panX = width / 2 - ((bounds.minX + bounds.maxX) / 2) * state.zoom;
  state.panY = height / 2 - ((bounds.minY + bounds.maxY) / 2) * state.zoom;
}

function resize() {
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = Math.max(1, Math.floor(width * ratio));
  canvas.height = Math.max(1, Math.floor(height * ratio));
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  state.autoFit = true;
  layout();
  draw();
}

function draw() {
  ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  ctx.save();
  ctx.translate(state.panX, state.panY);
  ctx.scale(state.zoom, state.zoom);
  nodeBoxes = [];
  drawEdges();
  if (state.mode === 'boundaries') drawDependencyEdges();
  for (const node of visibleNodes) drawNode(node);
  ctx.restore();
}

function drawEdges() {
  ctx.lineWidth = 1.2 / state.zoom;
  ctx.strokeStyle = '#3b4147';
  for (const [from, to] of visibleEdges) {
    ctx.beginPath();
    ctx.moveTo(from.x + 72, from.y);
    ctx.bezierCurveTo(from.x + 150, from.y, to.x - 150, to.y, to.x - 72, to.y);
    ctx.stroke();
  }
}

function drawDependencyEdges() {
  const visibleIds = new Set(visibleNodes.filter(node => node.file).map(node => node.file.source_id));
  ctx.lineWidth = 1 / state.zoom;
  for (const file of files) {
    if (!visibleIds.has(file.source_id)) continue;
    const source = visibleNodes.find(node => node.file && node.file.source_id === file.source_id);
    if (!source) continue;
    for (const targetId of file.imports) {
      if (!visibleIds.has(targetId)) continue;
      const target = visibleNodes.find(node => node.file && node.file.source_id === targetId);
      if (!target) continue;
      const hot = file.boundary_findings.length || target.file.boundary_findings.length;
      ctx.strokeStyle = hot ? 'rgba(227, 93, 91, 0.58)' : 'rgba(88, 196, 221, 0.20)';
      ctx.beginPath();
      ctx.moveTo(source.x + 70, source.y + 12);
      ctx.lineTo(target.x - 70, target.y - 12);
      ctx.stroke();
    }
  }
}

function drawNode(node) {
  const {width, height} = nodeVisualSize(node);
  const x = node.x - width / 2;
  const y = node.y - height / 2;
  const color = nodeColor(node);
  roundedRect(x, y, width, height, 6, color.fill, color.stroke);
  ctx.fillStyle = color.text;
  ctx.font = `${Math.max(10, 12 / Math.sqrt(state.zoom))}px ui-sans-serif, system-ui`;
  ctx.textBaseline = 'middle';
  ctx.fillText(`${nodeIcon(node)} ${trimLabel(node.label, width)}`, x + 10, y + 17);
  if (node.kind === 'file' && node.file.layer_name) {
    ctx.fillStyle = '#a5adb5';
    ctx.font = '10px ui-sans-serif, system-ui';
    ctx.fillText(node.file.layer_name, x + width - 58, y + 17);
  }
  if (node.kind === 'file' && state.mode === 'symbols') drawSymbols(node, x, y, width);
  nodeBoxes.push({node, x, y, width, height});
}

function nodeVisualSize(node) {
  return {
    width: node.kind === 'root' ? 170 : 150,
    height: node.kind === 'file' && state.mode === 'symbols' ? symbolHeight(node) : 34,
  };
}

function drawSymbols(node, x, y, width) {
  const symbols = node.file.symbols.slice(0, 8);
  ctx.font = '10px ui-sans-serif, system-ui';
  for (let index = 0; index < symbols.length; index += 1) {
    const symbol = symbols[index];
    ctx.fillStyle = '#d7dcdf';
    ctx.fillText(`${symbolIcon(symbol.kind)} ${trimLabel(symbol.name, width - 22)}`, x + 12, y + 38 + index * 16);
  }
  if (node.file.symbols.length > symbols.length) {
    ctx.fillStyle = '#a5adb5';
    ctx.fillText(`+${node.file.symbols.length - symbols.length} more`, x + 12, y + 38 + symbols.length * 16);
  }
}

function roundedRect(x, y, width, height, radius, fill, stroke) {
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1.1 / state.zoom;
  ctx.stroke();
}

function nodeColor(node) {
  if (node.kind === 'root') return {fill: '#27343a', stroke: '#58c4dd', text: '#eff2f3'};
  if (node.kind === 'folder') return {fill: '#22272b', stroke: '#49515a', text: '#eff2f3'};
  if (state.mode === 'shape' && simulatedShapeFindings(node.file).length) {
    return {fill: '#3a243d', stroke: '#c779d8', text: '#eff2f3'};
  }
  if (state.mode === 'boundaries' && node.file.boundary_findings.length) {
    return {fill: '#3e2424', stroke: '#e35d5b', text: '#eff2f3'};
  }
  if (state.mode === 'symbols') {
    const moduleHeat = dependencyDegree.get(node.file.module_name) || 0;
    const focus = state.hoverId && node.file.module_name && sameHoverModule(node);
    const heat = Math.min(1, (moduleHeat + (focus ? 5 : 0)) / 12);
    return {
      fill: `rgb(${38 + heat * 72}, ${42 - heat * 10}, ${45 - heat * 12})`,
      stroke: heat > 0.35 ? '#e35d5b' : '#49515a',
      text: '#eff2f3',
    };
  }
  if (node.file.layer_name === 'domain') return {fill: '#223127', stroke: '#75c46b', text: '#eff2f3'};
  if (node.file.layer_name === 'ui') return {fill: '#2f2b22', stroke: '#e1b84f', text: '#eff2f3'};
  return {fill: '#24282c', stroke: '#49515a', text: '#eff2f3'};
}

function sameHoverModule(node) {
  const hovered = fileById.get(state.hoverId);
  return hovered && hovered.module_name === node.file.module_name;
}

function nodeIcon(node) {
  if (node.kind === 'root') return '◎';
  if (node.kind === 'folder') return '▸';
  if (node.file.boundary_findings.length) return '⚠';
  if (node.file.shape_findings.length) return '◆';
  return '◻';
}

function symbolIcon(kind) {
  return {
    class: 'C',
    abstract_class: 'A',
    interface: 'I',
    type: 'T',
    function: 'ƒ',
    method: 'm',
    abstract_method: 'a',
    property: 'p',
    signature: 's',
  }[kind] || '·';
}

function symbolHeight(node) {
  return 40 + Math.min(9, node.file.symbols.length) * 16;
}

function trimLabel(label, width) {
  const limit = Math.max(8, Math.floor(width / 8));
  return label.length > limit ? `${label.slice(0, limit - 1)}…` : label;
}

function renderSide() {
  if (state.mode === 'boundaries') renderBoundaries();
  if (state.mode === 'symbols') renderSymbols();
  if (state.mode === 'shape') renderShape();
}

function renderBoundaries() {
  const findings = files.flatMap(file => file.boundary_findings.map(finding => ({file, finding})));
  side.innerHTML = `
    ${summarySection()}
    <section class="panel-section">
      <h2>Boundary Rules</h2>
      <div class="list">${snapshot.boundary_rules.map(rule => `
        <div class="item"><b>${escapeHtml(rule.source)}</b><code>disallow ${escapeHtml(rule.disallow.join(', ') || 'none')} · allow ${escapeHtml(rule.allow.join(', ') || 'none')}</code></div>
      `).join('') || '<p class="empty">No boundary rules declared.</p>'}</div>
    </section>
    <section class="panel-section">
      <h2>Findings</h2>
      <div class="list">${findings.slice(0, 14).map(item => `
        <div class="item"><b>${escapeHtml(item.file.source_id)}</b><code>${escapeHtml(findingText(item.finding))}</code></div>
      `).join('') || '<p class="empty">No boundary findings.</p>'}</div>
    </section>
    <section class="panel-section">
      <h2>Exclusions</h2>
      <div class="list">${snapshot.exclusions.map(pattern => `<div class="item"><code>${escapeHtml(pattern)}</code></div>`).join('')}</div>
    </section>
  `;
}

function renderSymbols() {
  const symbolCount = files.reduce((total, file) => total + file.symbols.length, 0);
  const topFiles = files.slice().sort((left, right) => right.symbols.length - left.symbols.length).slice(0, 14);
  side.innerHTML = `
    ${summarySection()}
    <section class="panel-section">
      <h2>Symbols</h2>
      <div class="metric-grid">
        <div class="metric"><b>${symbolCount}</b><span>symbols</span></div>
        <div class="metric"><b>${dependencyDegree.size}</b><span>hot modules</span></div>
      </div>
    </section>
    <section class="panel-section">
      <h2>Densest Files</h2>
      <div class="list">${topFiles.map(file => `
        <div class="item"><b>${escapeHtml(file.source_id)}</b><code>${file.symbols.length} symbol(s) · ${escapeHtml(file.module_name || 'unmapped')}</code></div>
      `).join('')}</div>
    </section>
  `;
}

function renderShape() {
  const affected = files.filter(file => simulatedShapeFindings(file).length);
  side.innerHTML = `
    ${summarySection()}
    <section class="panel-section">
      <h2>Live Shape Values</h2>
      <p class="hint">Use -1 to disable a numeric limit.</p>
      ${shapeControl('max_classes_per_file', 'classes per file')}
      ${shapeControl('max_functions_per_file', 'functions per file')}
      ${shapeControl('max_lines_count_per_function', 'lines per function')}
      ${shapeControl('max_methods_per_class', 'methods per class')}
    </section>
    <section class="panel-section">
      <h2>Affected Files</h2>
      <div class="list">${affected.slice(0, 18).map(file => `
        <div class="item"><b>${escapeHtml(file.source_id)}</b><code>${simulatedShapeFindings(file).map(finding => escapeHtml(finding)).join(' · ')}</code></div>
      `).join('') || '<p class="empty">No files affected by current values.</p>'}</div>
    </section>
  `;
  for (const input of side.querySelectorAll('[data-shape-limit]')) {
    input.addEventListener('input', event => {
      state.shapeLimits[event.target.dataset.shapeLimit] = Number(event.target.value);
      renderSide();
      draw();
    });
  }
}

function summarySection() {
  return `
    <section class="panel-section">
      <h2>Project</h2>
      <div class="metric-grid">
        <div class="metric"><b>${files.length}</b><span>files checked</span></div>
        <div class="metric"><b>${snapshot.files_excluded}</b><span>files excluded</span></div>
      </div>
    </section>
  `;
}

function shapeControl(key, label) {
  return `
    <div class="shape-control">
      <label for="${key}">${label}</label>
      <input id="${key}" data-shape-limit="${key}" type="number" value="${state.shapeLimits[key]}">
    </div>
  `;
}

function simulatedShapeFindings(file) {
  const findings = [];
  const counts = symbolCounts(file);
  addLimitFinding(findings, 'classes', counts.classCount, state.shapeLimits.max_classes_per_file);
  addLimitFinding(findings, 'functions', counts.functionCount, state.shapeLimits.max_functions_per_file);
  addLimitFinding(findings, 'methods/class', counts.maxMethods, state.shapeLimits.max_methods_per_class);
  addLimitFinding(findings, 'function lines', counts.maxFunctionLines, state.shapeLimits.max_lines_count_per_function);
  return findings;
}

function symbolCounts(file) {
  const classNames = new Set(file.symbols.filter(symbol => symbol.kind === 'class' || symbol.kind === 'abstract_class').map(symbol => symbol.name));
  const methodCounts = new Map();
  let maxFunctionLines = 0;
  for (const symbol of file.symbols) {
    if (symbol.kind === 'function') maxFunctionLines = Math.max(maxFunctionLines, symbol.line_count);
    if (symbol.kind === 'method' || symbol.kind === 'abstract_method') {
      const owner = symbol.name.split('.')[0];
      methodCounts.set(owner, (methodCounts.get(owner) || 0) + 1);
    }
  }
  return {
    classCount: classNames.size,
    functionCount: file.symbols.filter(symbol => symbol.kind === 'function').length,
    maxMethods: Math.max(0, ...methodCounts.values()),
    maxFunctionLines,
  };
}

function addLimitFinding(findings, label, actual, limit) {
  if (limit >= 0 && actual > limit) findings.push(`${label} ${actual}/${limit}`);
}

function findingText(finding) {
  if (finding.message) return finding.message;
  if (finding.source_id && finding.target_id) return `${finding.source_id} -> ${finding.target_id}`;
  if (finding.path) return finding.path.join(' -> ');
  return JSON.stringify(finding);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function screenToWorld(x, y) {
  return {x: (x - state.panX) / state.zoom, y: (y - state.panY) / state.zoom};
}

function updateHover(x, y) {
  const point = screenToWorld(x, y);
  const box = nodeBoxes.find(item => point.x >= item.x && point.x <= item.x + item.width && point.y >= item.y && point.y <= item.y + item.height);
  state.hoverId = box && box.node.file ? box.node.file.source_id : '';
  draw();
}

canvas.addEventListener('mousedown', event => {
  state.dragging = true;
  state.autoFit = false;
  state.dragX = event.clientX;
  state.dragY = event.clientY;
  canvas.classList.add('dragging');
});
window.addEventListener('mouseup', () => {
  state.dragging = false;
  canvas.classList.remove('dragging');
});
window.addEventListener('mousemove', event => {
  if (state.dragging) {
    state.panX += event.clientX - state.dragX;
    state.panY += event.clientY - state.dragY;
    state.dragX = event.clientX;
    state.dragY = event.clientY;
    draw();
    return;
  }
  updateHover(event.clientX, event.clientY);
});
canvas.addEventListener('wheel', event => {
  event.preventDefault();
  state.autoFit = false;
  const point = screenToWorld(event.clientX, event.clientY);
  const factor = event.deltaY > 0 ? 0.9 : 1.1;
  state.zoom = Math.max(0.08, Math.min(3.5, state.zoom * factor));
  state.panX = event.clientX - point.x * state.zoom;
  state.panY = event.clientY - point.y * state.zoom;
  draw();
}, {passive: false});
window.addEventListener('keydown', event => {
  if (event.key === 'ArrowDown') {
    state.depth = Math.min(maxDepth, state.depth + 1);
    state.autoFit = true;
    layout();
    draw();
  }
  if (event.key === 'ArrowUp') {
    state.depth = Math.max(1, state.depth - 1);
    state.autoFit = true;
    layout();
    draw();
  }
});
for (const button of document.querySelectorAll('[data-mode]')) {
  button.addEventListener('click', () => {
    state.mode = button.dataset.mode;
    for (const sibling of document.querySelectorAll('[data-mode]')) sibling.classList.toggle('active', sibling === button);
    state.autoFit = true;
    layout();
    renderSide();
    draw();
  });
}
document.getElementById('fit').addEventListener('click', () => {
  state.autoFit = true;
  layout();
  draw();
});
window.addEventListener('resize', resize);
resize();
renderSide();
</script>
</body>
</html>
"""


enclosure.shared.ui.set_command_defaults(
    gui_command,
    {
        "llm": False,
        "docs": False,
        "host": "127.0.0.1",
        "port": 8421,
        "open_browser": True,
    },
)


__all__ = ["app"]
