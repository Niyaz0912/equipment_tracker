// static/js/network_topology.js
class NetworkTopology {
    constructor(containerId, nodesData, edgesData = []) {
        this.containerId = containerId;
        this.nodesData = nodesData;
        this.edgesData = edgesData;
        this.network = null;
        this.nodes = null;
        this.edges = null;
        
        this.init();
    }
    
    init() {
        this.loadVisJS().then(() => {
            this.createNetwork();
            this.setupEventListeners();
            this.updateStatistics();
        });
    }
    
    loadVisJS() {
        return new Promise((resolve) => {
            if (typeof vis !== 'undefined') {
                resolve();
                return;
            }
            
            // Загружаем стили
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/vis-network/styles/vis-network.min.css';
            document.head.appendChild(link);
            
            // Загружаем скрипт
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
            script.onload = resolve;
            document.head.appendChild(script);
        });
    }
    
    createNetwork() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Контейнер ${this.containerId} не найден`);
            return;
        }
        
        // Создаем DataSet
        this.nodes = new vis.DataSet(this.nodesData.map(node => ({
            ...node,
            shape: this.getShapeForType(node.group),
            color: this.getColorForType(node.group),
            font: { 
                size: 14, 
                multi: true,
                face: 'Arial'
            },
            margin: 10,
            widthConstraint: { maximum: 160 },
            heightConstraint: { minimum: 70 },
            borderWidth: 2,
            shadow: true
        })));
        
        this.edges = new vis.DataSet(this.edgesData);
        
        // Данные для сети
        const data = { nodes: this.nodes, edges: this.edges };
        
        // Настройки
        const options = {
            nodes: {
                borderWidthSelected: 4,
                scaling: {
                    min: 10,
                    max: 30,
                    label: {
                        enabled: true,
                        min: 14,
                        max: 30
                    }
                }
            },
            edges: {
                arrows: 'to',
                smooth: {
                    type: 'continuous',
                    roundness: 0.5
                },
                color: {
                    color: '#7F8C8D',
                    highlight: '#3498DB',
                    hover: '#2ECC71'
                },
                width: 2,
                hoverWidth: 3,
                selectionWidth: 4
            },
            physics: {
                enabled: true,
                stabilization: {
                    iterations: 100,
                    updateInterval: 25,
                    fit: true
                },
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 200,
                    springConstant: 0.08,
                    damping: 0.4,
                    avoidOverlap: 1
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true,
                hoverConnectedEdges: true
            },
            layout: {
                improvedLayout: true
            }
        };
        
        // Создаем сеть
        this.network = new vis.Network(container, data, options);
        
        // Обработка клика по узлу
        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = this.nodes.get(nodeId);
                if (node && node.url) {
                    window.location.href = node.url;
                }
            }
        });
        
        // Двойной клик для увеличения
        this.network.on('doubleClick', () => {
            this.network.fit();
        });
        
        // После стабилизации
        this.network.on('stabilizationIterationsDone', () => {
            this.network.fit();
        });
        
        // При наведении
        this.network.on('hoverNode', (params) => {
            const node = this.nodes.get(params.node);
            if (node) {
                // Можно добавить эффект при наведении
            }
        });
    }
    
    getShapeForType(type) {
        const shapes = {
            'router': 'diamond',
            'switch': 'box',
            'server': 'ellipse',
            'firewall': 'triangle',
            'access_point': 'dot',
            'default': 'box'
        };
        return shapes[type] || shapes.default;
    }
    
    getColorForType(type) {
        const colors = {
            'router': { 
                background: '#4A90E2', 
                border: '#2C3E50', 
                highlight: { background: '#5D9CEC', border: '#3498DB' } 
            },
            'switch': { 
                background: '#50E3C2', 
                border: '#27AE60', 
                highlight: { background: '#58EBC9', border: '#2ECC71' } 
            },
            'server': { 
                background: '#7ED321', 
                border: '#2ECC71', 
                highlight: { background: '#87DC2A', border: '#58D68D' } 
            },
            'firewall': { 
                background: '#D0021B', 
                border: '#C0392B', 
                highlight: { background: '#E74C3C', border: '#D98880' } 
            },
            'access_point': { 
                background: '#F5A623', 
                border: '#E67E22', 
                highlight: { background: '#F7B84B', border: '#F39C12' } 
            },
            'default': { 
                background: '#BDC3C7', 
                border: '#95A5A6', 
                highlight: { background: '#D5DBDB', border: '#BFC9CA' } 
            }
        };
        return colors[type] || colors.default;
    }
    
    setupEventListeners() {
        // Кнопка увеличения
        document.getElementById('btn-zoom-in')?.addEventListener('click', () => {
            if (this.network) {
                this.network.moveTo({ scale: this.network.getScale() * 1.2 });
            }
        });
        
        // Кнопка уменьшения
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => {
            if (this.network) {
                this.network.moveTo({ scale: this.network.getScale() * 0.8 });
            }
        });
        
        // Кнопка сброса
        document.getElementById('btn-reset')?.addEventListener('click', () => {
            if (this.network) {
                this.network.fit();
                this.network.stabilize(100);
            }
        });
        
        // Кнопка экспорта
        document.getElementById('btn-export')?.addEventListener('click', () => {
            this.exportAsImage();
        });
        
        // Фильтр по типу
        document.getElementById('type-filter')?.addEventListener('change', (e) => {
            this.filterByType(e.target.value);
        });
        
        // Фильтр по локации
        document.getElementById('location-filter')?.addEventListener('change', (e) => {
            this.filterByLocation(e.target.value);
        });
        
        // Фильтр по статусу
        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.filterByStatus(e.target.value);
        });
        
        // Переключение физики
        document.getElementById('physics-toggle')?.addEventListener('change', (e) => {
            if (this.network) {
                this.network.setOptions({
                    physics: { enabled: e.target.checked }
                });
            }
        });
        
        // Полноэкранный режим
        document.getElementById('btn-fullscreen')?.addEventListener('click', () => {
            const container = document.getElementById(this.containerId);
            if (!document.fullscreenElement) {
                container.requestFullscreen().catch(err => {
                    console.log(`Ошибка полноэкранного режима: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }
    
    filterByType(type) {
        if (!this.nodes) return;
        
        this.nodes.forEach((node) => {
            const update = { 
                id: node.id, 
                hidden: type ? node.group !== type : false 
            };
            this.nodes.update(update);
        });
        
        this.updateStatistics();
    }
    
    filterByLocation(locationId) {
        if (!this.nodes) return;
        
        this.nodes.forEach((node) => {
            const update = { 
                id: node.id, 
                hidden: locationId ? node.location_id != locationId : false 
            };
            this.nodes.update(update);
        });
        
        this.updateStatistics();
    }
    
    filterByStatus(status) {
        if (!this.nodes) return;
        
        this.nodes.forEach((node) => {
            const update = { 
                id: node.id, 
                hidden: status ? node.status !== status : false 
            };
            this.nodes.update(update);
        });
        
        this.updateStatistics();
    }
    
    updateStatistics() {
        if (!this.nodes) return;
        
        const visibleNodes = this.nodes.get({ filter: node => !node.hidden });
        const stats = {
            router: 0,
            switch: 0,
            server: 0,
            firewall: 0,
            access_point: 0,
            other: 0,
            total: visibleNodes.length
        };
        
        visibleNodes.forEach(node => {
            const type = node.group || 'other';
            if (stats.hasOwnProperty(type)) {
                stats[type]++;
            } else {
                stats.other++;
            }
        });
        
        // Обновляем DOM
        document.getElementById('node-count').textContent = `${stats.total} устройств`;
        document.getElementById('stat-routers').textContent = stats.router;
        document.getElementById('stat-switches').textContent = stats.switch;
        document.getElementById('stat-servers').textContent = stats.server;
        document.getElementById('stat-firewalls').textContent = stats.firewall;
        document.getElementById('stat-access-points').textContent = stats.access_point;
        document.getElementById('stat-others').textContent = stats.other;
    }
    
    exportAsImage() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        const canvas = container.querySelector('canvas');
        if (!canvas) {
            alert('Не удалось найти canvas для экспорта');
            return;
        }
        
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().slice(0,10).replace(/-/g, '');
        link.download = `network-topology-${timestamp}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
}

// Экспорт для использования в других файлах
if (typeof window !== 'undefined') {
    window.NetworkTopology = NetworkTopology;
}