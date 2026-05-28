const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const compression = require('compression');
const pino = require('pino')({ level: process.env.LOG_LEVEL || 'info' });
const ffmpeg = require('fluent-ffmpeg');
const path = require('path');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const mkdirp = require('mkdirp');

const app = express();

// ── Middleware (from nodejs-backend-patterns skill) ──

// Structured logging
app.use((req, res, next) => {
  req.log = pino.child({ reqId: uuidv4().slice(0, 8) });
  req.log.info({ method: req.method, path: req.path }, 'request start');
  const start = Date.now();
  res.on('finish', () => {
    req.log.info({ status: res.statusCode, duration: Date.now() - start }, 'request end');
  });
  next();
});

// Compression
app.use(compression());

// CORS — restrictive, not wildcard (security skill)
const allowedOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',')
  : ['http://localhost:3000', 'http://localhost:5173'];
app.use(cors({
  origin: (origin, cb) => {
    if (!origin || allowedOrigins.includes(origin)) return cb(null, true);
    cb(new Error('CORS blocked'));
  },
  credentials: true,
}));

// Rate limiting (prevent abuse)
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    req.log.warn('rate limit exceeded');
    res.status(429).json({ error: 'Too many requests, slow down' });
  },
});
app.use('/api/', limiter);

app.use(express.json({ limit: '10kb' }));

const PORT = process.env.PORT || 3000;
const DOWNLOADS_DIR = path.join(__dirname, '..', 'downloads');
mkdirp.sync(DOWNLOADS_DIR);

let client;
const activeTorrents = new Map();

// ── Validation (from nodejs-backend-patterns skill) ──

function isValidMagnet(uri) {
  if (typeof uri !== 'string') return false;
  return uri.startsWith('magnet:?');
}

function sanitizeFilename(name) {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_');
}

// ── Init WebTorrent (ESM dynamic import) ──

async function initWebTorrent() {
  const wt = await import('webtorrent');
  const WebTorrent = wt.default || wt;
  client = new WebTorrent();
  pino.info('WebTorrent initialized');
}

const videoExts = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v'];
const subExts = ['.srt', '.ass', '.ssa', '.vtt', '.sub'];

function findVideoFile(torrent) {
  return torrent.files.find(f => videoExts.some(ext => f.name.toLowerCase().endsWith(ext)));
}

function findSubtitleFiles(torrent) {
  return torrent.files.filter(f => subExts.some(ext => f.name.toLowerCase().endsWith(ext)));
}

function probeAudioTracks(videoPath) {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(videoPath, (err, metadata) => {
      if (err) return reject(err);
      const audioTracks = metadata.streams
        .filter(s => s.codec_type === 'audio')
        .map((s, idx) => ({
          index: idx,
          streamIndex: s.index,
          codec: s.codec_name,
          language: s.tags?.language || `Audio ${idx + 1}`,
          title: s.tags?.title || s.tags?.language || `Track ${idx + 1}`,
          channels: s.channels,
        }));
      const subtitleStreams = metadata.streams
        .filter(s => s.codec_type === 'subtitle')
        .map((s, idx) => ({
          index: idx,
          streamIndex: s.index,
          codec: s.codec_name,
          language: s.tags?.language || `Sub ${idx + 1}`,
          title: s.tags?.title || s.tags?.language || `Subtitle ${idx + 1}`,
        }));
      resolve({ audioTracks, subtitleStreams, duration: metadata.format.duration });
    });
  });
}

