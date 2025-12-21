(function () {
  const root = document.getElementById('partypad-root');
  const stageContainer = document.getElementById('partypad-stage');
  const objectsScript = document.getElementById('partypad-objects');

  if (!root || !stageContainer || !objectsScript || !window.Konva) {
    return;
  }

  const csrfToken = root.dataset.csrfToken;
  const padId = root.dataset.padId;
  const uploadUrl = root.dataset.uploadUrl;
  const upsertUrl = root.dataset.upsertUrl;
  const deleteUrlTemplate = root.dataset.deleteUrlTemplate;
  const wsUrl = root.dataset.wsUrl;

  const playerKey = 'partypad-player-name';
  let playerName = localStorage.getItem(playerKey);
  if (!playerName) {
    playerName = `Player_${Math.random().toString(36).substring(7)}`;
    localStorage.setItem(playerKey, playerName);
  }

  const objects = new Map();
  let selectedId = null;
  let copiedObject = null;
  let cursorPosition = { x: 0, y: 0 };

  const stage = new Konva.Stage({
    container: stageContainer,
    width: root.clientWidth,
    height: root.clientHeight,
  });
  const layer = new Konva.Layer();
  stage.add(layer);
  const transformer = new Konva.Transformer({
    rotateEnabled: true,
    ignoreStroke: true,
  });
  layer.add(transformer);

  const resizeStage = () => {
    stage.width(root.clientWidth);
    stage.height(root.clientHeight);
  };
  window.addEventListener('resize', resizeStage);

  const stagePointer = () => stage.getPointerPosition() || cursorPosition;

  const updateCursor = () => {
    const pos = stagePointer();
    if (pos) {
      cursorPosition = { x: pos.x, y: pos.y };
    }
  };

  const selectNode = (node, id) => {
    selectedId = id;
    transformer.nodes([node]);
    layer.batchDraw();
  };

  const clearSelection = () => {
    selectedId = null;
    transformer.nodes([]);
    layer.batchDraw();
  };

  stage.on('mousedown', (e) => {
    if (e.evt.button === 2) {
      return;
    }
    if (e.target === stage) {
      clearSelection();
    }
  });

  stage.on('mousemove', updateCursor);
  stageContainer.addEventListener('contextmenu', (e) => e.preventDefault());

  let isPanning = false;
  let lastPanPos = null;

  stage.on('mousedown', (e) => {
    if (e.evt.button !== 2) return;
    isPanning = true;
    lastPanPos = stage.getPointerPosition();
    e.evt.preventDefault();
  });

  stage.on('mouseup', () => {
    isPanning = false;
    lastPanPos = null;
  });

  stage.on('mousemove', (e) => {
    if (!isPanning) return;
    const pos = stage.getPointerPosition();
    if (!pos || !lastPanPos) return;
    const dx = pos.x - lastPanPos.x;
    const dy = pos.y - lastPanPos.y;
    stage.position({
      x: stage.x() + dx,
      y: stage.y() + dy,
    });
    lastPanPos = pos;
    stage.batchDraw();
    e.evt.preventDefault();
  });

  stage.on('wheel', (e) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const mousePointTo = {
      x: pointer.x / oldScale - stage.x() / oldScale,
      y: pointer.y / oldScale - stage.y() / oldScale,
    };
    const direction = e.evt.deltaY < 0 ? 1 : -1;
    const newScale = direction > 0 ? oldScale * scaleBy : oldScale / scaleBy;
    stage.scale({ x: newScale, y: newScale });
    stage.position({
      x: -(mousePointTo.x - pointer.x / newScale) * newScale,
      y: -(mousePointTo.y - pointer.y / newScale) * newScale,
    });
    stage.batchDraw();
  });

  const jsonHeaders = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken,
  };

  const postJson = (url, payload) =>
    fetch(url, {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    });

  const uploadFile = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(uploadUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      },
      body: formData,
    }).then((response) => response.json());
  };

  const sendSocket = (type, payload) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type, payload }));
  };

  const persistObject = (data) => {
    postJson(upsertUrl, data).catch(() => {});
  };

  const deleteObject = (id) => {
    const url = deleteUrlTemplate.replace('__OBJECT_ID__', id);
    postJson(url, { id }).catch(() => {});
  };

  const updateDataFromNode = (entry) => {
    const node = entry.node;
    const data = entry.data;
    const scaleX = node.scaleX();
    const scaleY = node.scaleY();
    node.scaleX(1);
    node.scaleY(1);
    data.x = Math.round(node.x());
    data.y = Math.round(node.y());
    data.width = Math.max(5, Math.round(node.width() * scaleX));
    data.height = Math.max(5, Math.round(node.height() * scaleY));
    data.rotation = Math.round(node.rotation());
  };

  const applyDataToNode = (entry) => {
    const data = entry.data;
    entry.node.position({ x: data.x, y: data.y });
    entry.node.width(data.width);
    entry.node.height(data.height);
    entry.node.rotation(data.rotation || 0);
  };

  const attachNodeHandlers = (entry) => {
    const node = entry.node;
    node.draggable(true);
    node.on('mousedown', (e) => {
      if (e.evt.button === 2) return;
      selectNode(node, entry.data.id);
    });
    node.on('dragend', () => {
      updateDataFromNode(entry);
      sendSocket('pad_object_update', { ...entry.data, playerName });
      persistObject(entry.data);
    });
    node.on('transformend', () => {
      updateDataFromNode(entry);
      sendSocket('pad_object_update', { ...entry.data, playerName });
      persistObject(entry.data);
    });
  };

  const createImageNode = (entry) => {
    const image = new Image();
    image.onload = () => layer.batchDraw();
    image.src = entry.data.file_url || '';
    const node = new Konva.Image({
      x: entry.data.x,
      y: entry.data.y,
      width: entry.data.width,
      height: entry.data.height,
      rotation: entry.data.rotation || 0,
      image,
    });
    entry.node = node;
    entry.imageElement = image;
    attachNodeHandlers(entry);
    layer.add(node);
  };

  const createVideoNode = (entry) => {
    const video = document.createElement('video');
    video.src = entry.data.file_url || '';
    video.loop = true;
    video.muted = true;
    video.addEventListener('loadedmetadata', () => {
      if (!entry.data.width || !entry.data.height) {
        entry.data.width = Math.round(video.videoWidth / 2) || 200;
        entry.data.height = Math.round(video.videoHeight / 2) || 200;
        applyDataToNode(entry);
      }
    });
    video.addEventListener('canplay', () => {
      video.play().catch(() => {});
    });
    const node = new Konva.Image({
      x: entry.data.x,
      y: entry.data.y,
      width: entry.data.width,
      height: entry.data.height,
      rotation: entry.data.rotation || 0,
      image: video,
    });
    entry.node = node;
    entry.videoElement = video;
    attachNodeHandlers(entry);
    layer.add(node);
    const anim = new Konva.Animation(() => {}, layer);
    anim.start();
    entry.animation = anim;
  };

  const createAudioNode = (entry) => {
    const audio = document.createElement('audio');
    audio.src = entry.data.file_url || '';
    const group = new Konva.Group({
      x: entry.data.x,
      y: entry.data.y,
      width: entry.data.width,
      height: entry.data.height,
      rotation: entry.data.rotation || 0,
    });
    const baseRect = new Konva.Rect({
      width: 250,
      height: 70,
      fill: '#333',
      cornerRadius: 10,
    });
    const label = new Konva.Text({
      text: (entry.data.file_url || '').split('/').pop() || 'Audio',
      fill: 'white',
      x: 10,
      y: 10,
      width: 230,
      fontSize: 12,
    });
    const playCircle = new Konva.Circle({
      radius: 15,
      fill: '#555',
    });
    const playText = new Konva.Text({
      text: entry.data.playing ? '❚❚' : '▶',
      fill: 'white',
      x: -5,
      y: -8,
      fontSize: 16,
    });
    const playGroup = new Konva.Group({ x: 30, y: 45 });
    playGroup.add(playCircle, playText);

    const exclusiveCircle = new Konva.Circle({ radius: 15, fill: '#555' });
    const exclusiveText = new Konva.Text({
      text: '▶!',
      fill: 'white',
      x: -8,
      y: -8,
      fontSize: 16,
      fontStyle: 'bold',
    });
    const exclusiveGroup = new Konva.Group({ x: 80, y: 45 });
    exclusiveGroup.add(exclusiveCircle, exclusiveText);

    const loopRect = new Konva.Rect({
      width: 40,
      height: 20,
      fill: entry.data.loop ? '#4CAF50' : '#777',
      cornerRadius: 10,
    });
    const loopCircle = new Konva.Circle({
      x: entry.data.loop ? 30 : 10,
      y: 10,
      radius: 8,
      fill: 'white',
    });
    const loopLabel = new Konva.Text({
      text: 'Loop',
      fill: 'white',
      x: -45,
      y: 3,
      fontSize: 12,
    });
    const loopGroup = new Konva.Group({ x: 190, y: 45 });
    loopGroup.add(loopRect, loopCircle, loopLabel);

    group.add(baseRect, label, playGroup, exclusiveGroup, loopGroup);
    entry.node = group;
    entry.audioElement = audio;
    entry.audioControls = { playText, loopRect, loopCircle };
    entry.audioLabel = label;
    attachNodeHandlers(entry);
    layer.add(group);

    const updateAudioState = () => {
      audio.loop = !!entry.data.loop;
      if (entry.data.playing) {
        audio.play().catch(() => {});
        playText.text('❚❚');
      } else {
        audio.pause();
        playText.text('▶');
      }
      loopRect.fill(entry.data.loop ? '#4CAF50' : '#777');
      loopCircle.x(entry.data.loop ? 30 : 10);
      layer.batchDraw();
    };

    updateAudioState();

    playGroup.on('click tap', () => {
      entry.data.playing = !entry.data.playing;
      updateAudioState();
      sendSocket('pad_object_update', { ...entry.data, playerName });
      persistObject(entry.data);
    });

    exclusiveGroup.on('click tap', () => {
      objects.forEach((other) => {
        if (other.data.object_type === 'audio' && other.data.id !== entry.data.id) {
          other.data.playing = false;
          if (other.audioElement) {
            other.audioElement.pause();
          }
          if (other.audioControls) {
            other.audioControls.playText.text('▶');
          }
        }
      });
      entry.data.playing = true;
      updateAudioState();
      sendSocket('pad_object_update', { ...entry.data, playerName });
      persistObject(entry.data);
    });

    loopGroup.on('click tap', () => {
      entry.data.loop = !entry.data.loop;
      updateAudioState();
      sendSocket('pad_object_update', { ...entry.data, playerName });
      persistObject(entry.data);
    });
  };

  const createTokenNode = (entry) => {
    const node = new Konva.Rect({
      x: entry.data.x,
      y: entry.data.y,
      width: entry.data.width,
      height: entry.data.height,
      rotation: entry.data.rotation || 0,
      fill: '#6b4e16',
      cornerRadius: 8,
      stroke: '#f5d97d',
      strokeWidth: 2,
    });
    entry.node = node;
    attachNodeHandlers(entry);
    layer.add(node);
  };

  const createNode = (data) => {
    const entry = {
      data: { ...data },
      node: null,
      imageElement: null,
      videoElement: null,
      audioElement: null,
      audioControls: null,
      audioLabel: null,
      animation: null,
    };

    switch (data.object_type) {
      case 'image':
        createImageNode(entry);
        break;
      case 'video':
        createVideoNode(entry);
        break;
      case 'audio':
        createAudioNode(entry);
        break;
      case 'token':
      default:
        createTokenNode(entry);
        break;
    }

    objects.set(data.id, entry);
    layer.batchDraw();
  };

  const applyIncoming = (payload) => {
    if (!payload || !payload.id) return;
    if (objects.has(payload.id)) {
      const entry = objects.get(payload.id);
      entry.data = { ...entry.data, ...payload };
      applyDataToNode(entry);
      if (entry.audioControls) {
        entry.audioControls.playText.text(entry.data.playing ? '❚❚' : '▶');
        entry.audioControls.loopRect.fill(entry.data.loop ? '#4CAF50' : '#777');
        entry.audioControls.loopCircle.x(entry.data.loop ? 30 : 10);
        if (entry.audioElement) {
          entry.audioElement.loop = !!entry.data.loop;
          if (entry.data.playing) {
            entry.audioElement.play().catch(() => {});
          } else {
            entry.audioElement.pause();
          }
        }
      }
      if (entry.imageElement && payload.file_url && entry.imageElement.src !== payload.file_url) {
        entry.imageElement.src = payload.file_url;
      }
      if (entry.videoElement && payload.file_url && entry.videoElement.src !== payload.file_url) {
        entry.videoElement.src = payload.file_url;
        entry.videoElement.play().catch(() => {});
      }
      if (entry.audioElement && payload.file_url && entry.audioElement.src !== payload.file_url) {
        entry.audioElement.src = payload.file_url;
        if (entry.audioLabel) {
          entry.audioLabel.text(payload.file_url.split('/').pop() || 'Audio');
        }
      }
      layer.batchDraw();
      return;
    }
    createNode(payload);
  };

  const removeNode = (payload) => {
    if (!payload || !payload.id) return;
    const entry = objects.get(payload.id);
    if (!entry) return;
    if (entry.node) {
      entry.node.destroy();
    }
    if (entry.animation) {
      entry.animation.stop();
    }
    if (entry.audioElement) {
      entry.audioElement.pause();
    }
    objects.delete(payload.id);
    if (selectedId === payload.id) {
      clearSelection();
    }
    layer.batchDraw();
  };

  const socket = wsUrl ? new ReconnectingWebSocket(wsUrl, null, { reconnectInterval: 3000 }) : null;
  if (socket) {
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'pad_object_create' || data.type === 'pad_object_update') {
          applyIncoming(data.payload);
        }
        if (data.type === 'pad_object_delete') {
          removeNode(data.payload);
        }
      } catch (err) {}
    };
  }

  const existingObjects = JSON.parse(objectsScript.textContent || '[]');
  existingObjects.forEach((data) => {
    createNode(data);
  });

  const createBaseObject = (objectType, overrides) => ({
    id: (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : `${objectType}-${Date.now()}`,
    object_type: objectType,
    x: Math.round(cursorPosition.x || 100),
    y: Math.round(cursorPosition.y || 100),
    width: 200,
    height: objectType === 'audio' ? 70 : 200,
    rotation: 0,
    file: null,
    file_url: null,
    playing: false,
    loop: false,
    ...overrides,
  });

  const addObject = (data) => {
    createNode(data);
    sendSocket('pad_object_create', { ...data, playerName });
    persistObject(data);
  };

  const handleFileUpload = (file, type) => {
    uploadFile(file).then((result) => {
      if (!result.success) return;
      const data = createBaseObject(type, {
        file: result.file,
        file_url: result.url,
      });
      if (type === 'audio') {
        data.width = 250;
        data.height = 70;
      }
      addObject(data);
    });
  };

  root.addEventListener('click', (event) => {
    const target = event.target.closest('[data-partypad-action]');
    if (!target) return;
    const action = target.dataset.partypadAction;
    if (action === 'upload-image') {
      const input = root.querySelector('[data-partypad-input="image"]');
      input.click();
    }
    if (action === 'upload-video') {
      const input = root.querySelector('[data-partypad-input="video"]');
      input.click();
    }
    if (action === 'upload-audio') {
      const input = root.querySelector('[data-partypad-input="audio"]');
      input.click();
    }
    if (action === 'add-token') {
      const data = createBaseObject('token', {
        width: 80,
        height: 80,
      });
      addObject(data);
    }
  });

  root.querySelector('[data-partypad-input="image"]').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file, 'image');
      event.target.value = '';
    }
  });
  root.querySelector('[data-partypad-input="video"]').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file, 'video');
      event.target.value = '';
    }
  });
  root.querySelector('[data-partypad-input="audio"]').addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file, 'audio');
      event.target.value = '';
    }
  });

  const copySelected = () => {
    if (!selectedId) return;
    const entry = objects.get(selectedId);
    if (!entry) return;
    copiedObject = { ...entry.data };
  };

  const pasteCopied = () => {
    if (!copiedObject) return;
    const data = createBaseObject(copiedObject.object_type, {
      ...copiedObject,
      id: (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : `${copiedObject.object_type}-${Date.now()}`,
      x: Math.round(cursorPosition.x || copiedObject.x),
      y: Math.round(cursorPosition.y || copiedObject.y),
    });
    addObject(data);
  };

  const handleDeleteSelected = () => {
    if (!selectedId) return;
    const entry = objects.get(selectedId);
    if (!entry) return;
    removeNode({ id: selectedId });
    sendSocket('pad_object_delete', { id: selectedId, playerName });
    deleteObject(selectedId);
  };

  window.addEventListener('keydown', (event) => {
    if (event.target && ['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
      return;
    }
    if (event.key === 'Escape') {
      clearSelection();
    }
    if (event.key === 'Delete') {
      handleDeleteSelected();
    }
    if (event.ctrlKey && event.key.toLowerCase() === 'c') {
      copySelected();
    }
    if (event.ctrlKey && event.key.toLowerCase() === 'v') {
      pasteCopied();
    }
  });

  document.addEventListener('paste', (event) => {
    if (copiedObject) {
      event.preventDefault();
      return;
    }
    if (!event.clipboardData) return;
    const items = event.clipboardData.items;
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        if (file) handleFileUpload(file, 'image');
        break;
      }
      if (item.type.indexOf('video') !== -1) {
        const file = item.getAsFile();
        if (file) handleFileUpload(file, 'video');
        break;
      }
      if (item.type.indexOf('audio') !== -1) {
        const file = item.getAsFile();
        if (file) handleFileUpload(file, 'audio');
        break;
      }
    }
  });
})();
