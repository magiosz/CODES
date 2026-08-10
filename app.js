// 1. Configuración de la Escena (Usando el objeto global en mayúsculas)
const canvas = document.querySelector('canvas.webgl');
const scene = new THREE.Scene();

// 2. Parámetros de la Galaxia
const parameters = {
    count: 70000,           
    size: 0.01,             
    radius: 5,              
    branches: 3,            
    spin: 1,                
    randomness: 0.5,        
    randomnessPower: 4,     
    insideColor: '#ff6030', 
    outsideColor: '#1b3984' 
};

// 3. Generador de Geometría de Partículas
const geometry = new THREE.BufferGeometry();
const positions = new Float32Array(parameters.count * 3);
const colors = new Float32Array(parameters.count * 3);

const colorInside = new THREE.Color(parameters.insideColor);
const colorOutside = new THREE.Color(parameters.outsideColor);

for (let i = 0; i < parameters.count; i++) {
    const i3 = i * 3;

    const radius = Math.random() * parameters.radius;
    const spinAngle = radius * parameters.spin;
    const branchAngle = ((i % parameters.branches) / parameters.branches) * Math.PI * 2;

    // Dispersión matemática de las estrellas
    const randomX = Math.pow(Math.random(), parameters.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * parameters.randomness * radius;
    const randomY = Math.pow(Math.random(), parameters.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * parameters.randomness * radius;
    const randomZ = Math.pow(Math.random(), parameters.randomnessPower) * (Math.random() < 0.5 ? 1 : -1) * parameters.randomness * radius;

    positions[i3    ] = Math.cos(branchAngle + spinAngle) * radius + randomX;
    positions[i3 + 1] = randomY;
    positions[i3 + 2] = Math.sin(branchAngle + spinAngle) * radius + randomZ;

    // Mezcla de colores (Degradado centro-afuera)
    const mixedColor = colorInside.clone();
    mixedColor.lerp(colorOutside, radius / parameters.radius);

    colors[i3    ] = mixedColor.r;
    colors[i3 + 1] = mixedColor.g;
    colors[i3 + 2] = mixedColor.b;
}

geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

// 4. Material de los puntos
const material = new THREE.PointsMaterial({
    size: parameters.size,
    sizeAttenuation: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexColors: true
});

const galaxy = new THREE.Points(geometry, material);
scene.add(galaxy);

// 5. Cámara y Renderizador
const sizes = { width: window.innerWidth, height: window.innerHeight };
const camera = new THREE.PerspectiveCamera(75, sizes.width / sizes.height, 0.1, 100);
camera.position.set(0, 5, 8);
scene.add(camera);

const renderer = new THREE.WebGLRenderer({ canvas: canvas });
renderer.setSize(sizes.width, sizes.height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

// 6. Controles de Órbita (Moverse con el ratón usando la librería global de cdnjs)
const controls = new THREE.OrbitControls(camera, canvas);
controls.enableDamping = true;

// 7. Bucle de Animación
const clock = new THREE.Clock();

const tick = () => {
    const elapsedTime = clock.getElapsedTime();
    
    // Rotación automática lenta
    galaxy.rotation.y = elapsedTime * 0.05; 

    // Actualiza los movimientos de arrastre del ratón
    controls.update();

    renderer.render(scene, camera);
    window.requestAnimationFrame(tick);
};

tick();

// Ajuste automático si se cambia el tamaño de la pantalla
window.addEventListener('resize', () => {
    sizes.width = window.innerWidth;
    sizes.height = window.innerHeight;
    camera.aspect = sizes.width / sizes.height;
    camera.updateProjectionMatrix();
    renderer.setSize(sizes.width, sizes.height);
});