async function startTranscoding(torrentId, videoPath, outputDir, audioTracks, subtitleStreams) {
  const torrentData = activeTorrents.get(torrentId);
  if (!torrentData) return;
  torrentData.status = 'transcoding';
  mkdirp.sync(outputDir);

  const cmd = ffmpeg(videoPath);

  // Video: H.264 baseline for max compatibility (mobile + laptop)
  cmd.outputOptions([
    '-map 0:v:0',
    '-c:v libx264',
    '-profile:v baseline',
    '-level 3.0',
    '-preset veryfast',
    '-crf 23',
    '-g 48',
    '-keyint_min 48',
    '-sc_threshold 0',
    '-hls_time 4',
    '-hls_playlist_type vod',
    '-hls_segment_filename', path.join(outputDir, 'segment_%03d.ts'),
    '-f hls',
  ]);

  // Audio: AAC with language metadata
  audioTracks.forEach((track, i) => {
    cmd.outputOptions([
      `-map 0:a:${i}`,
      `-c:a:${i} aac`,
      `-b:a:${i} 128k`,
      `-metadata:s:a:${i} language=${track.language}`,
    ]);
  });

  // Subtitles: WebVTT for browser compatibility
  subtitleStreams.forEach((sub, i) => {
    cmd.outputOptions([
      `-map 0:s:${i}`,
      `-c:s:${i} webvtt`,
    ]);
  });

  if (audioTracks.length === 0) cmd.outputOptions(['-an']);

  const playlistPath = path.join(outputDir, 'playlist.m3u8');
  cmd.save(playlistPath);

  cmd.on('start', () => pino.info(`[${torrentId}] ffmpeg transcoding started`));
  cmd.on('progress', (progress) => {
    torrentData.transcodeProgress = progress.percent || 0;
  });
  cmd.on('end', () => {
    torrentData.status = 'ready';
    torrentData.transcodeProgress = 100;
    pino.info(`[${torrentId}] transcoding complete`);
  });
  cmd.on('error', (err) => {
    pino.error(`[${torrentId}] ffmpeg error: ${err.message}`);
    torrentData.status = 'error';
    torrentData.error = err.message;
  });

  torrentData.ffmpegCommand = cmd;
}

async function extractSubtitles(torrent, outputDir) {
  const subs = findSubtitleFiles(torrent);
  const extracted = [];
  for (const file of subs) {
    const safeName = sanitizeFilename(file.name);
    const outPath = path.join(outputDir, `sub_${extracted.length}_${safeName}`);
    await new Promise((resolve, reject) => {
      const stream = file.createReadStream();
      const writeStream = fs.createWriteStream(outPath);
      stream.pipe(writeStream);
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
    extracted.push({ path: outPath, name: safeName, language: path.basename(safeName, path.extname(safeName)) });
  }
  return extracted;
}

// ── API Routes ──

// Health check (from nodejs-backend-patterns skill)
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    torrents: activeTorrents.size,
    memory: process.memoryUsage(),
    timestamp: new Date().toISOString(),
  });
});

