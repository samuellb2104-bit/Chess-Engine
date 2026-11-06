// Tablero y piezas en 3D con three.js.
// Coordenadas del mundo: cada casilla mide 1x1; (row, col) -> x = col - 3.5, z = row - 3.5.
// La fila 7 (rango 1, blancas) queda cerca de la cámara.

const Board3D = (() => {
  let renderer, scene, camera, container, onSquare;
  let piecesGroup, markersGroup;
  let lightMat, darkMat, frameMat;
  let whiteWood, blackWood;
  let renderQueued = false;
  const geoCache = {};
  const boardPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0); // el plano y = 0 donde se apoyan las piezas

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  /* ---------- Materiales ---------- */

  // Textura de madera dibujada en un canvas: color base + vetas verticales
  function woodTexture(base, grain) {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 256;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 90; i++) {
      const x = Math.random() * 256;
      ctx.strokeStyle = grain;
      ctx.globalAlpha = 0.05 + Math.random() * 0.18;
      ctx.lineWidth = 0.5 + Math.random() * 2.5;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x + Math.random() * 14 - 7, 85, x + Math.random() * 14 - 7, 170, x + Math.random() * 10 - 5, 256);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.encoding = THREE.sRGBEncoding;
    return texture;
  }

  function createMaterials() {
    whiteWood = new THREE.MeshStandardMaterial({ map: woodTexture("#efe0b8", "#a8894c"), roughness: 0.45, metalness: 0.0 });
    blackWood = new THREE.MeshStandardMaterial({ map: woodTexture("#3a2a20", "#0f0805"), roughness: 0.4, metalness: 0.0 });
    lightMat = new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.7 });
    darkMat = new THREE.MeshStandardMaterial({ color: "#000000", roughness: 0.7 });
    frameMat = new THREE.MeshStandardMaterial({ color: "#5a3d12", roughness: 0.55 });
  }

  /* ---------- Geometrías de las piezas ---------- */

  // Cada geometría se crea una sola vez y se comparte entre todas las piezas del mismo tipo
  function geo(key, make) {
    if (!geoCache[key]) geoCache[key] = make();
    return geoCache[key];
  }

  // Pieza torneada: gira un perfil [radio, altura] alrededor del eje vertical
  function lathe(key, points) {
    return geo(key, () => new THREE.LatheGeometry(points.map(([r, y]) => new THREE.Vector2(r, y)), 40));
  }

  const sphere = (key, r) => geo(key, () => new THREE.SphereGeometry(r, 32, 20));

  // Silueta del caballo vista de lado, con el morro hacia -x
  function knightGeometry() {
    const s = new THREE.Shape();
    s.moveTo(-0.27, 0.12);
    s.lineTo(0.3, 0.12);
    s.lineTo(0.3, 0.45);
    s.quadraticCurveTo(0.33, 0.75, 0.13, 0.92);
    s.lineTo(0.08, 1.04);
    s.lineTo(-0.02, 0.96);
    s.quadraticCurveTo(-0.12, 0.96, -0.3, 0.74);
    s.lineTo(-0.35, 0.62);
    s.quadraticCurveTo(-0.34, 0.54, -0.22, 0.55);
    s.quadraticCurveTo(-0.1, 0.58, -0.05, 0.5);
    s.quadraticCurveTo(-0.15, 0.34, -0.27, 0.12);
    const g = new THREE.ExtrudeGeometry(s, {
      depth: 0.22, bevelEnabled: true, bevelThickness: 0.06, bevelSize: 0.05, bevelSegments: 4, curveSegments: 14,
    });
    g.translate(0, 0.02, -0.11);
    return g;
  }

  function buildPiece(type, color) {
    const mat = color > 0 ? whiteWood : blackWood;
    const group = new THREE.Group();

    const add = (geometry, x = 0, y = 0, z = 0) => {
      const mesh = new THREE.Mesh(geometry, mat);
      mesh.position.set(x, y, z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      group.add(mesh);
      return mesh;
    };

    switch (type) {
      case 1: // peón
        add(lathe("pawn", [[0, 0], [.34, 0], [.34, .05], [.29, .09], [.2, .15], [.13, .3], [.11, .42], [.19, .46], [.19, .5], [.1, .54], [0, .54]]));
        add(sphere("pawnHead", 0.17), 0, 0.66, 0);
        break;

      case 2: { // caballo
        add(lathe("knightBase", [[0, 0], [.35, 0], [.35, .06], [.3, .1], [.26, .16], [0, .16]]));
        const horse = add(geo("knight", knightGeometry), 0, 0, 0);
        horse.rotation.y = color > 0 ? -Math.PI / 4 : (3 * Math.PI) / 4; // vista 3/4, mirando hacia el rival
        break;
      }

      case 3: { // alfil
        add(lathe("bishop", [[0, 0], [.35, 0], [.35, .06], [.3, .1], [.2, .17], [.12, .4], [.1, .6], [.2, .64], [.2, .68], [.09, .72], [0, .72]]));
        const head = add(sphere("bishopHead", 0.16), 0, 0.9, 0);
        head.scale.set(1, 1.45, 1);
        add(sphere("bishopKnob", 0.055), 0, 1.16, 0);
        break;
      }

      case 4: { // torre
        add(lathe("rook", [[0, 0], [.36, 0], [.36, .06], [.31, .1], [.22, .18], [.2, .55], [.27, .62], [.29, .7], [.29, .74], [0, .74]]));
        for (let i = 0; i < 6; i++) {
          const angle = (i * Math.PI) / 3;
          const merlon = add(geo("merlon", () => new THREE.BoxGeometry(0.14, 0.14, 0.1)), Math.sin(angle) * 0.22, 0.81, Math.cos(angle) * 0.22);
          merlon.rotation.y = angle;
        }
        break;
      }

      case 5: // dama
        add(lathe("queen", [[0, 0], [.37, 0], [.37, .06], [.32, .1], [.21, .18], [.13, .5], [.11, .75], [.22, .8], [.22, .86], [.12, .9], [.2, 1.0], [.2, 1.04], [0, 1.04]]));
        for (let i = 0; i < 8; i++) {
          const angle = (i * Math.PI) / 4;
          add(sphere("crownBall", 0.05), Math.sin(angle) * 0.19, 1.08, Math.cos(angle) * 0.19);
        }
        add(sphere("queenTop", 0.07), 0, 1.12, 0);
        break;

      case 6: // rey
        add(lathe("king", [[0, 0], [.37, 0], [.37, .06], [.32, .1], [.22, .18], [.14, .55], [.12, .8], [.24, .86], [.24, .92], [.14, .96], [.2, 1.08], [0, 1.08]]));
        add(geo("crossV", () => new THREE.BoxGeometry(0.08, 0.3, 0.08)), 0, 1.24, 0);
        add(geo("crossH", () => new THREE.BoxGeometry(0.22, 0.08, 0.08)), 0, 1.3, 0);
        break;
    }
    return group;
  }

  /* ---------- Escena ---------- */

  function labelTexture(text) {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 64;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "rgba(240, 228, 200, 0.85)";
    ctx.font = "600 38px Cinzel, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, 32, 34);
    const texture = new THREE.CanvasTexture(canvas);
    texture.encoding = THREE.sRGBEncoding;
    return texture;
  }

  function buildBoard() {
    const squareGeo = new THREE.BoxGeometry(1, 0.1, 1);
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const mesh = new THREE.Mesh(squareGeo, (row + col) % 2 === 0 ? lightMat : darkMat);
        mesh.position.set(col - 3.5, -0.05, row - 3.5);
        mesh.receiveShadow = true;
        scene.add(mesh);
      }
    }

    // Marco: cuatro tablones alrededor de las casillas
    const long = 9.4, edge = 0.7, height = 0.28, y = -0.06;
    const sides = [
      [long, height, edge, 0, y, -(4 + edge / 2) + 0.0],
      [long, height, edge, 0, y, 4 + edge / 2],
      [edge, height, 8, -(4 + edge / 2), y, 0],
      [edge, height, 8, 4 + edge / 2, y, 0],
    ];
    for (const [w, h, d, x, py, z] of sides) {
      const plank = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), frameMat);
      plank.position.set(x, py, z);
      plank.castShadow = true;
      plank.receiveShadow = true;
      scene.add(plank);
    }

    // Coordenadas sobre el marco
    "abcdefgh".split("").forEach((letter, col) => {
      const label = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.42), new THREE.MeshBasicMaterial({ map: labelTexture(letter), transparent: true }));
      label.rotation.x = -Math.PI / 2;
      label.position.set(col - 3.5, 0.09, 4.35);
      scene.add(label);
    });
    for (let row = 0; row < 8; row++) {
      const label = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.42), new THREE.MeshBasicMaterial({ map: labelTexture(String(8 - row)), transparent: true }));
      label.rotation.x = -Math.PI / 2;
      label.position.set(-4.35, 0.09, row - 3.5);
      scene.add(label);
    }

    // Suelo invisible que solo recoge las sombras sobre el fondo de la página
    const catcher = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: 0.5 }));
    catcher.rotation.x = -Math.PI / 2;
    catcher.position.y = -0.21;
    catcher.receiveShadow = true;
    scene.add(catcher);
  }

  function buildLights() {
    scene.add(new THREE.HemisphereLight(0xfff4e0, 0x3a2a1c, 0.75));
    const sun = new THREE.DirectionalLight(0xffffff, 0.95);
    sun.position.set(-5, 12, 7);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -7;
    sun.shadow.camera.right = 7;
    sun.shadow.camera.top = 7;
    sun.shadow.camera.bottom = -7;
    sun.shadow.bias = -0.0004;
    scene.add(sun);
  }

  /* ---------- Render bajo demanda ---------- */

  function requestRender() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(() => {
      renderQueued = false;
      renderer.render(scene, camera);
    });
  }

  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;

    // Cuanto más alta la cámara, menos tapan las piezas a las casillas de detrás
    // y menos se encogen las filas lejanas (más importante en el móvil, en vertical)
    const portrait = camera.aspect < 1.1;
    const elevation = ((portrait ? 64 : 54) * Math.PI) / 180;

    // Distancia a la que cabe todo el tablero, también en pantallas estrechas
    const distance = Math.max(16.5, 18.5 / camera.aspect);
    camera.position.set(0, Math.sin(elevation) * distance, 0.3 + Math.cos(elevation) * distance);
    camera.lookAt(0, 0, 0.3);
    camera.updateProjectionMatrix();
    requestRender();
  }

  /* ---------- API pública ---------- */

  function init(containerEl, onSquareClick) {
    container = containerEl;
    onSquare = onSquareClick;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputEncoding = THREE.sRGBEncoding; // los colores CSS son sRGB
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(32, 1.6, 0.1, 100);

    createMaterials();
    buildBoard();
    buildLights();

    piecesGroup = new THREE.Group();
    markersGroup = new THREE.Group();
    scene.add(piecesGroup, markersGroup);

    renderer.domElement.addEventListener("click", (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);

      // Dos candidatos, y decide quien llama (app.js), que sabe qué casillas son destinos:
      // - plane: la casilla del tablero bajo el dedo, ignorando las piezas (atraviesa las piezas altas)
      // - piece: la casilla de la pieza que se toca, incluida su parte alta
      let plane = null;
      const point = new THREE.Vector3();
      if (raycaster.ray.intersectPlane(boardPlane, point)) {
        const row = Math.floor(point.z + 4);
        const col = Math.floor(point.x + 4);
        if (row >= 0 && row < 8 && col >= 0 && col < 8) plane = [row, col];
      }

      let piece = null;
      const hits = raycaster.intersectObject(piecesGroup, true);
      if (hits.length) {
        let node = hits[0].object;
        while (node && node.userData.row === undefined) node = node.parent;
        if (node) piece = [node.userData.row, node.userData.col];
      }

      onSquare({ piece, plane });
    });

    new ResizeObserver(resize).observe(container);
    setTheme();
    resize();
  }

  // Lee los colores del tema actual desde las variables CSS (una sola fuente de verdad)
  function setTheme() {
    const css = getComputedStyle(document.body);
    lightMat.color.set(css.getPropertyValue("--light").trim()).convertSRGBToLinear();
    darkMat.color.set(css.getPropertyValue("--dark").trim()).convertSRGBToLinear();
    frameMat.color.set(css.getPropertyValue("--frame-solid").trim()).convertSRGBToLinear();
    requestRender();
  }

  function addPiece(type, color, row, col) {
    const group = buildPiece(type, color);
    group.position.set(col - 3.5, 0, row - 3.5);
    group.userData = { row, col, type, color };
    piecesGroup.add(group);
    return group;
  }

  // board: matriz 8x8 con piezas con signo (la que devuelve el servidor)
  function setPosition(board) {
    piecesGroup.clear();
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const piece = board[row][col];
        if (piece !== 0) addPiece(Math.abs(piece), Math.sign(piece), row, col);
      }
    }
    requestRender();
  }

  /* ---------- Animación de jugadas ---------- */

  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  // Llama a onUpdate(t) con t de 0 a 1 durante "duration" ms, dibujando cada fotograma
  function tween(duration, onUpdate) {
    return new Promise((resolve) => {
      const start = performance.now();
      function frame(now) {
        const t = Math.min(1, (now - start) / duration);
        onUpdate(t);
        renderer.render(scene, camera);
        if (t < 1) requestAnimationFrame(frame);
        else resolve();
      }
      requestAnimationFrame(frame);
    });
  }

  const findPiece = (row, col) =>
    piecesGroup.children.find((p) => p.userData.row === row && p.userData.col === col);

  // Anima una jugada en notación UCI ("e2e4", "a7a8q"). Devuelve una promesa que se cumple al terminar.
  // Mueve la pieza (con un pequeño salto), retira la capturada, mueve la torre en un enroque
  // y convierte el peón al coronar. Después hay que sincronizar con setPosition().
  async function animateMove(uci) {
    const files = "abcdefgh";
    const fromCol = files.indexOf(uci[0]), fromRow = 8 - Number(uci[1]);
    const toCol = files.indexOf(uci[2]), toRow = 8 - Number(uci[3]);
    const promotionType = { q: 5, r: 4, b: 3, n: 2 }[uci[4]] || 5;

    const mover = findPiece(fromRow, fromCol);
    if (!mover) return;
    const captured = findPiece(toRow, toCol);

    // Piezas que se desplazan: la principal y, en un enroque, también la torre
    const travelers = [{ piece: mover, toRow, toCol, lift: mover.userData.type === 2 ? 0.8 : 0.35 }];
    if (mover.userData.type === 6 && Math.abs(toCol - fromCol) === 2) {
      const kingside = toCol > fromCol;
      const rook = findPiece(fromRow, kingside ? 7 : 0);
      if (rook) travelers.push({ piece: rook, toRow: fromRow, toCol: kingside ? 5 : 3, lift: 0.2 });
    }
    travelers.forEach((tr) => {
      tr.fromX = tr.piece.position.x;
      tr.fromZ = tr.piece.position.z;
    });

    const distance = Math.hypot(toCol - fromCol, toRow - fromRow);
    const duration = 280 + 70 * distance; // las jugadas largas tardan un poco más

    await tween(duration, (t) => {
      const e = ease(t);
      for (const tr of travelers) {
        tr.piece.position.x = tr.fromX + (tr.toCol - 3.5 - tr.fromX) * e;
        tr.piece.position.z = tr.fromZ + (tr.toRow - 3.5 - tr.fromZ) * e;
        tr.piece.position.y = tr.lift * Math.sin(Math.PI * t);
      }
      // La pieza capturada se encoge justo cuando llega la otra
      if (captured && t > 0.7) captured.scale.setScalar(Math.max(0.001, 1 - (t - 0.7) / 0.3));
    });

    if (captured) piecesGroup.remove(captured);
    for (const tr of travelers) {
      tr.piece.position.y = 0;
      tr.piece.userData.row = tr.toRow;
      tr.piece.userData.col = tr.toCol;
    }

    // Coronación: el peón se sustituye por la pieza elegida (dama por defecto, igual que el servidor)
    if (mover.userData.type === 1 && (toRow === 0 || toRow === 7)) {
      piecesGroup.remove(mover);
      addPiece(promotionType, mover.userData.color, toRow, toCol);
    }
    requestRender();
  }

  // Marcas sobre las casillas: selected [r,c], last [[r,c],[r,c]], targets y captures [[r,c], ...]
  function setMarkers({ selected = null, last = [], targets = [], captures = [] }) {
    markersGroup.clear();

    // onTop: se dibuja encima de las piezas, para que un destino tapado por una pieza alta siga visible
    const flat = (geometry, color, opacity, [row, col], y, onTop = false) => {
      const mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
          color: new THREE.Color(color).convertSRGBToLinear(),
          transparent: true,
          opacity,
          depthWrite: false,
          depthTest: !onTop,
        })
      );
      mesh.position.set(col - 3.5, y, row - 3.5);
      if (onTop) mesh.renderOrder = 10;
      markersGroup.add(mesh);
    };

    const plane = geo("markPlane", () => new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2));
    const dot = geo("markDot", () => new THREE.CircleGeometry(0.17, 32).rotateX(-Math.PI / 2));
    const ring = geo("markRing", () => new THREE.RingGeometry(0.36, 0.47, 48).rotateX(-Math.PI / 2));

    last.forEach((sq) => flat(plane, 0xffe050, 0.35, sq, 0.012));
    if (selected) flat(plane, 0xffe050, 0.65, selected, 0.014);
    targets.forEach((sq) => flat(dot, 0x111111, 0.45, sq, 0.016, true));
    captures.forEach((sq) => flat(ring, 0x111111, 0.5, sq, 0.016, true));
    requestRender();
  }

  return { init, setTheme, setPosition, setMarkers, animateMove, resize };
})();
