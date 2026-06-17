import { ZgFile, Indexer } from "@0glabs/0g-ts-sdk";
import { ethers } from "ethers";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

// ─── 0G clients (private key ALWAYS from env, never hardcoded) ───────────────
const RPC_URL = process.env.OG_STORAGE_RPC!;
const INDEXER_URL = process.env.OG_STORAGE_INDEXER!;
const PRIVATE_KEY = process.env.OG_STORAGE_PRIVATE_KEY!;

if (!RPC_URL || !INDEXER_URL || !PRIVATE_KEY) {
  throw new Error(
    "Missing 0G storage env: OG_STORAGE_RPC, OG_STORAGE_INDEXER, OG_STORAGE_PRIVATE_KEY"
  );
}

const provider = new ethers.JsonRpcProvider(RPC_URL);
const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
const indexer = new Indexer(INDEXER_URL);

/**
 * Store a JSON record on 0G Storage. Returns the Merkle root hash.
 * SDK requires a file path, so we write the JSON to a temp file first.
 * Always closes the file handle and removes the temp file in `finally`.
 */
export async function storeRecord(record: unknown): Promise<string> {
  const tempPath = path.join(os.tmpdir(), `ola-record-${Date.now()}-${Math.random().toString(36).slice(2)}.json`);
  fs.writeFileSync(tempPath, JSON.stringify(record));

  const file = await ZgFile.fromFilePath(tempPath);
  try {
    const [tree, treeErr] = await file.merkleTree();
    if (treeErr) throw treeErr;

    const rootHash = tree!.rootHash();

    // upload() returns a [tx, err] tuple — it does NOT throw on logical errors.
    // `wallet as any`: SDK .d.ts references ethers' CJS Signer type while we import
    // the ESM build — a type-only dual-package clash, runtime is identical.
    const [, uploadErr] = await indexer.upload(file, RPC_URL, wallet as any);
    if (uploadErr) throw new Error(`0G upload failed: ${uploadErr.message ?? uploadErr}`);

    return rootHash!;
  } finally {
    await file.close();
    fs.unlinkSync(tempPath);
  }
}

/**
 * Retrieve a JSON record by root hash. Verified download (3rd param = true).
 * download() can THROW or return an error — always wrap in try/catch.
 */
export async function fetchRecord(rootHash: string): Promise<unknown> {
  const outPath = path.join(os.tmpdir(), `ola-fetch-${Date.now()}.json`);
  try {
    const err = await indexer.download(rootHash, outPath, true);
    if (err) throw err;
    const data = fs.readFileSync(outPath, "utf-8");
    return JSON.parse(data);
  } catch (error: any) {
    throw new Error(`0G download failed: ${error.message ?? error}`);
  } finally {
    if (fs.existsSync(outPath)) fs.unlinkSync(outPath);
  }
}