// Add torrent
app.post('/api/torrents', async (req, res) => {
  const { magnetUri } = req.body;

  // Input validation (from nodejs-backend-patterns skill)
  if (!magnetUri || !isValidMagnet(magnetUri)) {
    req.log.warn({ body: req.body }, 'invalid magnet link');
    return res.status(400).json({ error: 'Valid magnetUri required (must start with magnet:?)' });
  }

  const id = uuidv4();
  const outputDir = path.join(DOWNLOADS_DIR, id);
  mkdirp.sync(outputDir);

  req.log.info(`[${id}] Adding torrent`);

  try {
    const torrent = client.add(magnetUri, { path: outputDir });

    activeTorrents.set(id, {
      id, torrent, magnetUri,
      status: 'metadata',
      progress: 0,
      transcodeProgress: 0,
      outputDir,
      createdAt: new Date().toISOString(),
    });

    torrent.on('metadata', async () => {
      req.log.info(`[${id}] metadata received: ${torrent.name}`);
      const videoFile = findVideoFile(torrent);
      const subFiles = findSubtitleFiles(torrent);

      const info = {
        name: torrent.name,
        length: torrent.length,
        files: torrent.files.map(f => ({ name: f.name, length: f.length })),
        videoFile: videoFile ? { name: videoFile.name, length: videoFile.length } : null,
        subtitleFiles: subFiles.map(f => ({ name: f.name, length: f.length })),
      };

      const data = activeTorrents.get(id);
      data.info = info;
      data.status = 'downloading';

      if (!videoFile) {
        data.status = 'error';
        data.error = 'No video file found in torrent';
        req.log.error(`[${id}] no video file`);
        return;
      }

      const videoTempPath = path.join(outputDir, 'video_temp' + path.extname(videoFile.name));
      const writeStream = fs.createWriteStream(videoTempPath);
      const readStream = videoFile.createReadStream();
      readStream.pipe(writeStream);

      writeStream.on('finish', async () => {
        req.log.info(`[${id}] video buffered, probing...`);
        try {
          const probe = await probeAudioTracks(videoTempPath);
          data.probe = probe;
          const extractedSubs = await extractSubtitles(torrent, outputDir);
          data.extractedSubtitles = extractedSubs;
          await startTranscoding(id, videoTempPath, path.join(outputDir, 'hls'), probe.audioTracks, probe.subtitleStreams);
        } catch (err) {
          req.log.error(`[${id}] probe/transcode error: ${err.message}`);
          data.status = 'error';
          data.error = err.message;
        }
      });
    });

    torrent.on('download', () => {
      const data = activeTorrents.get(id);
      if (data) {
        data.progress = Math.round(torrent.progress * 100);
        data.downloadSpeed = torrent.downloadSpeed;
      }
    });

    torrent.on('done', () => {
      req.log.info(`[${id}] download complete`);
      const data = activeTorrents.get(id);
      if (data) data.progress = 100;
    });

    torrent.on('error', (err) => {
      req.log.error(`[${id}] torrent error: ${err.message}`);
      const data = activeTorrents.get(id);
      if (data) { data.status = 'error'; data.error = err.message; }
    });

    res.status(201).json({ id, status: 'metadata', message: 'Torrent added' });
  } catch (err) {
    req.log.error({ err }, 'Failed to add torrent');
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/torrents/:id', (req, res) => {
  const data = activeTorrents.get(req.params.id);
  if (!data) return res.status(404).json({ error: 'Torrent not found' });
  res.json({
    id: data.id,
    status: data.status,
    progress: data.progress,
    transcodeProgress: data.transcodeProgress,
    downloadSpeed: data.downloadSpeed,
    info: data.info,
    probe: data.probe,
    extractedSubtitles: data.extractedSubtitles?.map(s => ({ name: s.name, language: s.language })) || [],
    createdAt: data.createdAt,
    error: data.error,
  });
});

app.get('/api/torrents', (req, res) => {
  const list = Array.from(activeTorrents.values()).map(d => ({
    id: d.id,
    status: d.status,
    progress: d.progress,
    transcodeProgress: d.transcodeProgress,
    name: d.info?.name || 'Loading...',
    createdAt: d.createdAt,
  }));
  res.json(list);
});

app.delete('/api/torrents/:id', (req, res) => {
  const data = activeTorrents.get(req.params.id);
  if (!data) return res.status(404).json({ error: 'Not found' });
  if (data.ffmpegCommand) data.ffmpegCommand.kill('SIGKILL');
  if (data.torrent) client.remove(data.torrent);
  try { fs.rmSync(data.outputDir, { recursive: true, force: true }); } catch (e) {}
  activeTorrents.delete(req.params.id);
  pino.info(`[${req.params.id}] removed`);
  res.json({ message: 'Torrent removed' });
});

// Serve HLS
app.get('/api/stream/:id/:file', (req, res) => {
  const data = activeTorrents.get(req.params.id);
  if (!data) return res.status(404).json({ error: 'Not found' });
  const filePath = path.join(data.outputDir, 'hls', req.params.file);
  if (!filePath.startsWith(path.join(data.outputDir, 'hls'))) return res.status(403).json({ error: 'Invalid path' });
  if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'File not ready' });

  const ext = path.extname(filePath);
  if (ext === '.m3u8') res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
  else if (ext === '.ts') res.setHeader('Content-Type', 'video/mp2t');
  else if (ext === '.vtt') res.setHeader('Content-Type', 'text/vtt');

  res.sendFile(filePath);
});

// Serve subtitles
app.get('/api/subs/:id/:file', (req, res) => {
  const data = activeTorrents.get(req.params.id);
  if (!data) return res.status(404).json({ error: 'Not found' });
  const sub = data.extractedSubtitles?.find(s => s.name === req.params.file);
  if (!sub) return res.status(404).json({ error: 'Subtitle not found' });
  res.setHeader('Content-Type', 'text/vtt');
  res.sendFile(sub.path);
});

// Static frontend
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Global error handler (from nodejs-backend-patterns skill)
app.use((err, req, res, next) => {
  req.log.error({ err }, 'unhandled error');
  res.status(err.status || 500).json({
    error: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message,
    code: err.code,
  });
});

// Graceful shutdown (from nodejs-backend-patterns skill)
async function shutdown(signal) {
  pino.info(`Received ${signal}, shutting down gracefully...`);
  for (const [id, data] of activeTorrents) {
    if (data.ffmpegCommand) data.ffmpegCommand.kill('SIGKILL');
    if (data.torrent) client.remove(data.torrent);
  }
  if (client) client.destroy();
  process.exit(0);
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));

// Start
initWebTorrent().then(() => {
  app.listen(PORT, () => {
    pino.info(`Torrent Stream Player server running on port ${PORT}`);
  });
}).catch(err => {
  pino.fatal({ err }, 'Failed to init WebTorrent');
  process.exit(1);
});
