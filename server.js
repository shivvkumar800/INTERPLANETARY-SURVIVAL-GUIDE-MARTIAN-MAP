const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8080;
const PUBLIC_DIR = __dirname;

const MIME_TYPES = {
  '.html': 'text/html; charset=UTF-8',
  '.js': 'application/javascript; charset=UTF-8',
  '.css': 'text/css; charset=UTF-8',
  '.json': 'application/json; charset=UTF-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
  // CORS Headers for API requests
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  let reqPath = decodeURIComponent(req.url.split('?')[0]);

  // REST API: Multi-Site Trajectories
  if (reqPath === '/api/trajectories') {
    const trajFile = path.join(PUBLIC_DIR, 'public', 'data', 'all_trajectories.json');
    if (fs.existsSync(trajFile)) {
      res.writeHead(200, {
        'Content-Type': 'application/json; charset=UTF-8',
        'Cache-Control': 'no-cache'
      });
      fs.createReadStream(trajFile).pipe(res);
      return;
    }
  }

  // REST API: Specific Site Trajectory e.g. /api/trajectory/gale-crater
  if (reqPath.startsWith('/api/trajectory/')) {
    const siteId = reqPath.replace('/api/trajectory/', '').trim();
    const trajFile = path.join(PUBLIC_DIR, 'public', 'data', 'all_trajectories.json');
    if (fs.existsSync(trajFile)) {
      try {
        const all = JSON.parse(fs.readFileSync(trajFile, 'utf8'));
        if (all[siteId]) {
          res.writeHead(200, {
            'Content-Type': 'application/json; charset=UTF-8',
            'Cache-Control': 'no-cache'
          });
          res.end(JSON.stringify(all[siteId], null, 2));
          return;
        }
      } catch (e) {}
    }
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: `Trajectory not found for site: ${siteId}` }));
    return;
  }

  // REST API: Default Route Analysis (Jezero Crater)
  if (reqPath === '/api/route-analysis' || reqPath === '/api/route') {
    const routeFile = path.join(PUBLIC_DIR, 'route_analysis.json');
    if (fs.existsSync(routeFile)) {
      res.writeHead(200, {
        'Content-Type': 'application/json; charset=UTF-8',
        'Cache-Control': 'no-cache'
      });
      fs.createReadStream(routeFile).pipe(res);
      return;
    }
  }

  // REST API: Planetary Data
  if (reqPath === '/api/mars-data' || reqPath === '/api/data') {
    const dataFile = path.join(PUBLIC_DIR, 'public', 'data', 'mars_data.json');
    if (fs.existsSync(dataFile)) {
      res.writeHead(200, {
        'Content-Type': 'application/json; charset=UTF-8',
        'Cache-Control': 'no-cache'
      });
      fs.createReadStream(dataFile).pipe(res);
      return;
    }
  }

  if (reqPath === '/favicon.ico') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (reqPath === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'active', mission: 'SPACEWEB-ARES-2026', timestamp: new Date().toISOString() }));
    return;
  }

  // Root or Default Page
  if (reqPath === '/' || reqPath === '/index.html' || reqPath === '/Mars Survival guide.html') {
    reqPath = '/index.html';
  }

  const filePath = path.join(PUBLIC_DIR, reqPath);

  // Security check: ensure path is within PUBLIC_DIR
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('403 Forbidden');
    return;
  }

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found: ' + reqPath);
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': contentType,
      'Content-Length': stats.size,
      'Cache-Control': 'no-cache'
    });

    const stream = fs.createReadStream(filePath);
    stream.pipe(res);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`\n======================================================`);
  console.log(`  SPACEWEB // MARS MISSION CONTROL SERVER ACTIVE`);
  console.log(`  Local URL:        http://localhost:${PORT}`);
  console.log(`  All Trajectories: http://localhost:${PORT}/api/trajectories`);
  console.log(`  Site Trajectory:  http://localhost:${PORT}/api/trajectory/:siteId`);
  console.log(`  Mars Data API:    http://localhost:${PORT}/api/mars-data`);
  console.log(`  Serving:          index.html`);
  console.log(`======================================================\n`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    const nextPort = Number(PORT) + 1;
    console.log(`Port ${PORT} is in use, trying port ${nextPort}...`);
    server.listen(nextPort, '0.0.0.0');
  } else {
    console.error('Server error:', err);
  }
});
