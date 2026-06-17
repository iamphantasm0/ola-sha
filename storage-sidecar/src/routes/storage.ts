import { Router, Request, Response } from "express";
import { storeRecord, fetchRecord } from "../lib/zg.js";

export const storageRouter = Router();

// POST /store  { record: object }  → { rootHash: string }
storageRouter.post("/store", async (req: Request, res: Response) => {
  const { record } = req.body ?? {};
  if (!record || typeof record !== "object") {
    return res.status(400).json({ error: "Body must be { record: object }" });
  }
  try {
    const rootHash = await storeRecord(record);
    return res.json({ rootHash });
  } catch (error: any) {
    console.error("[/store] error:", error?.message ?? error);
    return res.status(502).json({ error: error?.message ?? "store failed" });
  }
});

// GET /record/:rootHash → { data: object }
storageRouter.get("/record/:rootHash", async (req: Request, res: Response) => {
  try {
    const data = await fetchRecord(req.params.rootHash);
    return res.json({ data });
  } catch (error: any) {
    console.error("[/record] error:", error?.message ?? error);
    return res.status(502).json({ error: error?.message ?? "fetch failed" });
  }
});
