/**
 * frontend/segmentation.js
 * Advanced Interactive Pixel/Region Highlighter & Segmentation Viewer for SatQuery AI.
 * Powered by SAM 2 (Segment Anything Model 2) & Adaptive RS Engine.
 */

class SatQuerySegmentationViewer {
  constructor(options) {
    this.container = options.container;
    this.apiBase = options.apiBase || '';
    this.onMasksChanged = options.onMasksChanged || (() => {});
    this.onStatusChanged = options.onStatusChanged || (() => {});

    // Image state
    this.image = null;
    this.imageId = null;
    this.imageUrl = null;
    this.isGeoTIFF = false;
    this.rasterMeta = null;

    // Viewport Transform (Pan & Zoom)
    this.zoom = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.minZoom = 0.1;
    this.maxZoom = 25.0;

    // Active Tool: 'point', 'box', 'polygon', 'brush', 'pan'
    this.activeTool = 'point';
    this.promptPolarity = 'positive'; // 'positive' or 'negative'

    // Brush settings
    this.brushRadius = 18;
    this.brushMode = 'add'; // 'add' or 'erase'
    this.brushPoints = [];
    this.isBrushing = false;

    // Drawing Interaction State
    this.isDraggingPan = false;
    this.isDrawingBox = false;
    this.boxStart = null;
    this.boxCurrent = null;

    this.polygonPoints = []; // in image coords
    this.currentMousePos = { x: 0, y: 0 }; // in image coords

    // Masks State & History
    this.masks = []; // List of mask objects
    this.activeMaskIndex = -1;
    this.opacity = 0.55;
    this.showMasks = true;
    this.showContours = true;

    // Undo / Redo Stacks
    this.undoStack = [];
    this.redoStack = [];

    // Setup DOM elements and Canvases
    this._initDOM();
    this._attachEvents();
    this.checkBackendStatus();
  }

