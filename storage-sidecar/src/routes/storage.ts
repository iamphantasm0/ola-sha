import { Router } from "express";
import { storeRecord, fetchRecord } from "../lib/zg.js";

export const storageRouter = Router();

/** POST /store  { record: object }  ->  { rootHash: string } */
storageRouter.post("/store", async (req, res) => {
  try {
    const record = req.body?.record;
    if (!record) {
      return res.status(400).json({ error: "missing 'record' in body" });
    }
    const rootHash = await storeRecord(record);
    return res.json({ rootHash });
  } catch (e: any) {
    console.error("[/store] error:", e);
    return res.status(500).json({ error: e?.message ?? "store failed" });
  }
});

/** GET /record/:rootHash  ->  { data: object } */
storageRouter.get("/record/:rootHash", async (req, res) => {
  try {
    const data = await fetchRecord(req.params.rootHash);
    return res.json({ data });
  } catch (e: any) {
    console.error("[/record] error:", e);
    return res.status(500).json({ error: e?.message ?? "fetch failed" });
  }
});
