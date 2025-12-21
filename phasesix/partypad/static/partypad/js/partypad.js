class PartyPad {
    constructor(root) {
        this.root = root;
        this.stageContainer =
            root.querySelector("[data-partypad-stage]") ||
            document.getElementById("partypad-stage");
        this.objectsScript =
            root.querySelector("[data-partypad-objects]") ||
            document.getElementById("partypad-objects");

        if (!this.stageContainer || !this.objectsScript || !window.Konva) {
            return;
        }

        this.csrfToken = root.dataset.csrfToken;
        this.padId = root.dataset.padId;
        this.modifyUrl = root.dataset.modifyObjectUrl;
        this.wsUrl = root.dataset.wsUrl;
        this.backgroundImageUrl = root.dataset.partypadBackgroundImage || "";
        this.backgroundColor =
            root.dataset.partypadBackgroundColor || "#0b0b0b";

        this.playerName = this.getOrCreatePlayerName();

        this.objects = new Map();
        this.selectedId = null;
        this.copiedObject = null;
        this.cursorPosition = { x: 0, y: 0 };
        this.isPanning = false;
        this.lastPanPos = null;
        this.socket = null;

        this.setupStage();
        this.setupStageEvents();
        this.setupStageNavigation();
        this.setupSocket();
        this.loadExistingObjects();
        this.setupUiHandlers();
        this.setupKeyboardHandlers();
        this.setupClipboardHandlers();
    }

    getOrCreatePlayerName() {
        const playerKey = "partypad-player-name";
        let playerName = localStorage.getItem(playerKey);
        if (!playerName) {
            playerName = `Player_${Math.random().toString(36).substring(7)}`;
            localStorage.setItem(playerKey, playerName);
        }
        return playerName;
    }

    setupStage() {
        this.stage = new Konva.Stage({
            container: this.stageContainer,
            width: this.root.clientWidth,
            height: this.root.clientHeight,
        });
        this.backgroundLayer = new Konva.Layer({ listening: false });
        this.backgroundRect = new Konva.Rect({
            x: 0,
            y: 0,
            width: this.stage.width(),
            height: this.stage.height(),
            fill: this.backgroundColor,
        });
        this.backgroundLayer.add(this.backgroundRect);
        this.stage.add(this.backgroundLayer);

        this.layer = new Konva.Layer();
        this.stage.add(this.layer);
        this.transformer = new Konva.Transformer({
            rotateEnabled: true,
            ignoreStroke: true,
            keepRatio: true,
        });
        this.layer.add(this.transformer);

        this.resizeStage = () => {
            this.stage.width(this.root.clientWidth);
            this.stage.height(this.root.clientHeight);
            this.updateBackgroundSize();
            this.updateBackgroundTransform();
        };
        window.addEventListener("resize", this.resizeStage);

        this.setupBackground();
    }

    setupStageEvents() {
        this.stage.on("mousedown", (event) => {
            if (event.evt.button === 2) {
                return;
            }
            if (event.target === this.stage) {
                this.clearSelection();
            }
        });

        this.stage.on("mousemove", () => this.updateCursor());
        this.stageContainer.addEventListener("contextmenu", (event) =>
            event.preventDefault(),
        );
    }

    setupStageNavigation() {
        this.stage.on("mousedown", (event) => {
            if (event.evt.button !== 2) return;
            this.isPanning = true;
            this.lastPanPos = this.stage.getPointerPosition();
            event.evt.preventDefault();
        });

        this.stage.on("mouseup", () => {
            this.isPanning = false;
            this.lastPanPos = null;
        });

        this.stage.on("mousemove", (event) => {
            if (!this.isPanning) return;
            const pos = this.stage.getPointerPosition();
            if (!pos || !this.lastPanPos) return;
            const dx = pos.x - this.lastPanPos.x;
            const dy = pos.y - this.lastPanPos.y;
            this.stage.position({
                x: this.stage.x() + dx,
                y: this.stage.y() + dy,
            });
            this.updateBackgroundTransform();
            this.lastPanPos = pos;
            this.stage.batchDraw();
            event.evt.preventDefault();
        });

        this.stage.on("wheel", (event) => {
            event.evt.preventDefault();
            const scaleBy = 1.1;
            const oldScale = this.stage.scaleX();
            const pointer = this.stage.getPointerPosition();
            if (!pointer) return;
            const mousePointTo = {
                x: pointer.x / oldScale - this.stage.x() / oldScale,
                y: pointer.y / oldScale - this.stage.y() / oldScale,
            };
            const direction = event.evt.deltaY < 0 ? 1 : -1;
            const newScale =
                direction > 0 ? oldScale * scaleBy : oldScale / scaleBy;
            this.stage.scale({ x: newScale, y: newScale });
            this.stage.position({
                x: -(mousePointTo.x - pointer.x / newScale) * newScale,
                y: -(mousePointTo.y - pointer.y / newScale) * newScale,
            });
            this.updateBackgroundTransform();
            this.stage.batchDraw();
        });
    }

    setupSocket() {
        if (!this.wsUrl) {
            return;
        }
        this.socket = new ReconnectingWebSocket(this.wsUrl, null, {
            reconnectInterval: 3000,
        });
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (
                    data.type === "pad_object_create" ||
                    data.type === "pad_object_update"
                ) {
                    this.applyIncoming(data.payload);
                }
                if (data.type === "pad_object_delete") {
                    this.removeNode(data.payload);
                }
            } catch (err) {}
        };
    }

    loadExistingObjects() {
        const existingObjects = JSON.parse(
            this.objectsScript.textContent || "[]",
        );
        existingObjects.forEach((data) => {
            this.createNode(data);
        });
        this.layer.batchDraw();
    }

    setupUiHandlers() {
        this.root.addEventListener("click", (event) => {
            const target = event.target.closest("[data-partypad-action]");
            if (!target) return;
            const action = target.dataset.partypadAction;
            if (action === "upload-image") {
                this.getInput("image").click();
            }
            if (action === "upload-video") {
                this.getInput("video").click();
            }
            if (action === "upload-audio") {
                this.getInput("audio").click();
            }
            if (action === "add-token") {
                const data = this.createBaseObject("token", {
                    width: 80,
                    height: 80,
                });
                this.addObject(data);
            }
        });

        this.getInput("image").addEventListener("change", async (event) => {
            const file = event.target.files[0];
            if (file) {
                await this.handleFileUpload(file, "image");
                event.target.value = "";
            }
        });

        this.getInput("video").addEventListener("change", async (event) => {
            const file = event.target.files[0];
            if (file) {
                await this.handleFileUpload(file, "video");
                event.target.value = "";
            }
        });

        this.getInput("audio").addEventListener("change", async (event) => {
            const file = event.target.files[0];
            if (file) {
                await this.handleFileUpload(file, "audio");
                event.target.value = "";
            }
        });
    }

    setupKeyboardHandlers() {
        window.addEventListener("keydown", (event) => {
            if (
                event.target &&
                ["INPUT", "TEXTAREA"].includes(event.target.tagName)
            ) {
                return;
            }
            if (event.key === "Escape") {
                this.clearSelection();
            }
            if (event.key === "Delete") {
                this.handleDeleteSelected();
            }
            if (event.ctrlKey && event.key.toLowerCase() === "c") {
                this.copySelected();
            }
            if (event.ctrlKey && event.key.toLowerCase() === "v") {
                this.pasteCopied();
            }
        });
    }

    setupClipboardHandlers() {
        document.addEventListener("paste", (event) => {
            if (this.copiedObject) {
                event.preventDefault();
                return;
            }
            if (!event.clipboardData) return;
            const items = event.clipboardData.items;
            for (let i = 0; i < items.length; i += 1) {
                const item = items[i];
                if (item.type.indexOf("image") !== -1) {
                    const file = item.getAsFile();
                    if (file) {
                        this.handleFileUpload(file, "image").catch(() => {});
                    }
                    break;
                }
                if (item.type.indexOf("video") !== -1) {
                    const file = item.getAsFile();
                    if (file) {
                        this.handleFileUpload(file, "video").catch(() => {});
                    }
                    break;
                }
                if (item.type.indexOf("audio") !== -1) {
                    const file = item.getAsFile();
                    if (file) {
                        this.handleFileUpload(file, "audio").catch(() => {});
                    }
                    break;
                }
            }
        });
    }

    setupBackground() {
        this.updateBackgroundTransform();
        if (!this.backgroundImageUrl) {
            this.backgroundLayer.batchDraw();
            return;
        }

        const image = new Image();
        image.onload = () => {
            this.backgroundRect.fillPatternImage(image);
            this.backgroundRect.fillPatternRepeat("repeat");
            this.backgroundRect.fillPatternOffset({ x: 0, y: 0 });
            this.updateBackgroundTransform();
            this.backgroundLayer.batchDraw();
        };
        image.onerror = () => {
            this.backgroundLayer.batchDraw();
        };
        image.src = this.backgroundImageUrl;
    }

    updateBackgroundSize() {
        if (!this.backgroundRect) return;
        this.backgroundRect.width(this.stage.width());
        this.backgroundRect.height(this.stage.height());
        this.backgroundLayer.batchDraw();
    }

    updateBackgroundTransform() {
        if (!this.backgroundLayer) return;
        const scaleX = this.stage.scaleX() || 1;
        const scaleY = this.stage.scaleY() || 1;
        this.backgroundLayer.scale({ x: 1 / scaleX, y: 1 / scaleY });
        this.backgroundLayer.position({
            x: -this.stage.x() / scaleX,
            y: -this.stage.y() / scaleY,
        });
    }

    getInput(type) {
        return this.root.querySelector(`[data-partypad-input="${type}"]`);
    }

    stagePointer() {
        return this.stage.getPointerPosition() || this.cursorPosition;
    }

    updateCursor() {
        const pos = this.stagePointer();
        if (pos) {
            this.cursorPosition = { x: pos.x, y: pos.y };
        }
    }

    selectNode(node, id) {
        this.selectedId = id;
        this.transformer.nodes([node]);
        this.layer.batchDraw();
    }

    clearSelection() {
        this.selectedId = null;
        this.transformer.nodes([]);
        this.layer.batchDraw();
    }

    jsonHeaders() {
        return {
            "Content-Type": "application/json",
            "X-CSRFToken": this.csrfToken,
        };
    }

    postJson(url, payload, method = "POST") {
        return fetch(url, {
            method: method,
            headers: this.jsonHeaders(),
            body: JSON.stringify(payload),
        });
    }

    sendSocket(type, payload) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
        this.socket.send(JSON.stringify({ type, payload }));
    }

    persistObject(data) {
        const url = data.modify_url || this.modifyUrl;
        this.postJson(url, data).catch(() => {});
    }

    deleteObject(id) {
        const entry = this.objects.get(id);
        const url =
            entry && entry.data.modify_url
                ? entry.data.modify_url
                : this.modifyUrl;
        this.postJson(url, { id }, "DELETE").catch(() => {});
    }

    updateDataFromNode(entry) {
        const node = entry.node;
        const data = entry.data;
        const scaleX = node.scaleX();
        const scaleY = node.scaleY();

        data.width = Math.max(5, Math.round(node.width() * scaleX));
        data.height = Math.max(5, Math.round(node.height() * scaleY));
        data.x = Math.round(node.x());
        data.y = Math.round(node.y());
        data.rotation = Math.round(node.rotation());

        node.scaleX(1);
        node.scaleY(1);
        node.width(data.width);
        node.height(data.height);
    }

    applyDataToNode(entry) {
        const data = entry.data;
        entry.node.position({ x: data.x, y: data.y });
        entry.node.width(data.width);
        entry.node.height(data.height);
        entry.node.rotation(data.rotation || 0);
    }

    attachNodeHandlers(entry) {
        const node = entry.node;
        node.draggable(true);
        node.on("mousedown", (event) => {
            if (event.evt.button === 2) return;
            this.selectNode(node, entry.data.id);
        });
        node.on("dragend", () => {
            this.updateDataFromNode(entry);
            this.sendSocket("pad_object_update", {
                ...entry.data,
                playerName: this.playerName,
            });
            this.persistObject(entry.data);
        });
        node.on("transformend", () => {
            this.updateDataFromNode(entry);
            this.sendSocket("pad_object_update", {
                ...entry.data,
                playerName: this.playerName,
            });
            this.persistObject(entry.data);
        });
    }

    createImageNode(entry) {
        const image = new Image();
        image.onload = () => {
            this.layer.batchDraw();
        };
        image.onerror = () => {
            console.error("Failed to load image:", entry.data.file_url);
        };

        const node = new Konva.Image({
            x: entry.data.x,
            y: entry.data.y,
            width: entry.data.width,
            height: entry.data.height,
            rotation: entry.data.rotation || 0,
            image,
        });

        image.src = entry.data.file_url || "";

        if (image.complete) {
            this.layer.batchDraw();
        }

        entry.node = node;
        entry.imageElement = image;
        this.attachNodeHandlers(entry);
        this.layer.add(node);
        this.layer.batchDraw();
    }

    createVideoNode(entry) {
        const video = document.createElement("video");
        video.loop = true;
        video.muted = true;
        video.playsInline = true;
        video.crossOrigin = "anonymous";

        video.addEventListener("loadedmetadata", () => {
            if (!entry.data.width || !entry.data.height) {
                entry.data.width = Math.round(video.videoWidth / 2) || 200;
                entry.data.height = Math.round(video.videoHeight / 2) || 200;
                this.applyDataToNode(entry);
            }
            this.layer.batchDraw();
        });
        video.addEventListener("canplay", () => {
            video.play().catch(() => {});
            this.layer.batchDraw();
        });

        const node = new Konva.Image({
            x: entry.data.x,
            y: entry.data.y,
            width: entry.data.width,
            height: entry.data.height,
            rotation: entry.data.rotation || 0,
            image: video,
        });

        video.src = entry.data.file_url || "";

        entry.node = node;
        entry.videoElement = video;
        this.attachNodeHandlers(entry);
        this.layer.add(node);

        const anim = new Konva.Animation(() => {}, this.layer);
        anim.start();
        entry.animation = anim;
        this.layer.batchDraw();
    }

    createAudioNode(entry) {
        const audio = document.createElement("audio");
        audio.src = entry.data.file_url || "";
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
            fill: "#333",
            cornerRadius: 10,
        });
        const label = new Konva.Text({
            text: (entry.data.file_url || "").split("/").pop() || "Audio",
            fill: "white",
            x: 10,
            y: 10,
            width: 230,
            fontSize: 12,
        });
        const playCircle = new Konva.Circle({
            radius: 15,
            fill: "#555",
        });
        const playText = new Konva.Text({
            text: entry.data.playing ? "❚❚" : "▶",
            fill: "white",
            x: -5,
            y: -8,
            fontSize: 16,
        });
        const playGroup = new Konva.Group({ x: 30, y: 45 });
        playGroup.add(playCircle, playText);

        const exclusiveCircle = new Konva.Circle({ radius: 15, fill: "#555" });
        const exclusiveText = new Konva.Text({
            text: "▶!",
            fill: "white",
            x: -8,
            y: -8,
            fontSize: 16,
            fontStyle: "bold",
        });
        const exclusiveGroup = new Konva.Group({ x: 80, y: 45 });
        exclusiveGroup.add(exclusiveCircle, exclusiveText);

        const loopRect = new Konva.Rect({
            width: 40,
            height: 20,
            fill: entry.data.loop ? "#4CAF50" : "#777",
            cornerRadius: 10,
        });
        const loopCircle = new Konva.Circle({
            x: entry.data.loop ? 30 : 10,
            y: 10,
            radius: 8,
            fill: "white",
        });
        const loopLabel = new Konva.Text({
            text: "Loop",
            fill: "white",
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
        this.attachNodeHandlers(entry);
        this.layer.add(group);
        this.layer.batchDraw();

        const updateAudioState = () => {
            audio.loop = !!entry.data.loop;
            if (entry.data.playing) {
                audio.play().catch(() => {});
                playText.text("❚❚");
            } else {
                audio.pause();
                playText.text("▶");
            }
            loopRect.fill(entry.data.loop ? "#4CAF50" : "#777");
            loopCircle.x(entry.data.loop ? 30 : 10);
            this.layer.batchDraw();
        };

        updateAudioState();

        playGroup.on("click tap", () => {
            entry.data.playing = !entry.data.playing;
            updateAudioState();
            this.sendSocket("pad_object_update", {
                ...entry.data,
                playerName: this.playerName,
            });
            this.persistObject(entry.data);
        });

        exclusiveGroup.on("click tap", () => {
            this.objects.forEach((other) => {
                if (
                    other.data.object_type === "audio" &&
                    other.data.id !== entry.data.id
                ) {
                    other.data.playing = false;
                    if (other.audioElement) {
                        other.audioElement.pause();
                    }
                    if (other.audioControls) {
                        other.audioControls.playText.text("▶");
                    }
                }
            });
            entry.data.playing = true;
            updateAudioState();
            this.sendSocket("pad_object_update", {
                ...entry.data,
                playerName: this.playerName,
            });
            this.persistObject(entry.data);
        });

        loopGroup.on("click tap", () => {
            entry.data.loop = !entry.data.loop;
            updateAudioState();
            this.sendSocket("pad_object_update", {
                ...entry.data,
                playerName: this.playerName,
            });
            this.persistObject(entry.data);
        });
    }

    createTokenNode(entry) {
        const node = new Konva.Rect({
            x: entry.data.x,
            y: entry.data.y,
            width: entry.data.width,
            height: entry.data.height,
            rotation: entry.data.rotation || 0,
            fill: "#6b4e16",
            cornerRadius: 8,
            stroke: "#f5d97d",
            strokeWidth: 2,
        });
        entry.node = node;
        this.attachNodeHandlers(entry);
        this.layer.add(node);
        this.layer.batchDraw();
    }

    createNode(data) {
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
            case "image":
                this.createImageNode(entry);
                break;
            case "video":
                this.createVideoNode(entry);
                break;
            case "audio":
                this.createAudioNode(entry);
                break;
            case "token":
            default:
                this.createTokenNode(entry);
                break;
        }

        this.objects.set(data.id, entry);
        this.layer.batchDraw();
    }

    applyIncoming(payload) {
        if (!payload || !payload.id) return;
        if (this.objects.has(payload.id)) {
            const entry = this.objects.get(payload.id);
            entry.data = { ...entry.data, ...payload };
            this.applyDataToNode(entry);
            if (entry.audioControls) {
                entry.audioControls.playText.text(
                    entry.data.playing ? "❚❚" : "▶",
                );
                entry.audioControls.loopRect.fill(
                    entry.data.loop ? "#4CAF50" : "#777",
                );
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
            if (
                entry.imageElement &&
                payload.file_url &&
                entry.imageElement.src !== payload.file_url
            ) {
                entry.imageElement.src = payload.file_url;
            }
            if (
                entry.videoElement &&
                payload.file_url &&
                entry.videoElement.src !== payload.file_url
            ) {
                entry.videoElement.src = payload.file_url;
                entry.videoElement.play().catch(() => {});
            }
            if (
                entry.audioElement &&
                payload.file_url &&
                entry.audioElement.src !== payload.file_url
            ) {
                entry.audioElement.src = payload.file_url;
                if (entry.audioLabel) {
                    entry.audioLabel.text(
                        payload.file_url.split("/").pop() || "Audio",
                    );
                }
            }
            this.layer.batchDraw();
            return;
        }
        this.createNode(payload);
    }

    removeNode(payload) {
        if (!payload || !payload.id) return;
        const entry = this.objects.get(payload.id);
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
        this.objects.delete(payload.id);
        if (this.selectedId === payload.id) {
            this.clearSelection();
        }
        this.layer.batchDraw();
    }

    createBaseObject(objectType, overrides) {
        return {
            id:
                window.crypto && window.crypto.randomUUID
                    ? window.crypto.randomUUID()
                    : `${objectType}-${Date.now()}`,
            object_type: objectType,
            x: Math.round(this.cursorPosition.x || 100),
            y: Math.round(this.cursorPosition.y || 100),
            width: 200,
            height: objectType === "audio" ? 70 : 200,
            rotation: 0,
            file: null,
            file_url: null,
            playing: false,
            loop: false,
            ...overrides,
        };
    }

    addObject(data) {
        this.createNode(data);
        this.sendSocket("pad_object_create", {
            ...data,
            playerName: this.playerName,
        });
        if (!data.modify_url) {
            data.modify_url = this.modifyUrl;
        }
        this.persistObject(data);
    }

    getImageDimensions(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                resolve({ width: img.width, height: img.height });
                URL.revokeObjectURL(img.src);
            };
            img.onerror = () => {
                resolve({ width: 200, height: 200 });
                URL.revokeObjectURL(img.src);
            };
            img.src = URL.createObjectURL(file);
        });
    }

    getVideoDimensions(file) {
        return new Promise((resolve) => {
            const video = document.createElement("video");
            video.preload = "metadata";
            video.onloadedmetadata = () => {
                resolve({
                    width: video.videoWidth,
                    height: video.videoHeight,
                });
                URL.revokeObjectURL(video.src);
            };
            video.onerror = () => {
                resolve({ width: 200, height: 200 });
                URL.revokeObjectURL(video.src);
            };
            video.src = URL.createObjectURL(file);
        });
    }

    async handleFileUpload(file, type) {
        let dimensions = { width: 200, height: 200 };
        if (type === "image") {
            dimensions = await this.getImageDimensions(file);
        } else if (type === "video") {
            dimensions = await this.getVideoDimensions(file);
        } else if (type === "audio") {
            dimensions = { width: 250, height: 70 };
        }

        const maxDim = 400;
        if (type !== "audio") {
            if (dimensions.width > maxDim || dimensions.height > maxDim) {
                const ratio = dimensions.width / dimensions.height;
                if (ratio > 1) {
                    dimensions.width = maxDim;
                    dimensions.height = Math.round(maxDim / ratio);
                } else {
                    dimensions.height = maxDim;
                    dimensions.width = Math.round(maxDim * ratio);
                }
            }
        }

        const formData = new FormData();
        formData.append("file", file);
        const data = this.createBaseObject(type, dimensions);
        Object.keys(data).forEach((key) => {
            if (data[key] !== null && data[key] !== undefined) {
                formData.append(key, data[key]);
            }
        });

        const url = this.modifyUrl;
        fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": this.csrfToken,
            },
            body: formData,
        })
            .then((response) => response.json())
            .then((result) => {
                if (!result.success) return;
                data.file = result.file;
                data.file_url = result.file_url;
                data.modify_url = result.modify_url;
                this.addObject(data);
            });
    }

    copySelected() {
        if (!this.selectedId) return;
        const entry = this.objects.get(this.selectedId);
        if (!entry) return;
        this.copiedObject = { ...entry.data };
    }

    pasteCopied() {
        if (!this.copiedObject) return;
        const data = this.createBaseObject(this.copiedObject.object_type, {
            ...this.copiedObject,
            id:
                window.crypto && window.crypto.randomUUID
                    ? window.crypto.randomUUID()
                    : `${this.copiedObject.object_type}-${Date.now()}`,
            x: Math.round(this.cursorPosition.x || this.copiedObject.x),
            y: Math.round(this.cursorPosition.y || this.copiedObject.y),
        });
        this.addObject(data);
    }

    handleDeleteSelected() {
        if (!this.selectedId) return;
        const entry = this.objects.get(this.selectedId);
        if (!entry) return;
        this.removeNode({ id: this.selectedId });
        this.sendSocket("pad_object_delete", {
            id: this.selectedId,
            playerName: this.playerName,
        });
        this.deleteObject(this.selectedId);
    }
}

window.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("partypad-root");
    if (!root) {
        return;
    }
    new PartyPad(root);
});