  _initDOM() {
    this.container.innerHTML = `
      <div class="seg-viewer-root" style="position:relative; width:100%; height:100%; display:flex; flex-direction:column; background:#060911; border-radius:8px; overflow:hidden; border:1px solid var(--panel-line, #1c2740);">
        <!-- Top Info Overlay -->
        <div class="seg-top-bar" style="position:absolute; top:8px; left:8px; right:8px; z-index:10; display:flex; justify-content:space-between; align-items:center; pointer-events:none;">
          <div style="display:flex; gap:6px; pointer-events:auto;">
            <span id="segEngineBadge" class="engine-pill" style="margin:0; font-size:10px; background:rgba(10,15,26,0.85); backdrop-filter:blur(4px);">Engine: SAM 2 Ready</span>
            <span id="segGeoBadge" class="engine-pill" style="display:none; margin:0; font-size:10px; border-color:var(--amber, #f0a94e); color:var(--amber, #f0a94e); background:rgba(10,15,26,0.85); backdrop-filter:blur(4px);">GeoTIFF</span>
          </div>
          <div style="display:flex; gap:6px; pointer-events:auto;">
            <div class="seg-coords-pill" id="segCoordsPill" style="font-family:'JetBrains Mono',monospace; font-size:10px; padding:3px 8px; border-radius:4px; background:rgba(10,15,26,0.85); border:1px solid rgba(79,216,196,0.25); color:var(--ink-dim, #7c8aa8);">X: 0 | Y: 0</div>
            <div class="seg-zoom-pill" id="segZoomPill" style="font-family:'JetBrains Mono',monospace; font-size:10px; padding:3px 8px; border-radius:4px; background:rgba(10,15,26,0.85); border:1px solid rgba(79,216,196,0.25); color:var(--teal, #4fd8c4);">100%</div>
          </div>
        </div>

        <!-- Canvas Container -->
        <div class="seg-canvas-wrap" style="position:relative; flex:1; width:100%; min-height:420px; cursor:crosshair; overflow:hidden;">
          <canvas id="segMainCanvas" style="position:absolute; top:0; left:0; width:100%; height:100%; display:block;"></canvas>
          <div id="segEmptyPlaceholder" style="position:absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--ink-dim, #7c8aa8); font-size:13px; pointer-events:none;">
            <div style="font-size:32px; margin-bottom:8px; opacity:0.7;">🛰️</div>
            <div>Upload or select a satellite image to start interactive segmentation</div>
            <div style="font-size:11px; font-family:'JetBrains Mono',monospace; margin-top:4px; opacity:0.6;">Supports Point · Bounding Box · Polygon · Brush · Natural Language AI</div>
          </div>
          <div id="segLoadingSpinner" style="display:none; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); background:rgba(10,15,26,0.85); border:1px solid var(--teal, #4fd8c4); padding:10px 18px; border-radius:8px; font-size:12px; font-family:'JetBrains Mono'; color:var(--teal, #4fd8c4); z-index:20; backdrop-filter:blur(4px);">
            <span class="spinner" style="display:inline-block; width:12px; height:12px; border:2px solid var(--teal, #4fd8c4); border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; vertical-align:middle; margin-right:6px;"></span>
            <span id="segLoadingText">Segmenting region with SAM 2…</span>
          </div>
        </div>

        <!-- Floating Zoom & Fit Controls -->
        <div style="position:absolute; bottom:12px; right:12px; z-index:10; display:flex; gap:4px;">
          <button type="button" class="source-pill active" id="btnZoomIn" title="Zoom In" style="padding:4px 8px; font-size:11px;">🔍+</button>
          <button type="button" class="source-pill active" id="btnZoomOut" title="Zoom Out" style="padding:4px 8px; font-size:11px;">🔍−</button>
          <button type="button" class="source-pill" id="btnZoomFit" title="Fit to Screen" style="padding:4px 8px; font-size:11px;">[⤢] Fit</button>
          <button type="button" class="source-pill" id="btnZoom100" title="Reset to 100%" style="padding:4px 8px; font-size:11px;">1:1</button>
        </div>
      </div>
    `;

    this.canvas = this.container.querySelector('#segMainCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.coordsPill = this.container.querySelector('#segCoordsPill');
    this.zoomPill = this.container.querySelector('#segZoomPill');
    this.engineBadge = this.container.querySelector('#segEngineBadge');
    this.geoBadge = this.container.querySelector('#segGeoBadge');
    this.emptyPlaceholder = this.container.querySelector('#segEmptyPlaceholder');
    this.loadingBox = this.container.querySelector('#segLoadingSpinner');
    this.loadingText = this.container.querySelector('#segLoadingText');

    this._resizeCanvas();
  }

  _resizeCanvas() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.render();
  }

  async checkBackendStatus() {
    try {
      const res = await fetch(`${this.apiBase}/api/segment/status`);
      if (res.ok) {
        const data = await res.json();
        this.engineBadge.textContent = data.engine;
        if (data.sam2_loaded) {
          this.engineBadge.style.borderColor = 'var(--teal)';
          this.engineBadge.style.color = 'var(--teal)';
        }
      }
    } catch (e) {
      console.warn('Could not query segmentation status:', e);
    }
  }

