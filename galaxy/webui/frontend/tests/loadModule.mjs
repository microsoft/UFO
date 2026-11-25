import { createServer as createHttpServer } from 'node:http';
import { createServer } from 'vite';

export async function loadModule(path) {
  const server = await createServer({
    configFile: false,
    // Attach Vite's websocket handler without opening a port in each test worker.
    server: { middlewareMode: true, hmr: { server: createHttpServer() }, watch: null },
    appType: 'custom',
  });
  try {
    return await server.ssrLoadModule(path);
  } finally {
    await server.close();
  }
}
