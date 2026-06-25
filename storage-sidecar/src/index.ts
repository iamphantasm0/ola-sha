import express from "express";
import { storageRouter } from "./routes/storage.js";

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req, res) =>
  res.json({ ok: true, service: "ola-storage-sidecar" })
);

app.use("/", storageRouter);

const PORT = Number(process.env.SIDECAR_PORT || 3001);
app.listen(PORT, () => {
  console.log(`0G storage sidecar listening on :${PORT}`);
});
