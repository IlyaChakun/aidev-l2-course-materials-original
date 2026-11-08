// Builds the Inspector catalog from catalog.template.json on every container start.
//
//   node render-catalog.mjs <template> <output>
//
// Inspector does not substitute environment variables into the catalog, and a stdio server does not get the
// container environment. So ${VAR} is substituted here. Service fields of the template:
//   "x-requires-env":  ["VAR"]  — the server enters the catalog only if VAR is set in .env;
//   "x-requires-path": "/path"  — the server enters the catalog only if the path exists in the container;
//   "x-note":          "..."    — a note for humans, it does not enter the catalog.
import { existsSync, readFileSync, writeFileSync } from "node:fs";

const [templatePath, outputPath] = process.argv.slice(2);
const template = JSON.parse(readFileSync(templatePath, "utf8"));

const substitute = (value) => {
  if (typeof value === "string") return value.replace(/\$\{(\w+)\}/g, (_, name) => process.env[name] ?? "");
  if (Array.isArray(value)) return value.map(substitute);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, substitute(v)]));
  }
  return value;
};

const servers = {};
for (const [name, entry] of Object.entries(template.mcpServers)) {
  const missingEnv = (entry["x-requires-env"] ?? []).filter((v) => !process.env[v]);
  const missingPath = entry["x-requires-path"] && !existsSync(entry["x-requires-path"]);
  if (missingEnv.length || missingPath) {
    const why = missingEnv.length ? `no ${missingEnv.join(", ")} in .env` : `no ${entry["x-requires-path"]}`;
    console.log(`  - ${name}: skipped (${why})`);
    continue;
  }
  const clean = Object.fromEntries(Object.entries(entry).filter(([k]) => !k.startsWith("x-")));
  servers[name] = substitute(clean);
  console.log(`  + ${name}`);
}

writeFileSync(outputPath, JSON.stringify({ mcpServers: servers }, null, 2) + "\n");
console.log(`Catalog: ${Object.keys(servers).length} servers → ${outputPath}`);