  loadImage(imageUrl, imageId, isGeoTIFF = false, rasterMeta = null) {
    this.showLoading(true, 'Loading satellite raster…');
    this.imageId = imageId;
    this.imageUrl = imageUrl;
    this.isGeoTIFF = isGeoTIFF;
    this.rasterMeta = rasterMeta;

    if (this.isGeoTIFF) {
      this.geoBadge.style.display = 'inline-block';
      this.geoBadge.textContent = rasterMeta?.crs || 'GeoTIFF';
    } else {
      this.geoBadge.style.display = 'none';
    }

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      this.image = img;
      this.emptyPlaceholder.style.display = 'none';
      this.masks = [];
      this.undoStack = [];
      this.redoStack = [];
      this.polygonPoints = [];
      this.brushPoints = [];
      this.fitToScreen();
      this.showLoading(false);
      this.onMasksChanged(this.masks);
      this.render();
    };
    img.onerror = () => {
      this.showLoading(false);
      alert('Failed to load image for segmentation.');
    };
    img.src = imageUrl.startsWith('http') || imageUrl.startsWith('data:') ? imageUrl : `${this.apiBase}${imageUrl}`;
  }

  fitToScreen() {
    if (!this.image) return;
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = (rect.width - 24) / this.image.width;
    const scaleY = (rect.height - 24) / this.image.height;
    this.zoom = Math.min(scaleX, scaleY, 1.0);
    this.panX = (rect.width - this.image.width * this.zoom) / 2;
    this.panY = (rect.height - this.image.height * this.zoom) / 2;
    this.updateZoomPill();
    this.render();
  }

  setZoom(newZoom, centerX = null, centerY = null) {
    if (!this.image) return;
    const rect = this.canvas.getBoundingClientRect();
    const cx = centerX !== null ? centerX : rect.width / 2;
    const cy = centerY !== null ? centerY : rect.height / 2;

    const clampedZoom = Math.max(this.minZoom, Math.min(this.maxZoom, newZoom));
    const factor = clampedZoom / this.zoom;

    this.panX = cx - (cx - this.panX) * factor;
    this.panY = cy - (cy - this.panY) * factor;
    this.zoom = clampedZoom;

    this.updateZoomPill();
    this.render();
  }

  updateZoomPill() {
    if (this.zoomPill) {
      this.zoomPill.textContent = `${Math.round(this.zoom * 100)}%`;
    }
  }

  showLoading(visible, text = 'Processing…') {
    if (this.loadingBox) {
      this.loadingBox.style.display = visible ? 'block' : 'none';
      if (this.loadingText) this.loadingText.textContent = text;
    }
  }

  // --------------------------------------------------------------------------
  // Coordinate Mapping
  // --------------------------------------------------------------------------

  screenToImageCoords(screenX, screenY) {
    if (!this.image) return { x: 0, y: 0 };
    const rect = this.canvas.getBoundingClientRect();
    const canvasX = screenX - rect.left;
    const canvasY = screenY - rect.top;

    const imgX = (canvasX - this.panX) / this.zoom;
    const imgY = (canvasY - this.panY) / this.zoom;

    return {
      x: Math.max(0, Math.min(this.image.width, imgX)),
      y: Math.max(0, Math.min(this.image.height, imgY)),
      inside: imgX >= 0 && imgX <= this.image.width && imgY >= 0 && imgY <= this.image.height,
    };
  }

  imageToScreenCoords(imgX, imgY) {
    const canvasX = imgX * this.zoom + this.panX;
    const canvasY = imgY * this.zoom + this.panY;
    const rect = this.canvas.getBoundingClientRect();
    return {
      screenX: canvasX + rect.left,
      screenY: canvasY + rect.top,
      canvasX,
      canvasY,
    };
  }

  // --------------------------------------------------------------------------
  // Event Handling
  // --------------------------------------------------------------------------

  _attachEvents() {
    window.addEventListener('resize', () => this._resizeCanvas());

    this.container.querySelector('#btnZoomIn').addEventListener('click', () => this.setZoom(this.zoom * 1.3));
    this.container.querySelector('#btnZoomOut').addEventListener('click', () => this.setZoom(this.zoom / 1.3));
    this.container.querySelector('#btnZoomFit').addEventListener('click', () => this.fitToScreen());
    this.container.querySelector('#btnZoom100').addEventListener('click', () => this.setZoom(1.0));

    // Mouse Wheel Zoom
    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.18 : 1 / 1.18;
      this.setZoom(this.zoom * factor, mouseX, mouseY);
    }, { passive: false });

    // Mouse Down
    this.canvas.addEventListener('mousedown', (e) => {
      if (!this.image) return;
      const imgPos = this.screenToImageCoords(e.clientX, e.clientY);

      // Pan with Middle Click or Space Key or 'pan' tool
      if (e.button === 1 || this.activeTool === 'pan' || e.spaceKey) {
        this.isDraggingPan = true;
        this.lastMouse = { x: e.clientX, y: e.clientY };
        return;
      }

      if (e.button !== 0) return; // Only primary click for drawing

      if (this.activeTool === 'point') {
        this.handlePointClick(imgPos.x, imgPos.y, this.promptPolarity === 'positive');
      } else if (this.activeTool === 'box') {
        this.isDrawingBox = true;
        this.boxStart = { x: imgPos.x, y: imgPos.y };
        this.boxCurrent = { x: imgPos.x, y: imgPos.y };
      } else if (this.activeTool === 'polygon') {
        this.polygonPoints.push([imgPos.x, imgPos.y]);
        this.render();
      } else if (this.activeTool === 'brush') {
        this.isBrushing = true;
        this.brushPoints = [[imgPos.x, imgPos.y]];
        this.render();
      }
    });

    // Mouse Move
    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.image) return;
      const imgPos = this.screenToImageCoords(e.clientX, e.clientY);
      this.currentMousePos = imgPos;

      if (this.coordsPill) {
        let text = `X: ${Math.round(imgPos.x)} | Y: ${Math.round(imgPos.y)}`;
        if (this.isGeoTIFF && this.rasterMeta?.bounding_box) {
          const [s, w, n, e_coord] = this.rasterMeta.bounding_box;
          const lat = n - (imgPos.y / this.image.height) * (n - s);
          const lng = w + (imgPos.x / this.image.width) * (e_coord - w);
          text += ` | 📍 ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
        }
        this.coordsPill.textContent = text;
      }

      if (this.isDraggingPan) {
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        this.panX += dx;
        this.panY += dy;
        this.lastMouse = { x: e.clientX, y: e.clientY };
        this.render();
        return;
      }

      if (this.isDrawingBox) {
        this.boxCurrent = { x: imgPos.x, y: imgPos.y };
        this.render();
      } else if (this.isBrushing) {
        this.brushPoints.push([imgPos.x, imgPos.y]);
        this.render();
      } else if (this.activeTool === 'polygon' && this.polygonPoints.length > 0) {
        this.render();
      } else if (this.activeTool === 'brush') {
        this.render();
      }
    });

    // Mouse Up
    window.addEventListener('mouseup', (e) => {
      if (this.isDraggingPan) {
        this.isDraggingPan = false;
      }

      if (this.isDrawingBox) {
        this.isDrawingBox = false;
        if (this.boxStart && this.boxCurrent) {
          const xmin = Math.min(this.boxStart.x, this.boxCurrent.x);
          const xmax = Math.max(this.boxStart.x, this.boxCurrent.x);
          const ymin = Math.min(this.boxStart.y, this.boxCurrent.y);
          const ymax = Math.max(this.boxStart.y, this.boxCurrent.y);

          // Only submit if dragged beyond tiny threshold
          if (xmax - xmin > 4 && ymax - ymin > 4) {
            this.handleBoxComplete(xmin, ymin, xmax, ymax);
          }
        }
        this.boxStart = null;
        this.boxCurrent = null;
      }

      if (this.isBrushing) {
        this.isBrushing = false;
        if (this.brushPoints.length > 0) {
          this.handleBrushComplete();
        }
      }
    });

    // Double Click to finish Polygon
    this.canvas.addEventListener('dblclick', (e) => {
      if (this.activeTool === 'polygon' && this.polygonPoints.length >= 3) {
        this.handlePolygonComplete();
      }
    });
  }

  // --------------------------------------------------------------------------
  // Actions & Backend API Calls
  // --------------------------------------------------------------------------

  pushUndoState() {
    // Deep clone masks
    const clone = this.masks.map(m => ({ ...m }));
    this.undoStack.push(clone);
    this.redoStack = [];
    if (this.undoStack.length > 20) this.undoStack.shift();
  }

  undo() {
    if (this.undoStack.length === 0) return;
    const current = this.masks.map(m => ({ ...m }));
    this.redoStack.push(current);
    this.masks = this.undoStack.pop();
    this.onMasksChanged(this.masks);
    this.render();
  }

  redo() {
    if (this.redoStack.length === 0) return;
    const current = this.masks.map(m => ({ ...m }));
    this.undoStack.push(current);
    this.masks = this.redoStack.pop();
    this.onMasksChanged(this.masks);
    this.render();
  }

  clearActiveMask() {
    if (this.activeMaskIndex >= 0 && this.activeMaskIndex < this.masks.length) {
      this.pushUndoState();
      this.masks.splice(this.activeMaskIndex, 1);
      this.activeMaskIndex = this.masks.length - 1;
      this.onMasksChanged(this.masks);
      this.render();
    }
  }

  resetAllMasks() {
    if (this.masks.length > 0) {
      this.pushUndoState();
      this.masks = [];
      this.activeMaskIndex = -1;
      this.polygonPoints = [];
      this.brushPoints = [];
      this.onMasksChanged(this.masks);
      this.render();
    }
  }

  async handlePointClick(x, y, isPositive = true) {
    this.showLoading(true, isPositive ? 'SAM 2 segmenting object…' : 'Refining mask (- negative seed)…');
    const color = this._getNextColor();
    const label = `Region #${this.masks.length + 1}`;

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('x', x);
    form.append('y', y);
    form.append('is_positive', isPositive ? 'true' : 'false');
    form.append('display_width', this.image.width);
    form.append('display_height', this.image.height);
    form.append('label', label);
    form.append('color', color);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/point`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this._addOrUpdateMask(data);
    } catch (err) {
      alert(`Segmentation error: ${err.message}`);
    } finally {
      this.showLoading(false);
    }
  }

  async handleBoxComplete(xmin, ymin, xmax, ymax) {
    this.showLoading(true, 'SAM 2 segmenting bounding box…');
    const color = this._getNextColor();
    const label = `Box Region #${this.masks.length + 1}`;

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('xmin', xmin);
    form.append('ymin', ymin);
    form.append('xmax', xmax);
    form.append('ymax', ymax);
    form.append('display_width', this.image.width);
    form.append('display_height', this.image.height);
    form.append('label', label);
    form.append('color', color);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/box`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this._addOrUpdateMask(data);
    } catch (err) {
      alert(`Box segmentation error: ${err.message}`);
    } finally {
      this.showLoading(false);
    }
  }

  async handlePolygonComplete() {
    if (this.polygonPoints.length < 3) return;
    this.showLoading(true, 'Constraining SAM 2 to polygon boundary…');
    const color = this._getNextColor();
    const label = `Polygon Area #${this.masks.length + 1}`;

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('points', JSON.stringify(this.polygonPoints));
    form.append('display_width', this.image.width);
    form.append('display_height', this.image.height);
    form.append('label', label);
    form.append('color', color);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/polygon`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this._addOrUpdateMask(data);
    } catch (err) {
      alert(`Polygon segmentation error: ${err.message}`);
    } finally {
      this.polygonPoints = [];
      this.showLoading(false);
    }
  }

  async handleBrushComplete() {
    if (this.brushPoints.length === 0 || this.activeMaskIndex < 0) {
      this.brushPoints = [];
      return;
    }

    const activeMask = this.masks[this.activeMaskIndex];
    if (!activeMask) {
      this.brushPoints = [];
      return;
    }

    this.showLoading(true, 'Updating mask with manual brush…');

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('mask_rle', JSON.stringify(activeMask.rle));
    form.append('brush_stroke', JSON.stringify({
      points: this.brushPoints,
      radius: this.brushRadius,
      mode: this.brushMode,
    }));
    form.append('display_width', this.image.width);
    form.append('display_height', this.image.height);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/refine`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      this._updateActiveMaskData(data);
    } catch (err) {
      console.error('Brush refine error:', err);
    } finally {
      this.brushPoints = [];
      this.showLoading(false);
    }
  }

  async highlightWithAI(textQuery) {
    if (!textQuery || !textQuery.trim()) return;
    this.showLoading(true, `VLM grounding & SAM 2 segmenting: "${textQuery}"…`);

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('query', textQuery.trim());
    form.append('display_width', this.image.width);
    form.append('display_height', this.image.height);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/text`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      if (data.regions && data.regions.length > 0) {
        this.pushUndoState();
        for (const reg of data.regions) {
          await this._addMaskDirect({
            id: reg.id || `ai-reg-${Date.now()}`,
            label: reg.label,
            category: reg.category || 'other',
            color: reg.color || '#4fd8c4',
            rle: reg.rle,
            stats: reg.stats,
            contours: reg.contours,
            mask_png_base64: reg.mask_png_base64,
            visible: true,
          });
        }
        this.onMasksChanged(this.masks);
        this.render();
      } else {
        alert('No distinct region could be segmented for that query.');
      }
      return data;
    } catch (err) {
      alert(`AI text highlight error: ${err.message}`);
    } finally {
      this.showLoading(false);
    }
  }

  async highlightBiTemporalChanges(beforeId, afterId, query) {
    this.showLoading(true, 'Computing bi-temporal difference & SAM 2 change masks…');

    const form = new FormData();
    form.append('before_image_id', beforeId);
    form.append('after_image_id', afterId);
    form.append('query', query || 'Highlight changes between the two images');

    try {
      const res = await fetch(`${this.apiBase}/api/segment/change`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      if (data.change_regions && data.change_regions.length > 0) {
        this.pushUndoState();
        for (const reg of data.change_regions) {
          await this._addMaskDirect({
            id: reg.id || `change-${Date.now()}`,
            label: reg.label,
            category: 'change',
            color: reg.color || '#e74c3c',
            rle: reg.rle,
            stats: reg.stats,
            contours: reg.contours,
            mask_png_base64: reg.mask_png_base64,
            visible: true,
          });
        }
        this.onMasksChanged(this.masks);
        this.render();
      }
      return data;
    } catch (err) {
      alert(`Bi-temporal change highlight error: ${err.message}`);
    } finally {
      this.showLoading(false);
    }
  }

  // --------------------------------------------------------------------------
  // Mask State Helpers
  // --------------------------------------------------------------------------

  _getNextColor() {
    const palette = ['#4fd8c4', '#e67e22', '#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e74c3c', '#1abc9c'];
    return palette[this.masks.length % palette.length];
  }

  async _addOrUpdateMask(data) {
    this.pushUndoState();
    const maskObj = {
      id: `mask-${Date.now()}`,
      label: data.label || `Region #${this.masks.length + 1}`,
      category: data.category || 'other',
      color: data.color || '#4fd8c4',
      rle: data.rle,
      stats: data.stats,
      contours: data.contours,
      mask_png_base64: data.mask_png_base64,
      visible: true,
    };
    await this._prepareMaskImage(maskObj);
    this.masks.push(maskObj);
    this.activeMaskIndex = this.masks.length - 1;
    this.onMasksChanged(this.masks);
    this.render();
  }

  async _addMaskDirect(maskObj) {
    await this._prepareMaskImage(maskObj);
    this.masks.push(maskObj);
    this.activeMaskIndex = this.masks.length - 1;
  }

  async _updateActiveMaskData(data) {
    this.pushUndoState();
    const activeMask = this.masks[this.activeMaskIndex];
    activeMask.rle = data.rle;
    activeMask.stats = data.stats;
    activeMask.contours = data.contours;
    activeMask.mask_png_base64 = data.mask_png_base64;
    await this._prepareMaskImage(activeMask);
    this.onMasksChanged(this.masks);
    this.render();
  }

  _prepareMaskImage(maskObj) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        maskObj.maskImg = img;
        resolve();
      };
      img.onerror = () => resolve();
      img.src = maskObj.mask_png_base64;
    });
  }

  // --------------------------------------------------------------------------
  // Rendering
  // --------------------------------------------------------------------------

  render() {
    const rect = this.canvas.getBoundingClientRect();
    this.ctx.clearRect(0, 0, rect.width, rect.height);

    if (!this.image) return;

    this.ctx.save();
    this.ctx.translate(this.panX, this.panY);
    this.ctx.scale(this.zoom, this.zoom);

    // 1. Draw Original Satellite Image
    this.ctx.drawImage(this.image, 0, 0);

    // 2. Draw Semi-Transparent Mask Overlays & Outlines
    if (this.showMasks && this.masks.length > 0) {
      for (let i = 0; i < this.masks.length; i++) {
        const m = this.masks[i];
        if (!m.visible) continue;

        // Draw colored mask pixels
        if (m.maskImg) {
          this.ctx.save();
          this.ctx.globalAlpha = this.opacity;
          // Tint color using destination-in / source-over composite
          const offCanvas = document.createElement('canvas');
          offCanvas.width = this.image.width;
          offCanvas.height = this.image.height;
          const offCtx = offCanvas.getContext('2d');
          offCtx.fillStyle = m.color;
          offCtx.fillRect(0, 0, offCanvas.width, offCanvas.height);
          offCtx.globalCompositeOperation = 'destination-in';
          offCtx.drawImage(m.maskImg, 0, 0);

          this.ctx.drawImage(offCanvas, 0, 0);
          this.ctx.restore();
        }

        // Draw Boundary Contours
        if (this.showContours && m.contours && m.contours.length > 0) {
          this.ctx.save();
          this.ctx.strokeStyle = m.color;
          this.ctx.lineWidth = Math.max(1.5, 2.5 / this.zoom);
          this.ctx.shadowColor = 'rgba(0,0,0,0.8)';
          this.ctx.shadowBlur = 4;

          for (const poly of m.contours) {
            if (poly.length < 3) continue;
            this.ctx.beginPath();
            this.ctx.moveTo(poly[0][0], poly[0][1]);
            for (let j = 1; j < poly.length; j++) {
              this.ctx.lineTo(poly[j][0], poly[j][1]);
            }
            this.ctx.closePath();
            this.ctx.stroke();
          }
          this.ctx.restore();
        }
      }
    }

    // 3. Draw Active Interaction Tools
    if (this.isDrawingBox && this.boxStart && this.boxCurrent) {
      const x = Math.min(this.boxStart.x, this.boxCurrent.x);
      const y = Math.min(this.boxStart.y, this.boxCurrent.y);
      const w = Math.abs(this.boxCurrent.x - this.boxStart.x);
      const h = Math.abs(this.boxCurrent.y - this.boxStart.y);

      this.ctx.save();
      this.ctx.strokeStyle = '#4fd8c4';
      this.ctx.lineWidth = Math.max(1.5, 2.0 / this.zoom);
      this.ctx.setLineDash([4 / this.zoom, 4 / this.zoom]);
      this.ctx.fillStyle = 'rgba(79, 216, 196, 0.2)';
      this.ctx.fillRect(x, y, w, h);
      this.ctx.strokeRect(x, y, w, h);
      this.ctx.restore();
    }

    if (this.activeTool === 'polygon' && this.polygonPoints.length > 0) {
      this.ctx.save();
      this.ctx.strokeStyle = '#4fd8c4';
      this.ctx.fillStyle = 'rgba(79, 216, 196, 0.15)';
      this.ctx.lineWidth = Math.max(1.5, 2.0 / this.zoom);

      this.ctx.beginPath();
      this.ctx.moveTo(this.polygonPoints[0][0], this.polygonPoints[0][1]);
      for (let i = 1; i < this.polygonPoints.length; i++) {
        this.ctx.lineTo(this.polygonPoints[i][0], this.polygonPoints[i][1]);
      }
      this.ctx.lineTo(this.currentMousePos.x, this.currentMousePos.y);
      this.ctx.stroke();

      // Vertex dots
      for (const pt of this.polygonPoints) {
        this.ctx.fillStyle = '#4fd8c4';
        this.ctx.beginPath();
        this.ctx.arc(pt[0], pt[1], 4 / this.zoom, 0, Math.PI * 2);
        this.ctx.fill();
      }
      this.ctx.restore();
    }

    if (this.activeTool === 'brush') {
      // Brush cursor circle
      this.ctx.save();
      this.ctx.strokeStyle = this.brushMode === 'erase' ? '#e74c3c' : '#4fd8c4';
      this.ctx.lineWidth = Math.max(1.0, 1.5 / this.zoom);
      this.ctx.beginPath();
      this.ctx.arc(this.currentMousePos.x, this.currentMousePos.y, this.brushRadius, 0, Math.PI * 2);
      this.ctx.stroke();

      // Active stroke
      if (this.isBrushing && this.brushPoints.length > 0) {
        this.ctx.fillStyle = this.brushMode === 'erase' ? 'rgba(231,76,60,0.3)' : 'rgba(79,216,196,0.3)';
        for (const pt of this.brushPoints) {
          this.ctx.beginPath();
          this.ctx.arc(pt[0], pt[1], this.brushRadius, 0, Math.PI * 2);
          this.ctx.fill();
        }
      }
      this.ctx.restore();
    }

    this.ctx.restore();
  }

  // --------------------------------------------------------------------------
  // Exporting
  // --------------------------------------------------------------------------

  exportPNGComposite() {
    if (!this.image) return;
    const off = document.createElement('canvas');
    off.width = this.image.width;
    off.height = this.image.height;
    const ctx = off.getContext('2d');
    ctx.drawImage(this.image, 0, 0);

    for (const m of this.masks) {
      if (!m.visible || !m.maskImg) continue;
      const tint = document.createElement('canvas');
      tint.width = off.width;
      tint.height = off.height;
      const tCtx = tint.getContext('2d');
      tCtx.fillStyle = m.color;
      tCtx.fillRect(0, 0, tint.width, tint.height);
      tCtx.globalCompositeOperation = 'destination-in';
      tCtx.drawImage(m.maskImg, 0, 0);

      ctx.globalAlpha = this.opacity;
      ctx.drawImage(tint, 0, 0);

      if (this.showContours && m.contours) {
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = m.color;
        ctx.lineWidth = 3;
        for (const poly of m.contours) {
          if (poly.length < 3) continue;
          ctx.beginPath();
          ctx.moveTo(poly[0][0], poly[0][1]);
          for (let j = 1; j < poly.length; j++) ctx.lineTo(poly[j][0], poly[j][1]);
          ctx.closePath();
          ctx.stroke();
        }
      }
    }

    const a = document.createElement('a');
    a.href = off.toDataURL('image/png');
    a.download = `satquery_highlighted_${this.imageId || 'image'}.png`;
    a.click();
  }

  async exportBackendMask(format = 'binary_png') {
    if (this.activeMaskIndex < 0 || !this.masks[this.activeMaskIndex]) {
      alert('Please select a mask layer to export.');
      return;
    }
    const m = this.masks[this.activeMaskIndex];

    const form = new FormData();
    form.append('image_id', this.imageId);
    form.append('mask_rle', JSON.stringify(m.rle));
    form.append('export_format', format);
    form.append('color', m.color);
    form.append('opacity', this.opacity);

    try {
      const res = await fetch(`${this.apiBase}/api/segment/export`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const ext = format === 'geotiff' ? 'tif' : 'png';
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `satquery_${m.label.replace(/\s+/g, '_')}_${format}.${ext}`;
      a.click();
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    }
  }
}

// Attach to window object
window.SatQuerySegmentationViewer = SatQuerySegmentationViewer;
