"""Step 7. Memory sizing helper (formulas from https://qdrant.tech/documentation/capacity-planning/).

dense originals  = points * replication_factor * dims * bytes_per_dim
HNSW graph       = points * replication_factor * m * 2 * 4 bytes * 1.2   (1.2: lower layers, bookkeeping)
quantized copy   = int8: dims bytes, binary: dims / 8 bytes per vector
+ ~20% headroom on the totals (page cache, runtime, optimizations). Payload and ID tracker not included.
"""

import os

from common import console, new_table, note

RF = int(os.environ.get("REPLICATION_FACTOR", "2"))
M = int(os.environ.get("HNSW_M", "16"))
HEADROOM = 1.2


def gb(b: float) -> str:
    return f"{b / 1024 ** 3:,.1f}"


def main() -> None:
    console.rule(f"Step 7 · How much memory is needed: replication_factor={RF}, m={M}, headroom +{HEADROOM - 1:.0%}")
    t = new_table(f"GiB for the whole cluster (x{RF} replicas), without payload", "points", "dims", "float32", "int8",
                  "binary", "HNSW", "RAM: all float32", "RAM: int8 + HNSW", "RAM: binary + HNSW",
                  "disk: originals")
    for n in (1_000_000, 10_000_000):
        for d in (1024, 1536):
            base = n * RF
            f32, i8, b1 = base * d * 4, base * d, base * d / 8
            graph = base * M * 2 * 4 * 1.2
            t.add_row(f"{n / 1e6:.0f}M", str(d), gb(f32), gb(i8), gb(b1), gb(graph),
                      gb((f32 + graph) * HEADROOM), gb((i8 + graph) * HEADROOM), gb((b1 + graph) * HEADROOM),
                      gb(f32))
        t.add_section()
    console.print(t)
    note("RAM columns = (vectors in RAM + HNSW graph) x 1.2. The int8 and binary variants keep only the compressed copy in RAM, "
         "the float32 originals live on disk for rescoring - they are in the \"disk\" column.")
    note("Source of the formulas: https://qdrant.tech/documentation/capacity-planning/ "
         "(dense_size, hnsw_size = base * m * 2 * 4 * 1.2, +20% headroom).")


if __name__ == "__main__":
    main()
