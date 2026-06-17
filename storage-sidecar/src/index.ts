import "dotenv/config";
import express, { NextFunction, Request, Response } from "express";
import { storageRouter } from "./routes/storage.js";

const app = express();
app.use(express.json({ limit: "1mb" }));

const AUTH_TOKEN = process.env.SIDECAR_AUTH_TOKEN ?? "";

// Health check is unauthenticated; everything else requires the shared secret.
app.get("/health", (_req, res) => res.json({ ok: true, service: "ola-storage-sidecar" }));

app.use((req: Request, res: Response, next: NextFunction) => {
  if (!AUTH_TOKEN) {
    console.error("SIDECAR_AUTH_TOKEN is not set — refusing requests.");
    return res.status(503).json({ error: "sidecar not configured" });
  }
  if (req.header("x-sidecar-token") !== AUTH_TOKEN) {
    return res.status(401).json({ error: "unauthorized" });
  }
  next();
});

app.use("/", storageRouter);

const PORT = Number(process.env.SIDECAR_PORT ?? 3001);
app.listen(PORT, () => {
  console.log(`Ola storage sidecar listening on :${PORT}`);
});
