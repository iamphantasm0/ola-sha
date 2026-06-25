import { ethers } from "ethers";
import { Indexer, ZgFile } from "@0gfoundation/0g-ts-sdk";
import { writeFile, readFile, unlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

/**
 * 0G Storage helpers.
 *
 * Follows the upload/download pattern from the official starter kit:
 *   https://github.com/0gfoundation/0g-storage-ts-starter-kit
 *
 * The SDK returns Go-style [value, error] tuples. ethers v6 is required
 * (never v5). If your installed SDK version exposes slightly different
 * symbols (e.g. `Blob` instead of `ZgFile`), adjust the imports here — the
 * package name (@0gfoundation/0g-ts-sdk) is the confirmed one.
 */

const RPC = process.env.OG_STORAGE_RPC || "https://evmrpc-testnet.0g.ai";
const INDEXER_RPC =
  process.env.OG_STORAGE_INDEXER ||
  "https://indexer-storage-testnet-turbo.0g.ai";
const PRIVATE_KEY = process.env.OG_STORAGE_PRIVATE_KEY || "";

if (!PRIVATE_KEY) {
  console.warn(
    "[zg] OG_STORAGE_PRIVATE_KEY is empty — uploads will fail until it is set."
  );
}

const provider = new ethers.JsonRpcProvider(RPC);
const signer = new ethers.Wallet(PRIVATE_KEY, provider);
const indexer = new Indexer(INDEXER_RPC);

/** Write a JSON record to 0G Storage. Returns the Merkle root hash. */
export async function storeRecord(record: unknown): Promise<string> {
  const path = join(tmpdir(), `ola-${randomUUID()}.json`);
  await writeFile(path, JSON.stringify(record, null, 2), "utf-8");

  let file: ZgFile | undefined;
  try {
    file = await ZgFile.fromFilePath(path);

    const [tree, treeErr] = await file.merkleTree();
    if (treeErr !== null) throw new Error(`merkleTree failed: ${treeErr}`);
    const rootHash = tree?.rootHash();
    if (!rootHash) throw new Error("merkleTree produced no root hash");

    const [tx, uploadErr] = await indexer.upload(file, RPC, signer);
    if (uploadErr !== null) throw new Error(`upload failed: ${uploadErr}`);

    console.log(`[zg] stored ${rootHash} (tx ${tx})`);
    return rootHash;
  } finally {
    if (file) await file.close();
    await unlink(path).catch(() => {});
  }
}

/** Read a JSON record back from 0G Storage by root hash. */
export async function fetchRecord(rootHash: string): Promise<unknown> {
  const path = join(tmpdir(), `ola-dl-${randomUUID()}.json`);
  try {
    // (rootHash, outputPath, withProof)
    const err = await indexer.download(rootHash, path, true);
    if (err !== null) throw new Error(`download failed: ${err}`);
    const data = await readFile(path, "utf-8");
    return JSON.parse(data);
  } finally {
    await unlink(path).catch(() => {});
  }
}
